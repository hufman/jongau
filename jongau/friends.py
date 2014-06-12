import jongau.identity
import jongau.settings
import jongau.webid
from .app import app
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


def list_friends():
	return list(jongau.settings.friends)

def list_following():
	return list(jongau.settings.following)

def list_pending_friends():
	return list(jongau.settings.pending_friends)

def list_pending_following():
	return list(jongau.settings.pending_following)


def approve_friend(webid):
	""" Grant access to a specific webid
	    Also removes that webid from the pending_friends list
	"""
	friends = jongau.settings.friends
	if webid not in friends:
		friends.append(webid)
		jongau.settings.friends = friends
	pending_friends = jongau.settings.pending_friends
	if webid in pending_friends:
		while webid in pending_friends:
			pending_friends.remove(webid)
		jongau.settings.pending_friends = pending_friends
	ping_friend(webid)

def delete_friend(webid):
	""" Revoke access to a specific webid
	    Also removes that webid from the pending_friends list
	"""
	friends = jongau.settings.friends
	if webid in friends:
		while webid in friends:
			friends.remove(webid)
		jongau.settings.friends = friends
	pending_friends = jongau.settings.pending_friends
	if webid in pending_friends:
		while webid in pending_friends:
			pending_friends.remove(webid)
		jongau.settings.pending_friends = pending_friends
	ping_friend(webid)

def ping_friend(webid, ident=None):
	""" Notifies the webid about a change in friendship """
	if not ident:
		ident = jongau.identity.get_client_cert()
	server_root = jongau.webid.get_server_root(webid)
	ping_url = urlparse.urljoin(server_root, 'crunoi')
	resp = requests.post(ping_url, cert=ident)

def is_friend(webid):
	return webid in jongau.settings.friends

def requested_friend(webid):
	""" Called when a remote webid wants access
	    Added to the list of pending_friends, if not already a friend
	"""
	friends = jongau.settings.friends
	pending_friends = jongau.settings.pending_friends
	if webid in friends:
		if webid in pending_friends:
			while webid in pending_friends:
				pending_friends.delete(webid)
			jongau.settings.pending_friends = pending_friends
		return
	if webid in pending_friends:
		return
	pending_friends.append(webid)
	jongau.settings.pending_friends = pending_friends


def request_follow(webid, ident):
	""" Requests that the given ident wants to access the server controlled by webid
	    Adds the webid to the pending_following
	    Also checks if we have access, and moves it directly to following if we do
	"""
	has_access = check_follow(webid, ident)
	if not has_access:
		server_root = jongau.webid.get_server_root(webid)
		request_url = urlparse.urljoin(server_root, 'cpecru')
		resp = requests.post(request_url, cert=ident)
		pending_following = jongau.settings.pending_following
		pending_following.append(webid)
		jongau.settings.pending_following = pending_following


def check_follow(webid, ident):
	server_root = jongau.webid.get_server_root(webid)
	request_url = urlparse.urljoin(server_root, 'xukahecru')
	resp = requests.post(request_url, cert=ident)
	logging.debug('Checking following access at %s, received status %s'%(request_url, resp.status_code))
	if resp.status_code == 200:
		has_access = True
	else:
		has_access = False

	following = jongau.settings.following
	pending_following = jongau.settings.pending_following
	logging.debug('Received access %s, updating following list %s and pending_following list %s'%(has_access, following, pending_following))
	if has_access:
		if webid not in following:
			following.append(webid)
			jongau.settings.following = following
		if webid in pending_following:
			while webid in pending_following:
				pending_following.remove(webid)
			jongau.settings.pending_following = pending_following
	else:
		if webid in following:
			while webid in following:
				following.remove(webid)
			jongau.settings.following = following
	logging.debug('Lists have been updated: following list %s and pending_following list %s'%(jongau.settings.following, jongau.settings.pending_following))
	return has_access

@app.route('/crunoi')
def follow_callback():
	""" Called by remote followed server when an update to friendship status happens """
	if hasattr(g, 'webid'):
		ident = jongau.identity.get_client_cert()
		check_follow(g.webid, ident)
		return 'Acknowledged', 200
	else:
		return 'Invalid WebID', 401

@app.route('/cpecru')
def request_friend():
	""" Called by a client when they want to follow us """
	if hasattr(g, 'webid'):
		requested_friend(g.webid)
		return 'Requested', 200
	else:
		return 'Invalid WebID', 401

@app.route('/xukahecru')
def check_friendship():
	if hasattr(g, 'webid') and is_friend(g.webid):
		return 'Is friend', 200
	elif hasattr(g, 'webid'):
		return 'Is not friend', 403
	else:
		return 'Invalid WebID', 401
