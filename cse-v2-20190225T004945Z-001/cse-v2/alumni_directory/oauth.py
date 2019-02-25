#code-reference: https://blog.miguelgrinberg.com/post/oauth-authentication-with-flask
import json
# import simplejson as json
from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session, abort


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        # note: config['OAUTH_CREDENTIALS'] maps to a dict
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def validate_oauth2callback(self):
        if 'code' not in request.args: #dump request if problem
            abort(500, 'oauth2 callback: code not in request.args: \n' + str(request.__dict__))
        if request.args.get('state') != session.get('state'):
            abort(500, 'oauth2 callback: state does not match: \n' + str(request.__dict__))

    def get_callback_url(self, email_token):
        # return(url_for('AlumniDirectoryApp:oauth_callback', provider=self.provider_name, _external=True, _scheme='https'))
        #return(url_for('AlumniDirectoryApp:oauth_callback', provider=self.provider_name, email_token=email_token, _external=True))
        return(url_for('AlumniDirectoryApp:oauth_callback', provider=self.provider_name, _external=True))

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class FacebookSignIn(OAuthSignIn):
    # print("I am here.")
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )
        self.email_token = None

    def authorize(self, email_token):
        self.email_token = email_token
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url(email_token))
        )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={
                'code': request.args['code'],
                'grant_type': 'authorization_code',
                'redirect_uri': self.get_callback_url(self.email_token)
            },
            decoder=decode_json
        )
        me = oauth_session.get('me?fields=id,email').json()
        print("ME: ", me.get('email'))
        if not me.get('email') is None:
            username = me.get('email').split('@')[0]
        else:
            username = None
        return (
            'facebook$' + me['id'],
            username,
            me.get('email')
        )


# import simplejson as json
class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        self.service = OAuth2Service(
            name='google',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            access_token_url='https://accounts.google.com/o/oauth2/token',
            base_url = 'https://www.googleapis.com/oauth2/v3/userinfo'      # base_url='https://www.googleapis.com/plus/v1/people/'
        )
        self.email_token = None

    def authorize(self, email_token):
        self.email_token = email_token
        return redirect(self.service.get_authorize_url(
            scope ='email',     ## scope='https://www.googleapis.com/auth/userinfo.email',
            response_type='code',
            redirect_uri=self.get_callback_url(email_token))
        )
    

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={
                'code': request.args['code'],
                'grant_type': 'authorization_code',
                'redirect_uri': self.get_callback_url(self.email_token)
            },
            decoder=decode_json
        )
        # me = oauth_session.get('me?fields=id,emails').json()
        me = oauth_session.get('').json()
        social_id = me.get('sub')
        # check if stack_overflow for different version if doesn't work
        if not me.get('email') is None:
            username = me.get('email').split('@')[0]
        else:
            print("me: {0}".format(me))
            username = None
        return (
            'google$' + social_id,
            username,
            me.get('email')
        )


class LinkedInSignIn(OAuthSignIn):
    def __init__(self):
        super(LinkedInSignIn, self).__init__('linkedin')
        self.service = OAuth2Service(
            name='linkedin',
            client_id = self.consumer_id,
            client_secret = self.consumer_secret,
            authorize_url='https://www.linkedin.com/uas/oauth2/authorization',
            access_token_url='https://www.linkedin.com/uas/oauth2/accessToken', 
            base_url='https://api.linkedin.com/v1/'
        )
        self.email_token = None

    def authorize(self, email_token):
        self.email_token = email_token
        return redirect(self.service.get_authorize_url(
            scope='r_basicprofile r_emailaddress',
            response_type='code',
            redirect_uri=self.get_callback_url(email_token))
        )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))
        
        self.validate_oauth2callback()
        #get token
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url(self.email_token)}, 
            # decoder=jsondecoder
            decoder = decode_json
        )
        me = oauth_session.get('people/~:(id,first-name,last-name,public-profile-url,email-address)?format=json&oauth2_access_token='+str(oauth_session.access_token), data={'x-li-format': 'json'}, bearer_auth=False).json()
        social_id = 'linkedin$' + me['id']
        nickname = me['firstName'] + ' ' + me['lastName']
        email = me['emailAddress']
        url = me['publicProfileUrl'] #TODO: be sure this didn't change
        return (social_id, nickname, email)