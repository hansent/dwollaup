'''
dwolla-python
=============
dwolla-python is a simple python module to use
`Dwolla's <http://www.dwolla.com>`_  REST API.

For the general API documentation and other dwolla documentation go to
http://developers.dwolla.com/
'''

import json
import urllib
import datetime
from google.appengine.api import urlfetch

class DwollaGateway(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session = []
        self.mode = 'LIVE'

    def set_mode(self, mode):
        if mode not in ['LIVE', 'TEST']:
            return False

        self.mode = mode
        return True

    def start_gateway_session(self):
        self.session = []
        return True

    def add_gateway_product(self, name, amount, desc = '', qty = 1):
        product = {}
        product['Name'] = name
        product['Description'] = desc
        product['Price'] = amount
        product['Quantity'] = qty

        self.session.append(product)
        return True

    def get_gateway_URL(self, destination_id, order_id=None,
            discount=0, shipping=0, tax=0, notes=None, callback=None,
            allow_funding_sources=0):
        # Calcualte subtotal
        subtotal = 0
        for product in self.session:
            subtotal += float(product['Price']) * float(product['Quantity'])

        # Calculate grand total
        total = subtotal - discount + shipping + tax


        # Create request body
        request = {}
        request['Key'] = self.client_id
        request['Secret'] = self.client_secret
        request['Test'] = 'true' if (self.mode == 'TEST') else 'false'
        request['AllowFundingSources'] = "true"
        request['Redirect'] = self.redirect_uri
        request['PurchaseOrder'] = {}
        request['PurchaseOrder']['DestinationId'] = destination_id
        request['PurchaseOrder']['OrderItems'] = self.session
        request['PurchaseOrder']['Discount'] = -discount
        request['PurchaseOrder']['Shipping'] = shipping
        request['PurchaseOrder']['Tax'] = tax

        request['PurchaseOrder']['Total'] = round(total, 2)

        # Append optional parameters
        if order_id:
            request['OrderId'] = order_id
        if callback:
            request['Callback'] = callback
        if notes:
            request['PurchaseOrder']['Notes'] = notes

        # Send off the request
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(request)

        #response = requests.post(, verify=True)
        response = urlfetch.fetch(url='https://www.dwolla.com/payment/request',
            method=urlfetch.POST,
            payload=data,
            headers=headers
        )
        # Parse the response
        response = json.loads(response.content)
        if response['Result'] != 'Success':
            raise DwollaAPIError(response['Message'])

        return 'https://www.dwolla.com/payment/checkout/%s' % response['CheckoutId']

    def verify_gateway_signature(self, signature, checkout_id, amount):
        import hmac
        import hashlib

        amount = float(amount)

        raw = '%s&%s' % (checkout_id, amount)
        hash = hmac.new(self.client_secret, raw, hashlib.sha1).hexdigest()

        return True if (hash == signature) else False


class DwollaAPIError(Exception):
    '''Raised if the dwolla api returns an error.'''
    pass


class DwollaClientApp(object):
    '''
    Encapsulates OAuth dance, and making requests to the dwolla api.
    '''
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://www.dwolla.com/oauth/rest/"
        self.auth_url = "https://www.dwolla.com/oauth/v2/authenticate"
        self.token_url = "https://www.dwolla.com/oauth/v2/token"

    def parse_response(self, resp):
        '''
        Helper function to parse json API response. Raises `DwollaAPIError`
        if the response indicates an error.
        '''
        resp = json.loads(resp.content)
        if resp['Success'] is False:
            err_msg = resp['Message']
            if resp['Response']:
                err_msg += ": " + json.dumps(resp['Response'])
            raise DwollaAPIError(err_msg)
        return resp['Response']

    def init_oauth_url(self, redirect_uri=None, scope="accountinfofull"):
        '''
        geneates url to initialize the Oauth dance.  redirext the user to the
        returned URL, and the Dwolla API will authenticat/authorize the request
        and redirect back to the default OAuth Callback URL you registered with
        dwolla, or to the url you pass via the `redirect_uri` parameter.

        :param redirect_uri:  URL to return the user to after they approve or
            deny the authentication request. If not provided, will default to
            registered OAuth Callback URL.

        :param scope: "|" seperated string of any auth scope you are requesting
            access to. For example "balance|contacts|transactions" to request
            access to balance, contacts, and transaction resources. Availeble
            resources inlude: `balance`, `contacts`, `transactions`,
            `request`, `send`, `accountinfofull`, `funding`.
        '''
        # dwolla api only uses response_type 'code'
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': scope
        }
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        return "%s?%s" % (self.auth_url, urllib.urlencode(params))

    def get_oauth_token(self, code, **kwargs):
        '''
        Returns a valid OAuth token given the code you got from dwolla
        when they redirected the user back to your site after you sent
        them to the url generated by :method:`init_oauth_url`.

        :param code: Verification code obtained from dwolla in response
            to user authorizing your application

        :param grant_type: (optional) set's the grant_type url parameter.
            defaults to `authorization_code`

        :param redirect_uri: (optional) URI user was redirected back to by
            dwolla. This must match the URI you specified when you generated
            the initial OAuth redirect via `init_oauth_url`
        '''
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': kwargs.get('grant_type', 'authorization_code')
        }
        if 'redirect_uri' in kwargs:
            params['redirect_uri'] = kwargs['redirect_uri']
        #resp = requests.get(, params=params, verify=True)
        _url = "%s?%s" % (self.token_url, urllib.urlencode(params))
        resp = urlfetch.fetch(_url)
        resp = json.loads(resp.content)
        try:
            return resp['access_token']
        except:
            err_msg = "<%(error)s>: %(error_description)s" % resp
            raise DwollaAPIError(err_msg)

    def api_request(self, resource, **params):
        '''
        Helper function that makes an API request, by automatically setting
        the `client_id`, and `client_secret` url parameters.
        '''
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        url = "%s/%s" % (self.api_url, resource)
        _url = "%s?%s" % (url, urllib.urlencode(params))
        return urlfetch.fetch(_url)

    def api_post(self, endpoint, data):
        url = "%s%s" % (self.api_url, endpoint)
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(data)

        return urlfetch.fetch(url, method=urlfetch.POST, payload=data, headers=headers)

    def get(self, resource, **params):
        '''
        Get an API resource via the REST api. E.g. to get a certain user::
            resource = "user/" + account_id
            user = dwolla_client.get(resource)

        :param resource: the resource to fetch.

        :param **params: optional arguments to use as url arguments, depending
            on the kind of resource being fetched (.e.g range=10, limit=10,
            etc.)
        '''
        resp = self.api_request(resource, **params)
        return self.parse_response(resp)

    def post(self, endpoint, data):
        resp = self.api_post(endpoint, data)
        return self.parse_response(resp)

    def get_account_info(self, account_id):
        '''
        Convinience function to get a certain user accounts data.  Equivalent
        to doing ```dwolla_client.get("users/%"%account_id)```

        :param account_id: Dwolla account identifier or email address
            of the Dwolla account
        '''
        return self.get("users/%s" % account_id)

    def get_nearby_spots(self, lat='41.59', lon='-93.62', range=10, limit=10):
        '''
        Convinience function to get a list of nearby dwolla spots for a given
        lat,long.

        :param lat: lattitude of location. defaults to '41.59'

        :param long: longitude of location. defaults to '-92,62'

        :param range: number of miles within which to look for spots.
            defaults to 10

        :param limit: limit the number of results. defaults to 10.
        '''
        return self.get("contacts/nearby",
            latitude=lat,
            longitude=lon,
            range=range,
            limit=limit)

    def register_user(self, email, password, pin, firstName, lastName, address, address2, city, state, zip, phone, dateOfBirth, organization=None, ein=None, type='Personal', acceptTerms='true'):
        '''
        Register a new Dwolla user account

        :param email: (required) Email address of the new user
        :param password: (required) Desired user's password
        :param pin: (required) Desired 4 digit PIN
        :param firstName: (required) User's first name
        :param lastName: (required) User's last name
        :param address: (required) Line 1 of the address
        :param address2: (optional) Line 2 of the address
        :param city: (required) City.
        :param state: (required) USA state or territory two character code.
        :param zip: (required) Postal code or zip code.
        :param phone: (required) Primary phone number of the user.
        :param dateOfBirth: (required) Date of birth of the user.
        :param organization: (optional) Company name for a commercial or non-profit account.
        :param type: (optional) Account type of the new user. Defaults to Personal. Options are Personal, Commercial, and NonProfit.
        :param acceptTerms: (optional) Did user agree to Dwolla's TOS?
        '''
        params = {}
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        params['email'] = email
        params['password'] = password
        params['firstName'] = firstName
        params['lastName'] = lastName
        params['address'] = address
        params['address2'] = address2
        params['city'] = city
        params['state'] = state
        params['zip'] = zip
        params['phone'] = phone
        params['dateOfBirth'] = dateOfBirth
        params['type'] = type
        params['pin'] = pin
        params['acceptTerms'] = acceptTerms

        if address2:
            params['address2'] = address2
        if ein:
            params['ein'] = ein
        if organization:
            params['organization'] = organization

        return self.post("register/", params)

class DwollaUser(object):
    '''
    Once you have an access token for a specfic user, you can use it
    to instatiate this class, ehich wraps usefull api resources/functions.
    '''

    def __init__(self, access_token):
        self.api_url = "https://www.dwolla.com/oauth/rest"
        self.access_token = access_token

    def parse_response(self, resp):
        resp = json.loads(resp.content)
        if resp['Success'] is False:
            raise DwollaAPIError(resp['Message'])
        return resp['Response']

    def api_get(self, endpoint, **params):
        url = "%s/%s" % (self.api_url, endpoint)
        params['oauth_token'] = self.access_token
        #return requests.get(url, params=params, verify=True)
        _url = "%s?%s" % (url, urllib.urlencode(params))
        return urlfetch.fetch(_url)

    def api_post(self, endpoint, data):
        url = "%s/%s" % (self.api_url, endpoint)
        headers = {'Content-Type': 'application/json'}
        data['oauth_token'] = self.access_token
        data = json.dumps(data)
        #return requests.post(url, data=data, headers=headers)
        return urlfetch.fetch(url, method=urlfetch.POST, payload=data, headers=headers)

    def get(self, endpoint, **params):
        resp = self.api_get(endpoint, **params)
        return self.parse_response(resp)

    def post(self, endpoint, data):
        resp = self.api_post(endpoint, data)
        return self.parse_response(resp)

    def get_account_info(self):
        '''returs the account info for this user account'''
        return self.get("users")

    def get_balance(self):
        '''returns the balance for this user account'''
        return self.get("balance")

    def get_contacts(self, search=None, types=None, limit=None):
        '''
        returns a list of contacts for this user account.

        :param search: (optional) Search term used to search the contacts.

        :param types: (optional) not sure?

        :param search: (optional) Number of contacts to retrieve.
            Defaults to 10. Can be between 1 and 200 contacts .

        '''
        params = {}
        if search:
            params['search'] = search
        if types:
            params['types'] = types
        if limit:
            params['limit'] = limit
        return self.get("contacts", **params)

    def get_transaction(self, transaction_id):
        '''
        returns a specific transaction resource

        :param transaction_id: id of the transaction to fetch.
        '''
        return self.get("transactions/%s" % int(transaction_id))

    def get_transaction_list(self, since="", types="", limit=None, skip=None):
        '''
        returns a list of contacts for this user account.

        :param since: (optional) Earliest date and time for which to retrieve
            transactions. Defaults to 7 days prior to current date and time
            in UTC. Can be string with format 'mm-dd-YYYY' or a python
            `datetime.datetime` object.

        :param types: (optional) Transaction types to retrieve.
            Must be delimited by a '|'. Options are money_sent, money_received,
            deposit, withdrawal, and fee. Defaults to include all
            transaction types.

        :param: limit: (optional) Number of transactions to retrieve.
            Defaults to 10. Can be between 1 and 200 transactions.

        :param skip: (optional) Numer of transactions to skip. Defaults to 0.
        '''
        if type(since) == datetime.datetime:
            since = since.strformat("%m-%d-%Y")
        params = {}
        if since:
            params['sinceDate'] = since
        if types:
            params['types'] = types
        if limit:
            params['limit'] = limit
        if skip:
            params['skip'] = skip
        return self.get("transactions", **params)

    def get_transaction_stats(self, types=None, start_date="", end_date=""):
        '''
        returns transaction stats for the user account.

        :param start_date: (optional) Starting date and time to for which to
            process transactions stats. Defaults to 0300 of the current day in
            UTC.  Can be string with format 'mm-dd-YYYY' or a python
            `datetime.datetime` object.

        :param end_date: (optional) Starting date and time to for which to
            process transactions stats. Defaults to 0300 of the current day in
            UTC.  Can be string with format 'mm-dd-YYYY' or a python
            `datetime.datetime` object.
        '''
        if type(start_date) == datetime.datetime:
            start_date = start_date.strformat("%m-%d-%Y")
        if type(end_date) == datetime.datetime:
            end_date = end_date.strformat("%m-%d-%Y")
        params = {}
        if types:
            params['types'] = types
        if types:
            params['startDate'] = start_date
        if types:
            params['endDate'] = end_date
        return self.get("transactions/stats", **params)

    def send_funds(self, amount, dest, pin,
            notes=None, assume_cost=None, facil_amount=None, dest_type=None, funds_source=None):
        '''
        Send funds from this user account to another one.

        :param amount: Amount of funds to transfer to the destination user.

        :param dest: Identification of the user to send funds to. Must be the
            Dwolla identifier, Facebook identifier, Twitter identifier,
            phone number, or email address.

        :param pin: User's pin number to verify transaction.

        :param notes: (optional )Note to attach to the transaction. Limited to
            250 characters.

        :param assume_cost: (optional) Set to True if the user will assume the
            Dwolla fee.  Set to false if the destination user will assume the
            Dwolla fee. Does not affect facilitator fees. Defaults to false.

        :param facil_amount: (optional) Amount of the facilitator fee to
            override. Only applicable if the facilitator fee feature is
            enabled. If set to 0, facilitator fee is disabled for transaction.
            Cannot exceed 25% of the 'amount'.

        :param dest_type: (optional) Type of destination user.
            Defaults to "Dwolla". Can be "Dwolla", "Facebook", "Twitter",
            "Email", or "Phone".

        :param funds_source: (optional) The Dwolla ID of the funding
           source to be used. Defaults to the user's Dwolla balance.
        '''
        params = {'pin': pin, 'destinationId': dest, 'amount': amount}
        if notes:
            params['notes'] = notes
        if assume_cost:
            params['assume_cost'] = assume_cost
        if facil_amount:
            params['facilitatorAmount'] = facil_amount
        if dest_type:
            params['destinationType'] = dest_type
        if funds_source:
            params['fundsSource'] = funds_source

        return self.post('transactions/send', params)

    def request_funds(self, amount, source, pin,
            notes=None, facil_amount=None, source_type=None):
        '''
        Request funds from another dwolla user on behalf of the user.

        :param amount: Amount of funds to transfer to the user.

        :param source: Identification of the user to request funds from.
            Must be the Dwolla identifier, Facebook identifier, Twitter
            identifier, phone number, or email address.

        :param pin: User's pin number to verify transaction.

        :param notes: (optional )Note to attach to the transaction. Limited to
            250 characters.

        :param facil_amount: (optional) Amount of the facilitator fee to
            override. Only applicable if the facilitator fee feature is
            enabled. If set to 0, facilitator fee is disabled for transaction.
            Cannot exceed 25% of the 'amount'.

        :param source_type: (optional) Type of destination user.
            Defaults to "Dwolla". Can be "Dwolla", "Facebook", "Twitter",
            "Email", or "Phone".

        '''
        params = {'pin': pin, 'sourceId': source, 'amount': amount}
        if notes:
            params['notes'] = notes
        if facil_amount:
            params['facilitatorAmount'] = facil_amount
        if source_type:
            params['sourceType'] = source_type
        return self.post('transactions/request', params)

    def get_funding_sources(self):
        ''' Returns a list of verified funding sources for the user '''
        return self.get('fundingsources')

    def get_funding_source(self, source_id):
        '''
        Returns the data for a specific funding source given its ID.

        :param source_id: Funding source identifier of the funding source
            being requested.
        '''
        return self.get("fundingsources/%s" % source_id)
