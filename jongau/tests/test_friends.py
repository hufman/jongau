import os.path
import rdflib
import httmock
import logging
import jongau.friends
import jongau.identity
import jongau.webid
import jongau.app as app
app = app.app
from jongau.tests._common import TestSession
from flask import g, request
#rdflib.plugin.register('sparql', rdflib.query.Processor,
#                       'rdfextras.sparql.processor', 'Processor')
#rdflib.plugin.register('sparql', rdflib.query.Result,
#                       'rdfextras.sparql.query', 'SPARQLQueryResult')
namespaces = {
	"dcterms": "http://purl.org/dc/terms/",
	"schema": "http://schema.org/",
	"cert": "http://www.w3.org/ns/auth/cert#",
	"foaf": "http://xmlns.com/foaf/0.1/",
	"bio": "http://purl.org/vocab/bio/0.1/",
	"xsd": "http://www.w3.org/2001/XMLSchema#",
	"mo": "http://purl.org/ontology/mo/",
	"event": "http://purl.org/NET/c4dm/event.owl#",
	"tl": "http://purl.org/NET/c4dm/timeline.owl#"
}


class TestPersistentClient(TestSession):
	""" Sets up a key at the beginning of a test session
	    Applies that key to the blank settings for each test from TestSession
	    Cleans up the key at the end of a test session
	    Also mocks all requests into self.remote_requests
	"""
	@classmethod
	def setUpClass(cls):
		cls.key = jongau.identity._generate_key(bits=512)
		cls.cert = jongau.identity._create_cert(cls.key, 'http://example.com/webid/sevzi#subject', 30)
		cls.cert['sitename'] = jongau.settings.sitename
		cls.keypath = os.path.join(jongau.settings.key_dir, cls.key['filename'])
		cls.certpath = os.path.join(jongau.settings.key_dir, cls.cert['filename'])
	@classmethod
	def tearDownClass(cls):
		os.unlink(cls.keypath)
		os.unlink(cls.certpath)

	def setUp(self):
		super(TestFriends, self).setUp()
		jongau.settings.keys = [self.key]
		jongau.settings.certificates = [self.cert]
		self.remote_requests = []	# logs any requested urls
		self.ident = jongau.identity.get_client_cert()
		self.set_mock_response(404, '')
		self.mockrequests = httmock.HTTMock(self.mock_logging)
		self.mockrequests.__enter__()
	def tearDown(self):
		# Don't let the TestSession teardown delete our key
		self.mockrequests.__exit__(None, None, None)
		keys = jongau.settings.keys
		certs = jongau.settings.certificates
		keys.remove(self.key)
		certs.remove(self.cert)
		jongau.settings.keys = keys
		jongau.settings.certificates = certs
		super(TestFriends, self).tearDown()

	@httmock.all_requests
	def mock_logging(self, url, request):
		self.remote_requests.append(request)
		return self.remote_response
	def set_mock_response(self, code, content):
		self.remote_response = httmock.response(code, content)

	def setUp(self):
		super(TestPersistentClient, self).setUp()
		jongau.settings.keys = [self.key]
		jongau.settings.certificates = [self.cert]
		self.remote_requests = []	# logs any requested urls
		self.ident = jongau.identity.get_client_cert()
		self.set_mock_response(404, '')
		self.mockrequests = httmock.HTTMock(self.mock_logging)
		self.mockrequests.__enter__()
	def tearDown(self):
		# Don't let the TestSession teardown delete our key
		self.mockrequests.__exit__(None, None, None)
		keys = jongau.settings.keys
		certs = jongau.settings.certificates
		keys.remove(self.key)
		certs.remove(self.cert)
		jongau.settings.keys = keys
		jongau.settings.certificates = certs
		super(TestPersistentClient, self).tearDown()

	@httmock.all_requests
	def mock_logging(self, url, request):
		self.remote_requests.append(request)
		return self.remote_response
	def set_mock_response(self, code, content):
		self.remote_response = httmock.response(code, content)

class TestFollowing(TestPersistentClient):
	""" Test client-side friendship functionality """
	def test_check_follow(self):
		self.set_mock_response(200, '')
		webid = 'http://remote.com/webid/sevzi#subject'
		valid = jongau.friends.check_follow(webid, self.ident)
		logging.debug("Requests: "+str(["%s %s"%(x.method, x.url) for x in self.remote_requests]))
		self.assertEqual(1, len(self.remote_requests))	# checked access
		self.assertEqual('http://remote.com/xukahecru', self.remote_requests[-1].url)
		self.assertTrue(valid)
		self.assertFalse(webid in jongau.settings.pending_following)
		self.assertTrue(webid in jongau.settings.following)
		self.assertEqual(0, len(jongau.settings.pending_following))
		self.assertEqual(1, len(jongau.settings.following))
	def test_check_follow_invalid(self):
		self.set_mock_response(403, '')
		webid = 'http://remote.com/webid/sevzi#subject'
		valid = jongau.friends.check_follow(webid, self.ident)
		self.assertEqual(1, len(self.remote_requests))	# checked that we don't follow
		self.assertEqual('http://remote.com/xukahecru', self.remote_requests[-1].url)
		self.assertFalse(valid)
		self.assertFalse(webid in jongau.settings.following)
		self.assertEqual(0, len(jongau.settings.pending_following))
		self.assertEqual(0, len(jongau.settings.following))

	def test_requestFollow_accept(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		jongau.friends.request_follow(webid, self.ident)
		logging.debug("Requests: "+str(["%s %s"%(x.method, x.url) for x in self.remote_requests]))
		self.assertEqual(2, len(self.remote_requests))	# checked that we don't follow
		self.assertEqual('http://remote.com/xukahecru', self.remote_requests[0].url)
		self.assertEqual('http://remote.com/cpecru', self.remote_requests[1].url)
		self.assertTrue(webid in jongau.settings.pending_following)
		self.assertFalse(webid in jongau.settings.following)
		self.assertEqual(1, len(jongau.settings.pending_following))
		self.assertEqual(0, len(jongau.settings.following))

		self.set_mock_response(200, '')
		valid = jongau.friends.check_follow(webid, self.ident)
		self.assertEqual(3, len(self.remote_requests))	# checked that we don't follow
		self.assertEqual('http://remote.com/xukahecru', self.remote_requests[2].url)
		self.assertFalse(webid in jongau.settings.pending_following)
		self.assertTrue(webid in jongau.settings.following)
		self.assertEqual(0, len(jongau.settings.pending_following))
		self.assertEqual(1, len(jongau.settings.following))

class TestFriends(TestPersistentClient):
	""" Test server-side friendship functionality """
	def test_friendship_loading_invalid(self):
		with app.test_request_context('/crunoi'):
			request.environ['webid.valid'] = False
			app.preprocess_request()
			self.assertFalse(hasattr(g, 'webid'))

	def test_friendship_loading_valid(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		with app.test_request_context('/crunoi'):
			request.environ['webid.valid'] = True
			request.environ['webid.uri'] = webid
			app.preprocess_request()
			self.assertTrue(hasattr(g, 'webid'))
			self.assertEqual(webid, g.webid)
			for rel in ['friends', 'following', 'pending_friends',
			            'pending_following']:
				self.assertTrue(hasattr(g, rel))
				self.assertFalse(getattr(g, rel))

	def test_friendship_loading_statuses(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		for mainrel in ['friends', 'following', 'pending_friends',
		                'pending_following']:
			setattr(jongau.settings, mainrel, [webid])
			if mainrel == 'friends':
				self.assertTrue(jongau.friends.is_friend(webid))
			else:
				self.assertFalse(jongau.friends.is_friend(webid))
			with app.test_request_context('/crunoi'):
				request.environ['webid.valid'] = True
				request.environ['webid.uri'] = webid
				app.preprocess_request()
				self.assertTrue(hasattr(g, 'webid'))
				self.assertEqual(webid, g.webid)
				for rel in ['friends', 'following', 'pending_friends',
					    'pending_following']:
					self.assertTrue(hasattr(g, rel))
					if mainrel == rel:
						self.assertTrue(getattr(g, rel))
					else:
						self.assertFalse(getattr(g, rel))
			setattr(jongau.settings, mainrel, [])

	def test_invalid_friendship_request(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		with app.test_request_context('/cpecru'):
			app.preprocess_request()
			resp = jongau.friends.request_friend()
			self.assertEqual(401, resp[1])
			for rel in ['friends', 'following', 'pending_friends',
				    'pending_following']:
				self.assertEqual([], getattr(jongau.settings, rel))

	def test_friendship_request(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		with app.test_request_context('/cpecru'):
			request.environ['webid.valid'] = True
			request.environ['webid.uri'] = webid
			app.preprocess_request()
			resp = jongau.friends.request_friend()
			self.assertEqual(200, resp[1])

			for rel in ['friends', 'following', 'pending_friends',
				    'pending_following']:
				if rel == 'pending_friends':
					self.assertEqual([webid], getattr(jongau.settings, rel))
				else:
					self.assertEqual([], getattr(jongau.settings, rel))

	def test_invalid_friendship_status(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		with app.test_request_context('/xukahecru'):
			app.preprocess_request()
			response = jongau.friends.check_friendship()
			self.assertEqual(401, response[1])

	def test_friendship_status_false(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		with app.test_request_context('/xukahecru'):
			request.environ['webid.valid'] = True
			request.environ['webid.uri'] = webid
			app.preprocess_request()
			response = jongau.friends.check_friendship()
			self.assertEqual(403, response[1])

	def test_friendship_status_true(self):
		webid = 'http://remote.com/webid/sevzi#subject'
		jongau.friends.approve_friend(webid)
		self.assertEqual([webid], jongau.settings.friends)
		ping_url = 'http://remote.com/crunoi'
		self.assertEqual(1, len(self.remote_requests))
		self.assertEqual(ping_url, self.remote_requests[0].url)
		with app.test_request_context('/xukahecru'):
			request.environ['webid.valid'] = True
			request.environ['webid.uri'] = webid
			app.preprocess_request()
			response = jongau.friends.check_friendship()
			self.assertEqual(200, response[1])
		jongau.friends.delete_friend(webid)
		self.assertEqual(2, len(self.remote_requests))
		self.assertEqual(ping_url, self.remote_requests[1].url)
		jongau.friends.delete_friend(webid)
		self.assertEqual(3, len(self.remote_requests))
		self.assertEqual(ping_url, self.remote_requests[2].url)

