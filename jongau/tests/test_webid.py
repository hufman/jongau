import jongau.identity
import jongau.webid
import jongau.flask.webid
from jongau.flask import app
import rdflib
from jongau.tests._common import TestSession
import httmock
from flask_rdf import flask_rdf
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
			response = jongau.flask.webid.webid_self()
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
			response = jongau.flask.webid.webid_self()
			data = response.get_data()
			graph = rdflib.Graph()
			graph.parse(data=data, format='turtle')
			for key in jongau.settings.keys:
				modulus = key['modulus']
				self.assertTrue(modulus in data)
				query = 'SELECT ?user WHERE { ?user cert:key ?key . ?key cert:modulus "%s"^^xsd:hexBinary . }' % modulus
				res = graph.query(query, initNs=namespaces)
				self.assertEqual(1, len(res))

	def test_query(self):
		@httmock.all_requests
		@flask_rdf
		def rdf_mock(url, request):
			if 'foaf' in url: return rdf_mock_foaf(url, request)
			if 'webid' in url: return rdf_mock_webid(url, request)
		def rdf_mock_webid(url, request):
			graph = Graph('IOMemory', BNode())
			graph.add((URIRef(url), RDF.sameAs, URIRef(url+"/foaf")))
			return graph
		def rdf_mock_foaf(url, request):
			graph = Graph('IOMemory', BNode())
			graph.add((URIRef(url), FOAF.name, Literal('Test')))
			return graph

		jongau.identity.create_new_key()
		with httmock.HTTMock(rdf_mock):
			graph = jongau.webid.fetch_rdf('http://example/foaf')
			self.assertTrue(1, len(graph))
			graph = jongau.webid.fetch_rdf('http://example/webid')
			self.assertTrue(1, len(graph))
			graph = jongau.webid.fetch_webid('http://example/webid')
			self.assertTrue(2, len(graph))

	def test_server_root(self):
		self.assertEqual('http://example', jongau.webid.get_server_root('http://example/webid/test'))
