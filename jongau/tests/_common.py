import os
import unittest
import tempfile
import jongau.settings

class TestSession(unittest.TestCase):
	""" Creates a session with a blank settings file """
	def setUp(self):
		self.tempfiles = []
		(fd, self.settings_filename) = tempfile.mkstemp()
		os.close(fd)
		open(self.settings_filename, 'w').close()
		self.tempfiles.append(self.settings_filename)
		jongau.settings = jongau.settings_modules.JsonSettings(self.settings_filename)

	def tearDown(self):
		for key in jongau.settings.keys:
			path = os.path.join(jongau.settings.key_dir, key['filename'])
			self.tempfiles.append(path)
		for cert in jongau.settings.certificates:
			path = os.path.join(jongau.settings.key_dir, cert['filename'])
			self.tempfiles.append(path)
		for filename in self.tempfiles:
			try:
				os.unlink(filename)
			except:
				pass

