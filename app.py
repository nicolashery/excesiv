import os

from flask import Flask, render_template

from excesiv import excesiv_blueprint, xs
from demo import generate_demo_data, interpret_demo_data

# CONFIG
# -----------------------------------------------
APP_DEBUG = False

# APP
# -----------------------------------------------
app = Flask(__name__)

# Add Excesiv's routes and initialization to the app
app.register_blueprint(excesiv_blueprint)

app.debug = APP_DEBUG
# Tell Excesiv where to find the Excel templates
app.config['EXCEL_DIR'] = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)), 
                            'excel')
# This config value tells the demo app to use minified js & css in production,
# by setting the environment variable APP_ENV=production
app.config['APP_ENV'] = os.environ.get('APP_ENV', 'development') 

# ROUTING
# -----------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# EXCESIV TASK METHODS
# -----------------------------------------------
def demo_write(request):
    """Write task method for the demo"""
    n_rows = request.json.get('n_rows', 10)
    rand_max = request.json.get('rand_max', 3)
    data = generate_demo_data(n_rows, rand_max)
    return {'data': data}

def demo_read(result):
    """Read task method for the demo"""
    return interpret_demo_data(result['data'])

xs.register_task_method('write', 'demo', demo_write)
xs.register_task_method('read', 'demo', demo_read)

# RUN
# -----------------------------------------------
if __name__ == '__main__':
    app.run()
