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
        }
        log.debug({**data, password: ""})

        session.headers.update({
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.30 Safari/537.36',
            'origin': 'https://www.funimation.com',
            'referer': 'https://www.funimation.com/',
            'accept-encoding': 'gzip, deflate, br',
            'accept': 'application/json, text/javascript, */*; q=0.01',
        })
        response_json = session.post('https://prod-api-funimationnow.dadcdigital.com/api/auth/login/', data=data).json()
        # log.info(response_json)
        # sys.exit(0)
        if utils.check_error(response_json):
            sys.exit(0)

        access_token = response_json.get('token')
        self.config.set_conf(response_json.get('token'), 'token', 'access_token')
        self.config.set_conf(response_json.get('user', {}).get('id'), 'account', 'account_id')
        self.config.set_conf(response_json.get('user_region'), 'user_region')
        # self.config.set_conf('premium' in response_json.get('rlildup_cookie', ''), 'account', 'account_id')
        self.config.save()

        authorization = {'Authorization': '{} {}'.format('Token', access_token)}
        is_premium = "premium" in response_json.get('rlildup_cookie', "")

        headers = utils.get_headers(self.config)
        headers.update(authorization)
        session.headers = headers

        # response_json = session.get('https://beta-api.crunchyroll.com/accounts/v1/me').json()
        # if utils.check_error(response_json):
        #     sys.exit(0)

        # external_id = response_json.get('external_id')

        # response_json = session.get('https://beta-api.crunchyroll.com/accounts/v1/me/profile').json()
        # if utils.check_error(response_json):
        #     sys.exit(0)

        # email = response_json.get('email')
        # username = response_json.get('username')

        # response_json = session.get('https://beta-api.crunchyroll.com/index/v2').json()
        # if utils.check_error(response_json):
        #     sys.exit(0)

        # cms = response_json.get('cms')
        # bucket = cms.get('bucket')
        # policy = cms.get('policy')
        # signature = cms.get('signature')
        # key_pair_id = cms.get('key_pair_id')
        # expires = cms.get('expires')

        # self.config.set_conf(refresh_token, 'token', 'refresh_token')
        # self.config.set_conf(bucket, 'token', 'bucket')
        # self.config.set_conf(policy, 'token', 'policy')
        # self.config.set_conf(signature, 'token', 'signature')
        # self.config.set_conf(key_pair_id, 'token', 'key_pair_id')
        # self.config.set_conf(expires, 'token', 'expires')

        # self.config.set_conf(account_id, 'account', 'account_id')
        # self.config.set_conf(external_id, 'account', 'external_id')
        # self.config.set_conf(email, 'account', 'email')
        # self.config.set_conf(password, 'account', 'password')
        # self.config.set_conf(username, 'account', 'username')

        # log.info('Connected account: [%s]', email)

        # self.config.save()
        sys.exit(0)

    def search(self, query):
        headers = utils.get_headers(self.config, with_auth=True)

        session = utils.get_session(self.config)
        session.headers = headers

        params = {
            'q': str(query),
            'limit': '20',
            'region': self.config.config('user_region'),
            'offset': 0,
            'lang': 'en-US',
            'index': 'search-shows',
        }

        r = session.get('https://search.prd.funimationsvc.com/v1/search', params=params).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        extractor.search(r, self.config)
        sys.exit(0)


    def series(self, series_id: str):
        headers = utils.get_headers(self.config, with_auth=True)

        session = utils.get_session(self.config)
        session.headers = headers

        r = session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/title/{}'.format(series_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        series = r.get('items', [])
        if len(series) == 0:
            print("No series found")
            return

        extractor.outputSeasonList(series[0].get('children', []))


    def season(self, season_id: str) -> None:
        headers = utils.get_headers(self.config, with_auth=True)

        session = utils.get_session(self.config)
        session.headers = headers

        r = session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/season/{}'.format(season_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        seasons = r.get('items', [])
        if len(seasons) == 0:
            print("No series found")
            return

        extractor.outputEpisodeList(seasons[0].get('children', []))


    def episode(self, episode_id: str)-> None:
        headers = utils.get_headers(self.config, with_auth=True)

        session = utils.get_session(self.config)
        session.headers = headers

        r = session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/episode/{}'.format(episode_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        episodes = r.get('items', [])
        if len(episodes) == 0:
            print("No series found")
            return

        extractor.outputEpisodeList(episodes[0].get('children', []))


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
