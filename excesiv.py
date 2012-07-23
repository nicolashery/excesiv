import os
from time import sleep, time
from datetime import datetime
from urlparse import urlsplit, urlunsplit

from pymongo import Connection
from gridfs import GridFS, NoFile
from bson.objectid import ObjectId, InvalidId

# CONFIG
# How long to wait for task to finish (in seconds) 
TASK_TIMEOUT = 10
# How long to wait before deleting a result file (in seconds)
EXPIRE_RESULT_FILE = 5 * 60
# Capped collections settings
CAPPED_COLLECTION_SIZE = 1000000
CAPPED_COLLECTION_MAX = 3

class Excesiv:
    """Main class: connects to MongoDB, manages task queue and GridFS files"""

    def __init__(self):
        pass

    def connect_db(self, mongodb_uri):
        """Connect to MongoDB"""
        connection = Connection(mongodb_uri, tz_aware=True)
        db_name = urlsplit(mongodb_uri).path.strip('/')
        db = connection[db_name]
        # Create capped collections unless they exists already
        if 'tasks' in db.collection_names():
            tasks = db.tasks
        else:
            tasks = db.create_collection('tasks', capped=True, 
                                        autoIndexId=True,
                                        size=CAPPED_COLLECTION_SIZE, 
                                        max=CAPPED_COLLECTION_MAX)
            # Insert a dummy document just in case because some drivers 
            # have trouble with empty capped collections
            tasks.insert({'init': True})
        if 'results' in db.collection_names():
            results = db.results
        else:
            results = db.create_collection('results', capped=True, 
                                        autoIndexId=True,
                                        size=CAPPED_COLLECTION_SIZE, 
                                        max=CAPPED_COLLECTION_MAX)
            results.insert({'init': True})
        # Attach some database APIs
        self.db = db # Main database API
        self.fs = GridFS(db) # Access to the GridFS files
        self.fs_meta = db.fs.files # Access to the metadata of GridFS files
        # Attach queue collections
        self.tasks = tasks
        self.results = results
        return db

    def load_templates(self, excel_dir):
        """Load Excel templates from disk to MongoDB"""
        fs = self.fs
        fs_meta = self.fs_meta
        # Delete any result or task files still in database
        for doc in fs_meta.find({'$or': [{'label': 'result'}, \
                                        {'label': 'task'}]}):
            oid = doc['_id']
            fs.delete(ObjectId(oid))    
        # Drop all templates currently in GridFS
        for doc in fs_meta.find({'label': 'template'}):
            filename = doc['filename']
            oid = doc['_id']
            fs.delete(ObjectId(oid))
            print 'Dropped template %s' % filename
        mimetype = \
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # Load all Excel templates from provided directory
        template_list = []
        for filename in os.listdir(excel_dir):
            _, extension = os.path.splitext(filename)
            if extension == '.xlsx':
                filepath = os.path.join(excel_dir, filename)
                f = open(filepath, 'rb')
                fs.put(f, filename=filename, content_type=mimetype, 
                        label='template')
                f.close()
                template_list.append(filename)
                print 'Loaded template %s' % filename
        return template_list

    def process_task(self, task):
        """Send task object to MongoDB queue, wait and return result"""
        tasks = self.tasks
        results = self.results
        fs = self.fs
        fs_meta = self.fs_meta
        # Place cursor at the end of result set
        print 'Going to end of collection'
        cursor = results.find(tailable=True)
        while cursor.alive:
            try:
                doc = cursor.next()
            except StopIteration:
                break
        # If collection was empty, cursor is dead, so re-open it
        if not cursor.alive:
            cursor = tasks.find(tailable=True)
        # Send task
        task_id = tasks.insert(task)
        # Listen for result
        print 'Listening for new data'
        timeout_time = time() + TASK_TIMEOUT
        timeout = False
        while cursor.alive:
            # If taking too long, exit loop
            if time() > timeout_time:
                timeout = True
                break
            # Try to grab new doc from collection
            try:
                result = cursor.next()
                # Break if we have the result for this task
                if task_id == result['task_id']:
                    break
            except StopIteration:
                sleep(1)
        if timeout:
            return None
        # Clean out any result or task file past expiration date
        # Note: Ideally I would want to delete a result file after I'm done 
        # sending back to the client, but I haven't figured out how to do that
        for doc in fs_meta.find({'$or': [{'label': 'result'}, \
                                        {'label': 'task'}]}):
            age = (datetime.now(doc['uploadDate'].tzinfo) - 
                    doc['uploadDate']).total_seconds()
            if age > EXPIRE_RESULT_FILE:
                oid = doc['_id']
                fs.delete(ObjectId(oid))
        # Return result object
        return result

    def get_file(self, id):
        """Return file from id, None if no file"""
        fs = self.fs
        try:
            file_id = ObjectId(id)
        except InvalidId:
            f = None
        try:
            f = fs.get(file_id)
        except NoFile:
            f = None
        return f

    def get_file_meta(self, id):
        """Return file metadata from id, None if no file"""
        fs_meta = self.fs_meta
        try:
            file_id = ObjectId(id)
        except InvalidId:
            meta = None
        meta = fs_meta.find_one(file_id)
        return meta
