"""
    excesiv

    Application component to generate and read Excel files using Apache POI
    https://github.com/nicolahery/excesiv
"""

__version__ = '0.1'

# Tu add Excesiv to a Flask application
from server import excesiv_blueprint, xs
# To use just the Excesiv library without a server
from excesiv import Excesiv
