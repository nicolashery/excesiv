import os
from time import sleep, time
from urlparse import urlsplit, urlunsplit
from datetime import datetime

from flask import Flask, render_template, request, abort
from werkzeug.wsgi import wrap_file
from werkzeug.datastructures import Headers
from pymongo import Connection
from gridfs import GridFS, NoFile
from bson.objectid import ObjectId

# Envrionment variables for config
mongodb_uri = os.environ.get('MONGOLAB_URI', 'mongodb://localhost/excesiv')

# Other config
APP_DEBUG = True
# How long to wait for task to finish (in seconds) 
TASK_TIMEOUT = 10
# How long to wait before deleting a result file (in seconds)
EXPIRE_RESULT_FILE = 5 * 60

# Setup
app = Flask(__name__)
connection = Connection(mongodb_uri, tz_aware=True)
db_name = urlsplit(mongodb_uri).path.strip('/')
db = connection[db_name]
tasks = db.tasks
results = db.results
fs = GridFS(db)
fs_meta = db.fs.files
app.debug = APP_DEBUG

def load_excel_templates():
    # Delete any result files still in database
    for doc in fs_meta.find({'label': 'result'}):
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
    for filename in os.listdir(excel_dir):
        _, extension = os.path.splitext(filename)
        if extension == '.xlsx':
            filepath = os.path.join(excel_dir, filename)
            f = open(filepath, 'rb')
            fs.put(f, filename=filename, label='template')
            f.close()
            print 'Loaded template %s' % filename

# Mongo-Flask send file helper
# Adapted from Flask-PyMongo
# http://flask-pymongo.readthedocs.org/
def send_mongo_file(file_id, mimetype=None, as_attachment=False,
              attachment_filename=None, cache_timeout=60 * 60 * 12):
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/demo/')
def demo():
    message = request.args.get('message')
    template = 'demo.xlsx'
    if not message:
        abort(404)
    # Create new task 
    # ('assigned' is required by the worker, and needs to be set to False)
    task = {'message': message, 'template': template, 'assigned': False}
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
            if task_id == result['task']['_id']:
                break
        except StopIteration:
            sleep(1)
    if timeout:
        abort(404)
    # Clean out any result file past expiration date
    # Note: Ideally I would want to delete a result file after I'm done 
    # sending back to the client, but I haven't figured out how to do that
    for doc in fs_meta.find({'label': 'result'}):
        age = (datetime.now(doc['uploadDate'].tzinfo) - 
                doc['uploadDate']).total_seconds()
        if age > EXPIRE_RESULT_FILE:
            oid = doc['_id']
            fs.delete(ObjectId(oid))    
    # Get result file from database and send
    mimetype = 'application/vnd.openxmlformats-officedocument.\
                spreadsheetml.sheet'
    file_id = ObjectId(result['file']['_id'])
    response = send_mongo_file(file_id, 
                            mimetype=mimetype, 
                            as_attachment=True,
                            attachment_filename=template)
    return response

# Initialize
load_excel_templates()

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
