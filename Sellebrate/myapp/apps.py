# myapp/apps.py

from django.apps import AppConfig
from pymongo import MongoClient
from django.conf import settings
import environ
import os

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        # Initialize environment variables
        env = environ.Env()
        env.read_env(os.path.join(settings.BASE_DIR, '.env'))

        # MongoDB configuration
        MONGO_DB_URI = env('MONGO_DB_URI')
        MONGO_DB_NAME = env('MONGO_DB_NAME')

        client = MongoClient(MONGO_DB_URI)
        settings.mongo_db = client[MONGO_DB_NAME]
