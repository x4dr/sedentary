# configuration
from flask import Flask

DATABASE = './main_package/main_package.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'


app = Flask('main_package')
app.config.from_object(__name__)

# import main_package.sedentary
from .serverside import TimeOut
from .serverside import DB_Abstraction

