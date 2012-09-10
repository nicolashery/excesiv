"""
    excesiv

    Application component to generate and read Excel files using Apache POI
    https://github.com/nicolahery/excesiv
"""

__version__ = '0.1dev'

# To add Excesiv to a Flask app
from .blueprint import excesiv_blueprint, xs

# To use just the Excesiv library outside of a Flask app
from .core import Excesiv

# Helper methods
from .core import datetime_to_xldate, xldate_to_datetime
