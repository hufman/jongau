import jongau.identity
import jongau.webid
import jongau.app as app
app = app.app
import rdflib
from jongau.tests._common import TestSession
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


class TestWebid(TestSession):
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
