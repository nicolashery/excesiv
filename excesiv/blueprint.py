import os
from time import time

from flask import Blueprint, current_app
from flask import request, abort, jsonify
from werkzeug.wsgi import wrap_file
from werkzeug.datastructures import Headers

from .core import Excesiv

# CONFIG
# -----------------------------------------------
FILE_INPUT_NAME = 'files[]' # This is the name of input[type='file']

# MAIN OBJECTS
# -----------------------------------------------
# The blueprint can be registered to any Flask app 
# to give it Excesiv's functionalities
excesiv_blueprint = Blueprint('excesiv', __name__)

# Core object to use task queue and file system
xs = Excesiv()

# SETUP
# -----------------------------------------------
@excesiv_blueprint.before_app_first_request
def initialize():
    """Connect to database and load Excel templates"""
    # Connect to database
    print 'Connecting to MongoDB..'
    # MONGOLAB_URI: Heroku, MONGODB_URL: Stackato
    mongodb_uri = os.environ.get('MONGOLAB_URI', 
                os.environ.get('MONGODB_URL', 'mongodb://localhost/excesiv'))
    xs.connect_db(mongodb_uri)
    # Load Excel templates
    excel_dir = current_app.config.get('EXCEL_DIR')
    if excel_dir:
        xs.load_templates(excel_dir)
    else:
        print "No Excel template directory defined, use app.config['EXCEL_DIR'] to define one."

# HELPERS
# -----------------------------------------------
def send_mongo_file(id, mimetype=None, as_attachment=True,
              attachment_filename=None, cache_timeout=60 * 60 * 12):
    """
    Mongo-Flask send file helper
    Adapted from Flask-PyMongo
    http://flask-pymongo.readthedocs.org/
    """
    f = xs.get_file(id)
    if not f:
        abort(404)

    # Mostly copied from flask/helpers.py, with modifications for GridFS
    if mimetype is None:
        mimetype = f.content_type

    headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            # Check if file has attachment filename as metadata,
            # else use filename
            attachment_filename = xs.get_file_meta(id)
            if attachment_filename is not None:
                attachment_filename = \
                    attachment_filename.get('attachment_filename')
            if attachment_filename is None:
                attachment_filename = f.name
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    data = wrap_file(request.environ, f, buffer_size=1024 * 256)

    rv = current_app.response_class(data, mimetype=mimetype, headers=headers,
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

# ROUTING
# -----------------------------------------------
@excesiv_blueprint.route('/api/write/<template>', methods=['POST'])
def write(template):
    """Write data to an Excel file using a template"""
    # Task defaults
    # ('assigned' is required by the worker, and needs to be set to False)
    task = {'assigned': False, 'type': 'write', 
            'template': '%s.xlsx' % template, 
            'data': {}, 
            'attachment_filename': '%s.xlsx' % template}
    # Use registered task method for this template to create new task
    process_request = xs.get_task_method('write', template)
    if not process_request:
        abort(404)
    task.update(process_request(request))
    result = xs.process_task(task)
    if not result:
        # Probably timed out, i.e. worker not running
        abort(404)
    if 'error' in result.keys():
        # We got an error processing the task
        response = {'error': result['error']}
    else:
        # Send back url to result file
        response = {'file_url': '/api/files/%s' % result['file_id']}
    return jsonify(response)

@excesiv_blueprint.route('/api/read/<template>', methods=['POST'])
def read(template):
    """Read data from an Excel file that follows a template"""
    f = request.files.get(FILE_INPUT_NAME) 
    if f and file_ext(f.filename) in ['xlsx']:
        # Save file and metadata to MongoDB
        filename = 'task_%s.xlsx' % template
        content_type = f.content_type
        attachment_filename = f.filename
        file_id = xs.fs.put(f, filename=filename, content_type=content_type, 
                        label='task', attachment_filename=attachment_filename)
        # Create and process new task
        task = {'assigned': False, 'type': 'read', 'file_id': file_id}
        result = xs.process_task(task)
        if not result:
            # Probably timed out, i.e. worker not running
            abort(404)
        if 'error' in result.keys():
            # We got an error processing the task
            response = {'error': result['error']}
        else:
            # Pass results to registered task method for this template
            process_result = xs.get_task_method('read', template)
            if not process_result:
                abort(404)
            # Send back processed result data
            response = process_result(result)
        return jsonify(response)
    else:
        abort(400)

@excesiv_blueprint.route('/api/files/<id>')
def files(id):
    """Serves a MongoDB result file given the file id"""
    response = send_mongo_file(id)
    return response
