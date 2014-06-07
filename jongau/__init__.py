import os
from . import settings as settings_modules
from . import app as app_module
settings_filename = os.environ.get('JONGAU_SETINGS', 'settings.json')
settings = settings_modules.JsonSettings(settings_filename)

if __name__ == '__main__':
	app_module.app.run()
