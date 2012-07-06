import os
from time import sleep, time
from urlparse import urlsplit, urlunsplit
from datetime import datetime

from flask import Flask, render_template, request, abort, jsonify
from werkzeug.wsgi import wrap_file
from werkzeug.datastructures import Headers
from pymongo import Connection
from gridfs import GridFS, NoFile
from bson.objectid import ObjectId, InvalidId

# Envrionment variables for config
# MONGOLAB_URI: Heroku, MONGODB_URL: Stackato
mongodb_uri = os.environ.get('MONGOLAB_URI', 
                os.environ.get('MONGODB_URL', 'mongodb://localhost/excesiv'))

# Other config
APP_DEBUG = True
# How long to wait for task to finish (in seconds) 
TASK_TIMEOUT = 10
# How long to wait before deleting a result file (in seconds)
EXPIRE_RESULT_FILE = 5 * 60
# Capped collections settings
CAPPED_COLLECTION_SIZE = 1000000
CAPPED_COLLECTION_MAX = 3

# Setup
app = Flask(__name__)
connection = Connection(mongodb_uri, tz_aware=True)
db_name = urlsplit(mongodb_uri).path.strip('/')
db = connection[db_name]
# Create capped collections unless they exists already
if 'tasks' in db.collection_names():
    tasks = db.tasks
else:
    tasks = db.create_collection('tasks', capped=True, autoIndexId=True,
                                size=CAPPED_COLLECTION_SIZE, 
                                max=CAPPED_COLLECTION_MAX)
    # Insert a dummy document just in case because some drivers have trouble 
    # with empty capped collections
    tasks.insert({'init': True})
if 'results' in db.collection_names():
    results = db.results
else:
    results = db.create_collection('results', capped=True, autoIndexId=True,
                                size=CAPPED_COLLECTION_SIZE, 
                                max=CAPPED_COLLECTION_MAX)
    results.insert({'init': True})
fs = GridFS(db)
fs_meta = db.fs.files
app.debug = APP_DEBUG

def load_excel_templates():
    """Load Excel templates from disk to MongoDB"""
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
    # Load all Excel templates in the 'excel' directory
    excel_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 'excel')
    mimetype = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    for filename in os.listdir(excel_dir):
        _, extension = os.path.splitext(filename)
        if extension == '.xlsx':
            filepath = os.path.join(excel_dir, filename)
            f = open(filepath, 'rb')
            fs.put(f, filename=filename, content_type=mimetype, 
                    label='template')
            f.close()
            print 'Loaded template %s' % filename


def send_mongo_file(file_id, mimetype=None, as_attachment=True,
              attachment_filename=None, cache_timeout=60 * 60 * 12):
    """
    Mongo-Flask send file helper
    Adapted from Flask-PyMongo
    http://flask-pymongo.readthedocs.org/
    """
    try:
        f = fs.get(file_id)
    except NoFile:
        abort(404)

    # Mostly copied from flask/helpers.py, with modifications for GridFS
    if mimetype is None:
        mimetype = f.content_type

    headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            # Check if file has attachment filename as metadata,
            # else use filename
            attachment_filename = fs_meta.find_one(file_id)
            if attachment_filename is not None:
                attachment_filename = \
                    attachment_filename.get('attachment_filename')
            if attachment_filename is None:
                attachment_filename = f.name
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    data = wrap_file(request.environ, f, buffer_size=1024 * 256)

    rv = app.response_class(data, mimetype=mimetype, headers=headers,
                            direct_passthrough=True)
    rv.content_length = f.length
    rv.last_modified = f.upload_date
    rv.set_etag(f.md5)
    rv.cache_control.public = True
    if cache_timeout:
        rv.cache_control.max_age = cache_timeout
        rv.expires = int(time() + cache_timeout)
    return rv

def file_ext(filename):
    """Get file extension from file name"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1]
    else:
        return ''

def process_task(task):
    """Send task object to MongoDB queue, wait and return result"""
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
        return abort(404)
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

# ROUTING

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/write/<template>')
def write(template):
    """Write data to an Excel file using a template"""
    # This part is specific to the template
    message = request.args.get('message', 'Hello World!')
    template = '%s.xlsx' % template
    task_data = {'message': message}
    attachment_filename = template
    # Create new task 
    # ('assigned' is required by the worker, and needs to be set to False)
    task = {'assigned': False, 'type': 'write', 'template': template, 
            'data': task_data, 'attachment_filename': attachment_filename}
    result = process_task(task)
    # Send back url to result file
    file_url = '/api/files/%s' % result['file_id']
    return jsonify(file_url=file_url)

@app.route('/api/read/<template>', methods=['POST'])
def read(template):
    """Read data from an Excel file that follows a template"""
    f = request.files.get('files[]') # This is the name of input[type='file']
    if f and file_ext(f.filename) in ['xlsx']:
        # Save file and metadata to MongoDB
        filename = 'task_%s.xlsx' % template
        content_type = f.content_type
        attachment_filename = f.filename
        file_id = fs.put(f, filename=filename, content_type=content_type, 
                        label='task', attachment_filename=attachment_filename)
        # Create new task
        task = {'assigned': False, 'type': 'read', 'file_id': file_id}
        result = process_task(task)
        response = result['data'].get('response')
        return jsonify(response=response)
    else:
        abort(400)

@app.route('/api/files/<id>')
def files(id):
    """Serves a MongoDB result file given the file id"""
    try:
        file_id = ObjectId(id)
    except InvalidId:
        abort(404)
    response = send_mongo_file(file_id)
    return response

# Initialize
load_excel_templates()

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
