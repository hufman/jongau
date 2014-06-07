import tempfile
import os
import jongau
import unittest
import json


class TestSettings(unittest.TestCase):
	def setUp(self):
		(fd, self.settings_filename) = tempfile.mkstemp()
		os.close(fd)
		open(self.settings_filename, 'w').close()
		jongau.settings = jongau.settings_modules.JsonSettings(self.settings_filename)

	def tearDown(self):
		try:
			os.unlink(self.settings_filename)
		except:
			pass

	def test_addSetting(self):
		jongau.settings.test = 'Hi'
		self.assertEqual('Hi', jongau.settings.test)
		self.assertTrue('test' in dir(jongau.settings))
		with open(self.settings_filename, 'r') as fd:
			parsed = json.load(fd)
			self.assertEqual('Hi', parsed['test'])

	def test_addDefaultSetting(self):
		jongau.settings.defaults.fifty = 'Five'
		jongau.settings.defaults['sisty'] = '6'
		self.assertTrue('fifty' in dir(jongau.settings))
		self.assertTrue('sisty' in dir(jongau.settings))
		self.assertEqual('Five', jongau.settings.fifty)
		self.assertEqual('6', jongau.settings.sisty)
		self.assertEqual(0, os.path.getsize(self.settings_filename))

		jongau.settings.fifty = 'Six'
		self.assertEqual('Six', jongau.settings.fifty)
		self.assertTrue('fifty' in dir(jongau.settings))
		with open(self.settings_filename, 'r') as fd:
			parsed = json.load(fd)
			self.assertTrue('fifty' in parsed)
			self.assertEqual('Six', parsed['fifty'])

	def test_persistentDefaultSettings(self):
		jongau.settings.defaults.fifty = 'Five'
		with tempfile.NamedTemporaryFile() as tmpfile:
			tmpsettings = jongau.settings_modules.JsonSettings(tmpfile.name)
			self.assertTrue('fifty' in dir(tmpsettings))
			self.assertEqual('Five', tmpsettings.fifty)

	def test_readonlyDefaultSettingsList(self):
		jongau.settings.defaults.testlist = []
		testlist = jongau.settings.testlist
		testlist.append(1)
		jongau.settings.testlist = testlist
		self.assertEqual(1, testlist[0])
		self.assertEqual(0, len(jongau.settings.defaults.testlist))

	def test_readonlyDefaultSettingsDict(self):
		jongau.settings.defaults.testdict = {}
		testdict = jongau.settings.testdict
		testdict[1] = 2
		jongau.settings.testdict = testdict
		self.assertEqual(2, testdict[1])
		self.assertEqual(0, len(jongau.settings.defaults.testdict))
