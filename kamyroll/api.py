import logging
import sys
import requests
import kamyroll.extractor as extractor
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf
from typing import Optional

log = logging.getLogger(__name__)

class crunchyroll:

    def __init__(self, config: KamyrollConf):
        self.config = config
        self.session = utils.get_session(self.config)
        self.session.headers = utils.get_headers(self.config, with_auth=True)

    def login(self, username: str, password: str):
        data = {
            "username": username,
            "password": password,
        }
        log.debug({**data, password: ""})

        response_json = self.session.post('https://prod-api-funimationnow.dadcdigital.com/api/auth/login/', data=data).json()
        if utils.check_error(response_json):
            sys.exit(0)

        self.config.set_conf(response_json.get('token'), 'token', 'access_token')
        self.config.set_conf(response_json.get('user', {}).get('id'), 'account', 'account_id')
        self.config.set_conf(response_json.get('user_region'), 'user_region')
        self.config.save()

        self.session.headers = utils.get_headers(self.config, with_auth=True)
        sys.exit(0)

    def searchShows(self, query):

        params = {
            'q': str(query),
            'limit': '20',
            'region': self.config.config('user_region'),
            'offset': 0,
            'lang': 'en-US',
            'index': 'search-shows',
        }

        r = self.session.get('https://search.prd.funimationsvc.com/v1/search', params=params).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        extractor.outputSearchShowsResults(r)
        sys.exit(0)


    def getShowData(self, show_id: str) -> Optional[dict]:

        r = self.session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/title/{}'.format(show_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        shows = r.get('items', [])
        if len(shows) == 0:
            print("No shows found")
            return None

        extractor.outputShow(shows[0], with_children=True)
        return shows[0]


    def getSeasonData(self, season_id: str) -> Optional[dict]:

        r = self.session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/season/{}'.format(season_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        seasons = r.get('items', [])
        if len(seasons) == 0:
            print("No shows found")
            return

        extractor.outputSeason(seasons[0], with_children=True)
        return seasons[0]


    def getEpisodeData(self, episode_id: str) -> Optional[dict]:

        r = self.session.get('https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/episode/{}'.format(episode_id)).json()
        log.debug(r)
        if utils.check_error(r):
            sys.exit(0)

        episodes = r.get('items', [])
        if len(episodes) == 0:
            print("No episodes found for id {}".format(episode_id))
            return None

        extractor.outputEpisode(episodes[0])

        return episodes[0]


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
