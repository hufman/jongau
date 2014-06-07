import tempfile
import os
import os
import jongau.identity
import unittest
import json
import M2Crypto


class TestIdentity(unittest.TestCase):
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

	def test_addKey(self):
		key = jongau.identity._generate_key(bits=512)
		self.assertTrue('modulus' in key)
		self.assertTrue('filename' in key)
		self.assertTrue('bits' in key)
		self.assertEqual(512, key['bits'])
		keypath = os.path.join(jongau.settings.key_dir, key['filename'])
		self.assertTrue(os.path.isfile(keypath))
		self.tempfiles.append(keypath)

	def test_addDefaultKey(self):
		key = jongau.identity._generate_key()
		self.assertTrue('modulus' in key)
		self.assertTrue('filename' in key)
		self.assertTrue('bits' in key)
		self.assertEqual(jongau.settings.defaults.key_size, key['bits'])
		keypath = os.path.join(jongau.settings.key_dir, key['filename'])
		self.assertTrue(os.path.isfile(keypath))
		self.tempfiles.append(keypath)

	def test_createCert(self):
		key = jongau.identity._generate_key(bits=512)
		cert = jongau.identity._create_cert(key, 'http://example.com/webid#me', 30)
		self.assertEqual(key['created'], cert['created'])
		self.assertEqual(key['created'] + 30*24*60*60, cert['expiration'])
		keypath = os.path.join(jongau.settings.key_dir, key['filename'])
		self.assertTrue(os.path.isfile(keypath))
		self.tempfiles.append(keypath)
		certpath = os.path.join(jongau.settings.key_dir, cert['filename'])
		self.assertTrue(os.path.isfile(certpath))
		self.tempfiles.append(certpath)

	def test_addKeyProper(self):
		self.assertEqual(0, len(jongau.settings.keys))
		self.assertEqual(0, len(jongau.settings.certificates))
		jongau.identity.create_new_key()
		self.assertEqual(1, len(jongau.settings.keys))
		self.assertEqual(1, len(jongau.settings.certificates))
		key = jongau.settings.keys[0]
		cert = jongau.settings.certificates[0]
		self.assertTrue('modulus' in key)
		self.assertTrue('filename' in key)
		self.assertTrue('bits' in key)
		self.assertEqual(jongau.settings.defaults.key_size, key['bits'])
		keypath = os.path.join(jongau.settings.key_dir, key['filename'])
		self.assertTrue(os.path.isfile(keypath))
		certpath = os.path.join(jongau.settings.key_dir, cert['filename'])
		self.assertTrue(os.path.isfile(certpath))

		x509 = M2Crypto.X509.load_cert(certpath)
		altName = x509.get_ext('subjectAltName').get_value()
		self.assertEqual('URI:' + jongau.settings.sitename + 'webid/sevzi#subject', altName)

	def test_changesite(self):
		self.assertEqual(0, len(jongau.settings.keys))
		self.assertEqual(0, len(jongau.settings.certificates))
		jongau.identity.create_new_key()
		self.assertEqual(1, len(jongau.settings.keys))
		self.assertEqual(1, len(jongau.settings.certificates))
		cert = jongau.settings.certificates[0]
		self.assertEqual(jongau.settings.defaults['sitename'], cert['sitename'])
		certpath = os.path.join(jongau.settings.key_dir, cert['filename'])
		self.assertTrue(os.path.isfile(certpath))

		jongau.identity.set_sitename('http://example.com/')
		self.assertEqual('http://example.com/', jongau.settings.sitename)
		self.assertEqual(1, len(jongau.settings.keys))
		self.assertEqual(2, len(jongau.settings.certificates))
		cert = jongau.settings.certificates[1]
		self.assertEqual(jongau.settings.sitename, cert['sitename'])
		certpath = os.path.join(jongau.settings.key_dir, cert['filename'])
		self.assertTrue(os.path.isfile(certpath))

		x509 = M2Crypto.X509.load_cert(certpath)
		altName = x509.get_ext('subjectAltName').get_value()
		self.assertEqual('URI:' + jongau.settings.sitename + 'webid/sevzi#subject', altName)

	def test_selectcert(self):
		""" Test that get_client_cert picks the right cert
		    If there are only certs younger than key_ttl
		    it should pick the oldest one
		"""
		key_dir = jongau.settings.key_dir
		jongau.identity.create_new_key()
		jongau.identity.create_new_key()
		self.assertEqual(2, len(jongau.settings.keys))
		self.assertEqual(2, len(jongau.settings.certificates))
		key = jongau.settings.keys[0]
		cert = jongau.settings.certificates[0]
		keypath = os.path.join(key_dir, key['filename'])
		certpath = os.path.join(key_dir, cert['filename'])

		(chose_cert, chose_key) = jongau.identity.get_client_cert()
		self.assertEqual(certpath, chose_cert)
		self.assertEqual(keypath, chose_key)

	def test_selectoldcert(self):
		""" Test that get_client_cert picks the right cert
		    If there are multiple certs older than the key_ttl
		    it should pick the newest one that is older than key_ttl
		"""
		key_dir = jongau.settings.key_dir
		key_ttl = jongau.settings.key_ttl
		jongau.identity.create_new_key()
		jongau.identity.create_new_key()
		jongau.identity.create_new_key()
		self.assertEqual(3, len(jongau.settings.keys))
		self.assertEqual(3, len(jongau.settings.certificates))
		keys = jongau.settings.keys
		certs = jongau.settings.certificates
		key = keys[0]
		cert = certs[0]
		key['created'] = key['created'] - key_ttl * 4
		cert['created'] = cert['created'] - key_ttl * 4
		key = keys[1]
		cert = certs[1]
		key['created'] = key['created'] - key_ttl * 3
		cert['created'] = cert['created'] - key_ttl * 3
		jongau.settings.keys = keys
		jongau.settings.certificates = certs
		keypath = os.path.join(key_dir, key['filename'])
		certpath = os.path.join(key_dir, cert['filename'])

		(chose_cert, chose_key) = jongau.identity.get_client_cert()
		self.assertEqual(certpath, chose_cert)
		self.assertEqual(keypath, chose_key)
