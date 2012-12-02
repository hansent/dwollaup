import dwolla
import urlparse
import json
import webapp2
from webapp2_extras import sessions
from webapp2_extras import jinja2
from google.appengine.ext import db
from webapp2 import RequestHandler, WSGIApplication


class BaseHandler(RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    def base_url(self, secure=False):
        o = urlparse.urlsplit(self.request.url)
        scheme = 'https' if secure else o.scheme
        if o.port:
            return "%s://%s:%d" % (scheme, o.netloc, o.port)
        return "%s://%s" % (scheme, o.netloc)

    def app_url(self, path="/", secure=False):
        return "%s%s" % (self.base_url(secure=secure), path)

    def render_template(self, filename, **template_args):
        self.response.write(self.jinja2.render_template(filename, **template_args))

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    @webapp2.cached_property
    def dwolla(self):
        apikey = self.app.config['DWOLLA_API_KEY']
        secret = self.app.config['DWOLLA_API_SECRET']
        return dwolla.DwollaClientApp(apikey, secret)


class UserHandler(BaseHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        if not self.session.get('user'):
            self.redirect(self.app_url('/login'))
        self.user = db.get( db.Key(session['user']) )
        try:
            RequestHandler.dispatch(self)
        finally:


class LoginHandler(BaseHandler):
    def get(self):
        permissions = self.app.config["DWOLLA_API_PERMISSIONS"]
        redirect_uri = self.app_url('/oauth_cb')
        auth_url = self.dwolla.init_oauth_url(redirect_uri, permissions)
        self.redirect(auth_url)


class DwollaOauthHandler(BaseHandler):
    def get(self):
        code = self.request.get("code")
        redirect_uri = self.app_url('/oauth_cb')
        token = self.dwolla.get_oauth_token(code, redirect_uri=redirect_uri)

        api = dwolla.DwollaUser(token)
        account = api.get_account_info()
        self.session['user'] = account
        self.session['account'] = str(account['Id'])
        self.redirect("/")


class MainHandler(BaseHandler):
    def get(self):
        item_key = self.request.get('k')
        try:
            item = db.get(db.Key(item_key))
        except:
            return self.redirect(self.app_url("/new"))

        apikey = self.app.config['DWOLLA_API_KEY']
        secret = self.app.config['DWOLLA_API_SECRET']
        gateway = dwolla.DwollaGateway(apikey, secret, self.app_url('/gateway'))
        gateway.start_gateway_session()
        gateway.add_gateway_product(item.account, item.amount, desc=item.text, qty = 1)
        try:
            url = gateway.get_gateway_URL(item.account, callback=self.app_url('/confirm'))
            self.render_template('show.html', url=url, item=item)
        except Exception as e:
            self.session['account'] = item.account
            self.session['amount'] = item.amount
            self.session['text'] = item.text
            self.redirect('/new?err='+str(e))


class LogoutHandler(BaseHandler):
    def get(self):
        if 'user' in self.session:
            del self.session['user']
        if 'account' in self.session:
            del self.session['account']
        if 'text' in self.session:
            del self.session['text']
        if 'amount' in self.session:
            del self.session['amount']
        self.redirect("/")


class NewHandler(BaseHandler):
    def get(self):
        err = self.request.get('err', None)
        account = self.session.get('account', '000-000-0000')
        self.render_template('new.html', account=account, error=err, session=self.session)

    def post(self):
        item = db.Expando()
        item.account = self.request.get('dwolla_id')
        item.text = self.request.get('text')
        try:
            amount = float(self.request.get('amount').replace("$", ""))
            item.amount = amount
            item.put()
            self.redirect('/?k=%s' % item.key())
        except:
            amount = "1.0"
            item.amount = amount
            item.put()
            self.session['account'] = item.account
            self.session['amount'] = "0"
            self.session['text'] = item.text
            self.redirect('/new?err=Invalid%20Amount.')


class ConfirmHandler(BaseHandler):
    def get(self):
        self.render_template('confirm.html')


class GatewayHandler(BaseHandler):
    def get(self):
        err = self.request.get('error')
        text = self.request.get('error_description')
        self.render_template('gateway.html', error=err, text=text)


class PaidHandler(BaseHandler):
    def get(self):
        self.render_template(self.request)


import config

app_routes = [
    ('/', MainHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/oauth_cb', DwollaOauthHandler),
    ('/new', NewHandler),
    ('/confirm', ConfirmHandler),
    ('/gateway', GatewayHandler),
]

app = webapp2.WSGIApplication(app_routes,
    config=config.dev,
    debug=True
)
