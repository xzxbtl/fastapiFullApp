from typing import Any
from dotenv import load_dotenv
from authx import AuthX, AuthXConfig
import os


class AuthXConfigModel(AuthXConfig):
    def __init__(self, **values: Any):
        super().__init__(**values)
        self.JWT_SECRET_KEY = str(os.getenv('SECRET_TOKEN'))
        self.JWT_ACCESS_COOKIE_NAME = 'user_access_token'
        self.JWT_REFRESH_COOKIE_NAME = 'user_refresh_token'
        self.JWT_TOKEN_LOCATION = ["cookies"]
        self.JWT_COOKIE_CSRF_PROTECT = False


load_dotenv(dotenv_path='jwt_token.env')
security = AuthX(config=AuthXConfigModel())


class AdminConfig:
    def __init__(self):
        self.ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
        self.ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
        self.ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
        self.ADMIN_BACKEND_LVL = os.getenv('ADMIN_ACCESS_LVL')


load_dotenv(dotenv_path='admin_conf.env')
admin_config = AdminConfig()
