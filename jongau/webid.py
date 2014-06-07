from .app import app as app
import jongau.identity
import jongau.settings
from flask import url_for
from flask_rdf import flask_rdf
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, XSD
CERT = Namespace('http://www.w3.org/ns/auth/cert#')


@app.route('/webid/sevzi')
@flask_rdf
def webid_self():
	graph = Graph('IOMemory', BNode())
	subject = URIRef(jongau.identity.get_webid())

	for key in jongau.settings.keys:
		cert = BNode()
		graph.add((subject, CERT.key, cert))
		graph.add((cert, RDF.type, CERT.RSAPublicKey))
		graph.add((cert, CERT.modulus, Literal(key['modulus'], datatype=XSD.hexBinary)))
		graph.add((cert, CERT.exponent, Literal(key['exponent'], datatype=XSD.integer)))
	return graph


