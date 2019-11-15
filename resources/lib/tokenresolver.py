# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' This module contains all functionality for VRT NU API authentication. '''

from __future__ import absolute_import, division, unicode_literals
from statichelper import from_unicode
from kodiutils import (delete, exists, get_proxies, get_setting, get_tokens_path,
                       get_userdata_path, has_credentials, invalidate_caches, listdir, localize, log,
                       log_error, mkdir, notification, ok_dialog, open_file, open_settings,
                       set_setting)

try:  # Python 3
    import http.cookiejar as cookielib
    from urllib.parse import urlencode, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, urlopen, Request
except ImportError:  # Python 2
    from urllib import urlencode
    from urllib2 import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, unquote, urlopen, Request
    import cookielib


class NoRedirection(HTTPErrorProcessor):
    ''' Prevent urllib from following http redirects '''

    def http_response(self, request, response):
        return response

    https_response = http_response


class TokenResolver:
    ''' Get, refresh and cache tokens for VRT NU API authentication. '''

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _VRT_LOGIN_URL = 'https://login.vrt.be/perform_login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'
    _USER_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/'
    _ROAMING_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'

    def __init__(self):
        ''' Initialize Token Resolver class '''
        self._proxies = get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

    def get_playertoken(self, token_url, token_variant=None, roaming=False):
        ''' Get cached or new playertoken, variants: live or ondemand '''
        token = None
        xvrttoken_variant = None
        if roaming:
            xvrttoken_variant = 'roaming'
            # Delete cached playertoken
            path = self._get_token_path('vrtPlayerToken', token_variant)
            delete(path)
        else:
            token = self._get_cached_token('vrtPlayerToken', token_variant)

        if token is None:
            if token_variant == 'ondemand' or roaming:
                xvrttoken = self.get_xvrttoken(token_variant=xvrttoken_variant)
                if xvrttoken is None:
                    return token
                cookie_value = 'X-VRT-Token=' + xvrttoken
                headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            else:
                headers = {'Content-Type': 'application/json'}
            token = self._get_new_playertoken(token_url, headers, token_variant)

        return token

    def get_xvrttoken(self, token_variant=None):
        ''' Get cached, fresh or new X-VRT-Token, variants: None, user or roaming '''
        token = self._get_cached_token('X-VRT-Token', token_variant)
        if token is None:
            # Try to refresh if we have a cached refresh token (vrtlogin-rt)
            refresh_token = self._get_cached_token('vrtlogin-rt')
            if refresh_token and token_variant != 'roaming':
                token = self._get_fresh_token(refresh_token, 'X-VRT-Token', token_variant=token_variant)
            elif token_variant == 'user':
                token = self._get_new_user_xvrttoken()
            else:
                # Login
                token = self.login(token_variant=token_variant)
        return token

    @staticmethod
    def _get_token_path(token_name, token_variant):
        ''' Create token path following predefined file naming rules '''
        prefix = token_variant + '_' if token_variant else ''
        token_path = get_tokens_path() + prefix + token_name.replace('-', '') + '.tkn'
        return token_path

    def _get_cached_token(self, token_name, token_variant=None):
        ''' Return a cached token '''
        from json import load
        cached_token = None
        path = self._get_token_path(token_name, token_variant)

        if exists(path):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            with open_file(path) as fdesc:
                token = load(fdesc)
            now = datetime.now(dateutil.tz.tzlocal())
            exp = dateutil.parser.parse(token.get('expirationDate'))
            if exp > now:
                log(3, "Got cached token '{path}'", path=path)
                cached_token = token.get(token_name)
            else:
                log(2, "Cached token '{path}' deleted", path=path)
                delete(path)
        return cached_token

    def _set_cached_token(self, token, token_variant=None):
        ''' Save token to cache'''
        from json import dump
        token_name = list(token.keys())[0]
        path = self._get_token_path(token_name, token_variant)

        if not exists(get_tokens_path()):
            mkdir(get_tokens_path())

        with open_file(path, 'w') as fdesc:
            dump(token, fdesc)

    def _get_new_playertoken(self, token_url, headers, token_variant=None):
        ''' Get new playertoken from VRT Token API '''
        from json import load
        log(2, 'URL post: {url}', url=unquote(token_url))
        req = Request(token_url, data=b'', headers=headers)
        playertoken = load(urlopen(req))
        if playertoken is not None:
            self._set_cached_token(playertoken, token_variant)
        return playertoken.get('vrtPlayerToken')

    def login(self, refresh=False, token_variant=None):
        ''' Kodi GUI login flow '''
        # If no credentials, ask user for credentials
        if not has_credentials():
            if refresh:
                return open_settings()
            open_settings()
            if not self._credentials_changed():
                return None

        # Check credentials
        login_json = self._get_login_json()

        # Bad credentials
        while login_json.get('errorCode') != 0:
            # Show localized login error messages in Kodi GUI
            message = login_json.get('errorDetails')
            log_error('Login failed: {msg}', msg=message)
            if message == 'invalid loginID or password':
                message = localize(30953)  # Invalid login!
            elif message == 'loginID must be provided':
                message = localize(30955)  # Please fill in username
            elif message == 'Missing required parameter: password':
                message = localize(30956)  # Please fill in password
            ok_dialog(heading=localize(30951), message=message)  # Login failed!
            if refresh:
                return open_settings()
            open_settings()
            if not self._credentials_changed():
                return None
            login_json = self._get_login_json()

        # Get token
        token = self._get_new_xvrttoken(login_json, token_variant)
        return token

    def _get_login_json(self):
        ''' Get login json '''
        from json import load
        payload = dict(
            loginID=from_unicode(get_setting('username')),
            password=from_unicode(get_setting('password')),
            sessionExpiration='-1',
            APIKey=self._API_KEY,
            targetEnv='jssdk',
        )
        data = urlencode(payload).encode()
        log(2, 'URL post: {url}', url=unquote(self._LOGIN_URL))
        req = Request(self._LOGIN_URL, data=data)
        login_json = load(urlopen(req))
        return login_json

    def _get_new_xvrttoken(self, login_json, token_variant=None):
        ''' Get new X-VRT-Token from VRT NU website '''
        token = None
        login_token = login_json.get('sessionInfo', dict()).get('login_token')
        if login_token:
            from json import dumps
            login_cookie = 'glt_%s=%s' % (self._API_KEY, login_token)
            payload = dict(
                uid=login_json.get('UID'),
                uidsig=login_json.get('UIDSignature'),
                ts=login_json.get('signatureTimestamp'),
                email=from_unicode(get_setting('username')),
            )
            data = dumps(payload).encode()
            headers = {'Content-Type': 'application/json', 'Cookie': login_cookie}
            log(2, 'URL post: {url}', url=unquote(self._TOKEN_GATEWAY_URL))
            req = Request(self._TOKEN_GATEWAY_URL, data=data, headers=headers)
            try:  # Python 3
                setcookie_header = urlopen(req).info().get('Set-Cookie')
            except AttributeError:  # Python 2
                setcookie_header = urlopen(req).info().getheader('Set-Cookie')
            xvrttoken = TokenResolver._create_token_dictionary(setcookie_header)
            if token_variant == 'roaming':
                xvrttoken = self._get_roaming_xvrttoken(xvrttoken)
            if xvrttoken is not None:
                token = xvrttoken.get('X-VRT-Token')
                self._set_cached_token(xvrttoken, token_variant)
                notification(message=localize(30952))  # Login succeeded.
        return token

    def _get_new_user_xvrttoken(self):
        ''' Get new 'user' X-VRT-Token from VRT NU website '''
        token = None

        # Get login json
        login_json = self._get_login_json()

        if login_json.get('errorCode') != 0:
            return None

        payload = dict(
            UID=login_json.get('UID'),
            UIDSignature=login_json.get('UIDSignature'),
            signatureTimestamp=login_json.get('signatureTimestamp'),
            client_id='vrtnu-site',
            submit='submit',
        )
        data = urlencode(payload).encode()
        cookiejar = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookiejar), ProxyHandler(self._proxies))
        log(2, 'URL get: {url}', url=unquote(self._USER_TOKEN_GATEWAY_URL))
        opener.open(self._USER_TOKEN_GATEWAY_URL)
        log(2, 'URL post: {url}', url=unquote(self._VRT_LOGIN_URL))
        opener.open(self._VRT_LOGIN_URL, data=data)
        xvrttoken = TokenResolver._create_token_dictionary(cookiejar)
        refreshtoken = TokenResolver._create_token_dictionary(cookiejar, cookie_name='vrtlogin-rt')
        if xvrttoken is not None:
            token = xvrttoken.get('X-VRT-Token')
            self._set_cached_token(xvrttoken, token_variant='user')
        if refreshtoken is not None:
            self._set_cached_token(refreshtoken)
        return token

    def _get_fresh_token(self, refresh_token, token_name, token_variant=None):
        ''' Refresh an expired X-VRT-Token, vrtlogin-at or vrtlogin-rt token '''
        token = None
        refresh_url = self._TOKEN_GATEWAY_URL + '/refreshtoken'
        cookie_value = 'vrtlogin-rt=' + refresh_token
        headers = {'Cookie': cookie_value}
        cookiejar = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookiejar), ProxyHandler(self._proxies))
        log(2, 'URL get: {url}', url=refresh_url)
        req = Request(refresh_url, headers=headers)
        opener.open(req)
        token = TokenResolver._create_token_dictionary(cookiejar, token_name)
        if token is not None:
            self._set_cached_token(token, token_variant)
            token = list(token.values())[0]
        return token

    def _get_roaming_xvrttoken(self, xvrttoken):
        ''' Get new 'roaming' X-VRT-Token from VRT NU website '''
        roaming_xvrttoken = None
        cookie_value = 'X-VRT-Token=' + xvrttoken.get('X-VRT-Token')
        headers = {'Cookie': cookie_value}
        opener = build_opener(NoRedirection, ProxyHandler(self._proxies))
        log(2, 'URL get: {url}', url=unquote(self._ROAMING_TOKEN_GATEWAY_URL))
        req = Request(self._ROAMING_TOKEN_GATEWAY_URL, headers=headers)
        req_info = opener.open(req).info()
        try:  # Python 3
            cookie_value += '; state=' + req_info.get('Set-Cookie').split('state=')[1].split('; ')[0]
            url = req_info.get('Location')
        except AttributeError:  # Python 2
            cookie_value += '; state=' + req_info.getheader('Set-Cookie').split('state=')[1].split('; ')[0]
            url = req_info.getheader('Location')
        log(2, 'URL get: {url}', url=unquote(url))
        try:  # Python 3
            url = opener.open(url).info().get('Location')
        except AttributeError:  # Python 2
            url = opener.open(url).info().getheader('Location')
        headers = {'Cookie': cookie_value}
        if url is not None:
            log(2, 'URL get: {url}', url=unquote(url))
            req = Request(url, headers=headers)
            try:  # Python 3
                setcookie_header = opener.open(req).info().get('Set-Cookie')
            except AttributeError:  # Python 2
                setcookie_header = opener.open(req).info().getheader('Set-Cookie')
            roaming_xvrttoken = TokenResolver._create_token_dictionary(setcookie_header)
        return roaming_xvrttoken

    @staticmethod
    def _create_token_dictionary(cookie_data, cookie_name='X-VRT-Token'):
        ''' Create a dictionary with token name and token expirationDate from a Python cookielib.CookieJar or urllib2 Set-Cookie http header '''
        token_dictionary = None
        if isinstance(cookie_data, cookielib.CookieJar):
            # Get token dict from cookiejar
            token_cookie = next((cookie for cookie in cookie_data if cookie.name == cookie_name), None)
            if token_cookie:
                from datetime import datetime
                token_dictionary = {
                    token_cookie.name: token_cookie.value,
                    'expirationDate': datetime.utcfromtimestamp(token_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }
        elif cookie_name in cookie_data:
            # Get token dict from http header
            import dateutil.parser
            cookie_data = cookie_data.split('X-VRT-Token=')[1].split('; ')
            token_dictionary = {
                cookie_name: cookie_data[0],
                'expirationDate': dateutil.parser.parse(cookie_data[2].strip('Expires=')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
        return token_dictionary

    @staticmethod
    def delete_tokens():
        ''' Delete all cached tokens '''
        # Remove old tokens
        # FIXME: Deprecate and simplify this part in a future version
        dirs, files = listdir(get_userdata_path())  # pylint: disable=unused-variable
        token_files = [item for item in files if item.endswith('.tkn')]
        # Empty userdata/tokens/ directory
        if exists(get_tokens_path()):
            dirs, files = listdir(get_tokens_path())  # pylint: disable=unused-variable
            token_files += ['tokens/' + item for item in files]
        if token_files:
            for item in token_files:
                delete(get_userdata_path() + item)
            notification(message=localize(30985))

    def refresh_login(self):
        ''' Refresh login if necessary '''

        if self._credentials_changed() and has_credentials():
            log(2, 'Credentials have changed, cleaning up userdata')
            self.cleanup_userdata()

            # Refresh login
            log(2, 'Refresh login')
            self.login(refresh=True)

    def cleanup_userdata(self):
        ''' Cleanup userdata '''

        # Delete token cache
        self.delete_tokens()

        # Delete user-related caches
        invalidate_caches('continue-*.json', 'favorites.json', 'my-offline-*.json', 'my-recent-*.json', 'resume_points.json', 'watchlater-*.json')

    def logged_in(self):
        ''' Whether there is an active login '''
        return bool(self._get_cached_token('X-VRT-Token'))

    @staticmethod
    def _credentials_changed():
        ''' Check if credentials have changed '''
        old_hash = get_setting('credentials_hash')
        username = get_setting('username')
        password = get_setting('password')
        new_hash = ''
        if username or password:
            from hashlib import md5
            new_hash = md5((username + password).encode('utf-8')).hexdigest()
        if new_hash != old_hash:
            set_setting('credentials_hash', new_hash)
            return True
        return False
