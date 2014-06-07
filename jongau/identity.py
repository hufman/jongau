import jongau.settings
import os.path
import time
import urlparse
from M2Crypto import ASN1, EVP, RSA, X509

jongau.settings.defaults['key_dir'] = '.'
jongau.settings.defaults['key_ttl'] = 1 * 60 * 60   # 1 hour
jongau.settings.defaults['key_size'] = 2048
jongau.settings.defaults['keys'] = []
jongau.settings.defaults['certificates'] = []
jongau.settings.defaults['sitename'] = 'https://localhost/'


def _generate_key(bits=None):
	""" Create a new RSA key """
	if not bits:
		bits = jongau.settings.key_size
	key_dir = jongau.settings.key_dir
	newkey = {}
	now = time.time()
	timeformat = '%Y%m%d_%H%M_{0:07}.key'.format(long(now%60*10000))
	newkey['filename'] = time.strftime(timeformat, time.gmtime(now))
	newkey['created'] = long(now)
	newkey['bits'] = bits
	newpath = os.path.join(key_dir, newkey['filename'])
	exponent = 65537
	rsa = RSA.gen_key(bits, exponent, lambda:None)
	rsa.save_pem(newpath, cipher=None)
	pk = EVP.PKey()
	pk.assign_rsa(rsa)
	newkey['modulus'] = pk.get_modulus().lower()
	newkey['exponent'] = exponent
	newkey['format'] = 'rsa'
	return newkey

def create_new_key():
	newkey = _generate_key()
	keys = jongau.settings.keys
	keys.append(newkey)
	jongau.settings.keys = keys
	create_certs(jongau.settings.sitename)

def _create_cert(key, webid_uri, time_len=365):
	key_dir = jongau.settings.key_dir
	key_path = os.path.join(key_dir, key['filename'])
	rsa = RSA.load_key(key_path)

	pk = EVP.PKey()
	pk.assign_rsa(rsa)

	parsed = urlparse.urlparse(webid_uri)
	issuer = X509.X509_Name()
	issuer.CN = parsed[1]
	subject = X509.X509_Name()
	subject.CN = parsed[1]

	cert = X509.X509()
	cert.set_serial_number(long(time.time()))
	cert.set_version(2)
	cert.set_issuer(issuer)
	cert.set_subject(subject)
	cert.set_pubkey(pk)

	now = long(key['created'])
	time_start = ASN1.ASN1_UTCTIME()
	time_start.set_time(now)
	time_end = ASN1.ASN1_UTCTIME()
	time_end.set_time(now + time_len * 24 * 60 * 60)
	cert.set_not_before(time_start)
	cert.set_not_after(time_end)

	cert.add_ext(X509.new_extension('basicContraints', 'CA:FALSE'))
	cert.add_ext(X509.new_extension('subjectAltName', "URI:"+webid_uri))
	cert.add_ext(X509.new_extension('subjectKeyIdentifier', cert.get_fingerprint()))

	cert.sign(pk, 'sha1')

	filename = '%s_%s_%s' % (key['filename'], parsed[1], long(time.time()))
	pathname = os.path.join(key_dir, filename)
	cert.save_pem(pathname)

	certificate = {}
	certificate['filename'] = filename
	certificate['keyname'] = key['filename']
	certificate['created'] = key['created']
	certificate['expiration'] = key['created'] + time_len * 24 * 60 * 60
	return certificate

def create_certs(sitename):
	""" Build selfsigned certs using all of the keys that we know about """
	keys = jongau.settings.keys
	certs = jongau.settings.certificates
	mycerts = [c for c in certs if c['sitename'] == sitename]
	mycerts_bykey = dict([(c['keyname'], c) for c in mycerts])
	webid = get_webid(sitename)

	for key in keys:
		if key['filename'] not in mycerts_bykey:
			cert = _create_cert(key, webid)
			cert['sitename'] = sitename
			certs.append(cert)
	jongau.settings.certificates = certs

def set_sitename(sitename):
	jongau.settings.sitename = sitename
	create_certs(sitename)

def get_webid(sitename=None):
	if not sitename:
		sitename = jongau.settings.sitename
	webid = urlparse.urljoin(sitename, 'webid/sevzi#subject')
	return webid
	
def get_client_cert(sitename=None):
	""" Returns the (certpath, keypath) to be used as this identity """
	if not sitename:
		sitename = jongau.settings.sitename
	key_ttl = jongau.settings.key_ttl
	key_dir = jongau.settings.key_dir
	certs = jongau.settings.certificates
	sitename = jongau.settings.sitename
	mycerts = [c for c in certs if c['sitename'] == sitename]

	mycerts = sorted(mycerts, key=lambda x:x['created'])
	curtime = time.time()
	stable_certs = [c for c in certs if c['created'] < curtime - key_ttl]
	chosen_cert = None
	if len(stable_certs) > 0:
		chosen_cert = stable_certs[-1]	# newest stable key
	else:
		chosen_cert = certs[0]	# oldest key
	certpath = os.path.join(key_dir, chosen_cert['filename'])
	keypath = os.path.join(key_dir, chosen_cert['keyname'])
	return (certpath, keypath)
