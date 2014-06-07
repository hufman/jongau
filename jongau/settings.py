import os
import os.path
import logging


class FreshDefaults(dict):
	def __getitem__(self, key):
		value = super(FreshDefaults, self).__getitem__(key)
		if isinstance(value, dict):
			return dict(value)
		if isinstance(value, list):
			return list(value)
		return value
	def __getattr__(self, key):
		return self[key]

	def __setattr__(self, key, value):
		self[key] = value

	def __delattr__(self, key):
		del self[key]


class Settings(object):
	def __init__(self):
		if self.__class__ == Settings:
			raise NotImplementedError("Don't instantiate this abstract class")
		self.__dict__['_settings'] = {}

	def __getattr__(self, key):
		self.load()
		return self._settings[key]

	def __setattr__(self, key, value):
		if key == '_settings':
			if hasattr(value, '__getitem__'):
				self.__dict__['_settings'] = value
			else:
				raise ValueError('_settings must look like a dict')
		else:
			self._settings[key] = value
		self.save()

	def __delattr__(self, key):
		del self._settings[key]

	def __dir__(self):
		ret = list(self._settings.keys())
		ret.append('_settings')
		return ret

class DefaultSettings(Settings):
	""" Peeks inside a global defaults dictionary for unset settings """
	def __init__(self):
		super(DefaultSettings, self).__init__()

	def __getattr__(self, key):
		if key == 'defaults':
			return defaults
		self.load()
		if key in self._settings:
			return self._settings[key]
		else:
			return defaults[key]

	def __setattr__(self, key, value):
		if key == 'defaults':
			if hasattr(value, '__getitem__'):
				global defaults
				defaults = FreshDefaults(value)
			else:
				raise ValueError('defaults must look like a dict')
		else:
			super(DefaultSettings, self).__setattr__(key, value)

	def __dir__(self):
		ret = super(DefaultSettings, self).__dir__()
		ret.extend(defaults.keys())
		ret.append('defaults')
		return ret
defaults = FreshDefaults()

import json
class JsonSettings(DefaultSettings):
	def __init__(self, filename):
		super(JsonSettings, self).__init__()
		self.__dict__['_filename'] = filename

	def load(self):
		if not os.path.exists(self._filename):
			return
		if os.path.getsize(self._filename) == 0:
			return
		try:
			with open(self._filename, 'r') as input:
				self._settings = json.load(input)
		except Exception as e:
			logging.warn("Could not load settings file %s: %s"%(self._filename, e))

	def save(self):
		try:
			tmpfilename = self._filename + '.tmp'
			with open(tmpfilename, 'w') as output:
				json.dump(self._settings, output, ensure_ascii=False, sort_keys=True, indent=4)
			os.rename(tmpfilename, self._filename)
		except Exception as e:
			logging.error("Could not save settings file %s: %s"%(self._filename, e))
