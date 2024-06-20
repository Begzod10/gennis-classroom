#!/venv python3
# -*- coding: utf-8 -*-
# The above encoding declaration is required and the file must be saved as UTF-8
from flask import *
from backend.models.basic_model import *
from flask_cors import CORS, cross_origin
from pprint import pprint
from werkzeug.utils import *
import os
import json
from flask_jwt_extended import JWTManager, create_refresh_token, get_jwt_identity, create_access_token, \
    unset_jwt_cookies, jwt_required

app = Flask(__name__, static_folder="frontend/build", static_url_path="/")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# CORS(app, supports_credentials=True, resources=r'/api/*',
#      allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"])
# cors_api1 = {
#     "origins": ['http://192.168.1.13:5001/api/'],
#     "methods": ['POST', 'GET', 'OPTIONS'],
#     "allow_headers": ["Authorization", "Content-Type"]
# }
# cors_api2 = {
#     "origins": ['http://192.168.1.13:5001/api/'],
#     "methods": ['POST', 'GET', 'OPTIONS'],
#     "allow_headers": ["Authorization", "Content-Type"]
# }
# CORS(app, resources={
#     r'/api/*': cors_api1
# })

app.config.from_object('backend.models.config')
db = db_setup(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
api = '/api'
# platform_server = 'https://www.gennis.uz'
platform_server = "http://192.168.68.100:5002"

# basics
from backend.basics.views import *
# create basics
from backend.create_basics.views import *

# group
from backend.group.views import *

# student
from backend.student.views import *

# user
from backend.user.views import *

# teacher
from backend.teacher.views import *

if __name__ == '__main__':
    app.run()
