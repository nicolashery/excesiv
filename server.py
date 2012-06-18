import os
from time import sleep, time
from urlparse import urlsplit, urlunsplit

from flask import Flask, request, jsonify
from pymongo import Connection

# Envrionment variables for config
mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost/excesiv')

# Parse mongdb_uri
mongodb_uri = urlsplit(mongodb_uri)
db_name = mongodb_uri.path.strip('/')
mongodb_uri = urlunsplit((mongodb_uri.scheme, mongodb_uri.netloc,
                            '', '', ''))

# Initialize
app = Flask(__name__)
connection = Connection(mongodb_uri)
db = connection[db_name]
tasks = db.tasks
results = db.results

app.debug = True

TASK_TIMEOUT = 5 # How long to wait for task to finish (in seconds) 

@app.route('/')
def index():
    return 'Excesiv'

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

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
