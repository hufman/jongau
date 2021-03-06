import jongau.identity
import jongau.settings
import requests
import logging
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, XSD
CERT = Namespace('http://www.w3.org/ns/auth/cert#')


def fetch_webid(webid):
	""" Fetches an rdf object without sending a webid
	    A webid rdf object should not require authentication
	    Returns an rdflib graph, which will have content unless there was an error
	"""
	graph = Graph('IOMemory', BNode())
	headers = {'Content-type': 'text/turtle'}
	try:
		request = requests.get(webid, headers=headers)
		graph.parse(data=request.text, format='turtle')
	except Exception as e:
		logging.warning("Failed to fetch webid %s: %s"%(webid, e))
	query = 'SELECT ?source WHERE { <%s> rdf:sameAs ?source . }' % (webid,)
	res = graph.query(query)
	for source in res:
		parsed_source = fetch_rdf(source[0])
		if parsed_source:
			graph = graph + parsed_source
	return graph


def fetch_rdf(rdf, cert=None):
	""" Fetches an rdf object and sends the server's webid for authentication
	    A custom (cert, key) pair can be given, instead of using the server's webid
	    Returns an rdflib graph, which will have content unless there was an error
	"""
	graph = Graph('IOMemory', BNode())
	headers = {'Content-type': 'text/turtle'}
	if not cert:
		cert = jongau.identity.get_client_cert()
	try:
		request = requests.get(rdf, headers=headers, cert=cert)
		graph.parse(data=request.text, format='turtle')
	except Exception as e:
		logging.warning("Failed to fetch rdf url %s: %s"%(rdf, e))
	return graph


def get_server_root(webid):
	index = webid.find('/webid/')
	if index >= 0:
		return webid[:index]
	return webid
