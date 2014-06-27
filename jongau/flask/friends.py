import jongau.identity
import jongau.settings
import jongau.webid
import jongau.friends
from . import app
from flask import g, request
import requests
import urlparse
import logging
logger = logging.getLogger(__name__)

jongau.settings.defaults['friends'] = []	# people allowed to access
jongau.settings.defaults['following'] = []	# people we have access to
jongau.settings.defaults['pending_friends'] = []	# people that want to access
jongau.settings.defaults['pending_following'] = []	# people that we are trying to access


@app.before_request
def load_friendship(*args, **kwargs):
	""" Whenever an incoming request comes in, look up the webid
	    to determine whether we are friends with it
	    Will update g.friends, g.following,
	    g.pending_friends, and g.pending_following to match
	"""
	if 'webid.valid' in request.environ and \
	   request.environ['webid.valid'] and \
	   'webid.uri' in request.environ:
		webid = str(request.environ['webid.uri'])
		g.webid = webid
		for rel in ['friends', 'following', 'pending_friends',
		            'pending_following']:
			if webid in getattr(jongau.settings, rel):
				setattr(g, rel, True)
			else:
				setattr(g, rel, False)

@app.route('/crunoi')
def follow_callback():
	""" Called by remote followed server when an update to friendship status happens """
	if hasattr(g, 'webid'):
		ident = jongau.identity.get_client_cert()
		jongau.friends.check_follow(g.webid, ident)
		return 'Acknowledged', 200
	else:
		return 'Invalid WebID', 401

@app.route('/cpecru')
def request_friend():
	""" Called by a client when they want to follow us """
	if hasattr(g, 'webid'):
		jongau.friends.requested_friend(g.webid)
		return 'Requested', 200
	else:
		return 'Invalid WebID', 401

@app.route('/xukahecru')
def check_friendship():
	if hasattr(g, 'webid') and jongau.friends.is_friend(g.webid):
		return 'Is friend', 200
	elif hasattr(g, 'webid'):
		return 'Is not friend', 403
	else:
		return 'Invalid WebID', 401
