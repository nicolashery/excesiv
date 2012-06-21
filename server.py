import os
from time import sleep, time
from urlparse import urlsplit, urlunsplit

from flask import Flask, render_template, request, jsonify
from pymongo import Connection
from gridfs import GridFS
from bson.objectid import ObjectId

# Envrionment variables for config
mongodb_uri = os.environ.get('MONGOLAB_URI', 'mongodb://localhost/excesiv')

# Other config
APP_DEBUG = True
TASK_TIMEOUT = 5 # How long to wait for task to finish (in seconds) 

# Setup
app = Flask(__name__)
connection = Connection(mongodb_uri)
db_name = urlsplit(mongodb_uri).path.strip('/')
db = connection[db_name]
tasks = db.tasks
results = db.results
fs = GridFS(db)
fs_meta = db.fs.files
app.debug = APP_DEBUG

def load_excel_templates():
    # Drop all templates currently in GridFS
    for meta in fs_meta.find({'template': True}):
        filename = meta['filename']
        oid = meta['_id']
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
            fs.put(f, filename=filename, template=True)
            f.close()
            print 'Loaded template %s' % filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/demo/')
def demo():
    message = request.args.get('message')
    if not message:
        return ('Message required', 400)
    # Create new task 
    # ('assigned' is required by the worker, and needs to be set to False)
    task = {'message': message, 'assigned': False}
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
            doc = cursor.next()
            # Break if we have the result for this task
            if task_id == doc['task']['_id']:
                break
        except StopIteration:
            sleep(1)
    if timeout:
        return ('Task timed out', 504)
    # Process result
    return jsonify({'message': doc['message']})

# Initialize
load_excel_templates()

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
