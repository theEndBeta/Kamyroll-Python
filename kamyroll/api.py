import logging
import sys
import requests
import kamyroll.extractor as extractor
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf

log = logging.getLogger(__name__)

class crunchyroll:

    def __init__(self, config: KamyrollConf):
        self.config = config

    def login(self, username: str, password: str):
        session = utils.get_session(self.config)

        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": "offline_access"
        }
        log.debug({**data, password: ""})

        session.headers.update(utils.get_authorization(self.config, False))
        response_json = session.post('https://beta-api.crunchyroll.com/auth/v1/token', data=data).json()
        if utils.check_error(response_json):
            sys.exit(0)

        access_token = response_json.get('access_token')
        refresh_token = response_json.get('refresh_token')
        token_type = response_json.get('token_type')
        authorization = {'Authorization': '{} {}'.format(token_type, access_token)}
        account_id = response_json.get('account_id')

        headers = utils.get_headers(self.config)
        headers.update(authorization)
        session.headers = headers

        response_json = session.get('https://beta-api.crunchyroll.com/accounts/v1/me').json()
        if utils.check_error(response_json):
            sys.exit(0)

        external_id = response_json.get('external_id')

        response_json = session.get('https://beta-api.crunchyroll.com/accounts/v1/me/profile').json()
        if utils.check_error(response_json):
            sys.exit(0)

        email = response_json.get('email')
        username = response_json.get('username')

        response_json = session.get('https://beta-api.crunchyroll.com/index/v2').json()
        if utils.check_error(response_json):
            sys.exit(0)

        cms = response_json.get('cms')
        bucket = cms.get('bucket')
        policy = cms.get('policy')
        signature = cms.get('signature')
        key_pair_id = cms.get('key_pair_id')
        expires = cms.get('expires')

        self.config.set_conf(refresh_token, 'token', 'refresh_token')
        self.config.set_conf(bucket, 'token', 'bucket')
        self.config.set_conf(policy, 'token', 'policy')
        self.config.set_conf(signature, 'token', 'signature')
        self.config.set_conf(key_pair_id, 'token', 'key_pair_id')
        self.config.set_conf(expires, 'token', 'expires')

        self.config.set_conf(account_id, 'account', 'account_id')
        self.config.set_conf(external_id, 'account', 'external_id')
        self.config.set_conf(email, 'account', 'email')
        self.config.set_conf(password, 'account', 'password')
        self.config.set_conf(username, 'account', 'username')

        log.info('Connected account: [%s]', email)

        self.config.save()
        sys.exit(0)

    def search(self, query):
        authorization = utils.get_authorization(self.config, True)
        self.config = KamyrollConf.load(self.config._path)
        headers = utils.get_headers(self.config)
        headers.update(authorization)

        session = utils.get_session(self.config)
        session.headers = headers

        params = {
            'q': str(query),
            'n': '6',
            'locale': utils.get_locale(self.config)
        }

        r = session.get('https://beta-api.crunchyroll.com/content/v1/search', params=params).json()
        if utils.check_error(r):
            sys.exit(0)

        items = r.get('items')
        for item in items:
            extractor.search(item, self.config)
        sys.exit(0)

    def season(self, series_id):
        (policy, signature, key_pair_id) = utils.get_token(self.config)
        self.config = KamyrollConf.load(self.config._path)

        params = {
            'series_id': series_id,
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }
        log.debug("Season search params: %s", params)

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/seasons'.format(self.config.config('token', 'bucket'))
        r = requests.get(endpoint, params=params).json()

        if utils.check_error(r):
            sys.exit(0)

        extractor.season(r, series_id)
        sys.exit(0)

    def episode(self, season_id):
        (policy, signature, key_pair_id) = utils.get_token(self.config)
        self.config = KamyrollConf.load(self.config._path)

        params = {
            'season_id': season_id,
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/episodes'.format(self.config.config('token', 'bucket'))
        r = requests.get(endpoint, params=params).json()
        if utils.check_error(r):
            sys.exit(0)

        extractor.episode(r, season_id, self.config)
        sys.exit(0)

    def movie(self, movie_id):
        (policy, signature, key_pair_id) = utils.get_token(self.config)
        self.config = KamyrollConf.load(self.config._path)

        params = {
            'movie_listing_id': movie_id,
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/movies'.format(self.config.config('token', 'bucket'))
        r = requests.get(endpoint, params=params).json()

        if utils.check_error(r):
            sys.exit(0)

        extractor.movie(r, movie_id, self.config)
