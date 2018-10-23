# configuration
from flask import Flask

DATABASE = './sedentary/sedentary.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'


app = Flask('sedentary')
app.config.from_object(__name__)

import sedentary.sedentary
from .serverside import TimeOut
from .serverside import DB_Abstraction

