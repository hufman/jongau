import os
from . import settings as settings_modules
settings_filename = os.environ.get('JONGAU_SETINGS', 'settings.json')
settings = settings_modules.JsonSettings(settings_filename)

