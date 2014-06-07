import tempfile
import unittest
import jongau.identity
import jongau.webid
import jongau.app as app
app = app.app
import rdflib
import os
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


class TestWebid(unittest.TestCase):
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

	def test_singlekey(self):
		jongau.identity.create_new_key()
		self.assertEqual(1, len(jongau.settings.keys))
		with app.test_request_context('/webid/sevzi'):
			response = jongau.webid.webid_self()
			data = response.get_data()
			graph = rdflib.Graph()
			graph.parse(data=data, format='xml')
			modulus = jongau.settings.keys[0]['modulus']
			self.assertTrue(modulus in data)
			query = 'SELECT ?user WHERE { ?user cert:key ?key . ?key cert:modulus "%s"^^xsd:hexBinary . }' % modulus
			res = graph.query(query, initNs=namespaces)
			self.assertEqual(1, len(res))

	def test_multiplekeys(self):
		jongau.identity.create_new_key()
		jongau.identity.create_new_key()
		self.assertEqual(2, len(jongau.settings.keys))
		with app.test_request_context('/webid/sevzi', headers=[('Accept', 'text/turtle')]):
			response = jongau.webid.webid_self()
			data = response.get_data()
			graph = rdflib.Graph()
			graph.parse(data=data, format='turtle')
			for key in jongau.settings.keys:
				modulus = key['modulus']
				self.assertTrue(modulus in data)
				query = 'SELECT ?user WHERE { ?user cert:key ?key . ?key cert:modulus "%s"^^xsd:hexBinary . }' % modulus
				res = graph.query(query, initNs=namespaces)
				self.assertEqual(1, len(res))
