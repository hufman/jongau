from flask import Flask
app = Flask('jongau')

import wsgi_webid
app.wsgi_app = wsgi_webid.WebIDMiddleware(app.wsgi_app)
