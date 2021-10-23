#!/user/bin/env python

import argparse
import sys
import logging
import os

import kamyroll.api as api
import kamyroll.downloader as downloader
import kamyroll.utils as utils

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def run():

    parser = argparse.ArgumentParser()
    parser.add_argument('--login',        '-l',   type=str,               help='Login with ID')
    parser.add_argument('--authenticate', '-a',   action='store_true',    help='Authenticate with configured ID')
    parser.add_argument('--search',               type=str,               help='Search a series, films, episode')
    parser.add_argument('--season',       '-s',   type=str,               help='Show seasons of a series')
    parser.add_argument('--episode',      '-e',   type=str,               help='Show episodes of a season')
    parser.add_argument('--movie',        '-m',   type=str,               help='Show movies from a movie list')
    parser.add_argument('--download',     '-d',   type=str,               help='Download an episode or movie')
    parser.add_argument('--url',          '-u',   type=str,               help='Show m3u8 url of episode or movie')
    parser.add_argument('--playlist',     '-p',   type=str,               help='Download episode list')
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        default=os.path.join(os.getcwd(), 'config', 'kamyroll.json'),
        help='Location of the config file',
    )
    args = parser.parse_args()

    config = utils.get_config(args.config)

    cr_api = api.crunchyroll(config)

    if args.login:
        (username, password) = utils.get_login_form(args.login)
        cr_api.login(username, password, False)
    elif args.authenticate:
        username = config.get('configuration').get('account').get('email')
        password = config.get('configuration').get('account').get('password')
        if username is None or password is None:
            log.error('No login is configured.')
            sys.exit(0)
        cr_api.login(username, password, False)
    elif args.search:
        cr_api.search(args.search)
    elif args.season:
        cr_api.season(args.season)
    elif args.episode:
        cr_api.episode(args.episode)
    elif args.movie:
        cr_api.movie(args.movie)
    elif args.download:
        cr_dl = downloader.crunchyroll(config)
        if args.playlist:
            cr_dl.download_season(args.download, args.playlist)
        else:
            cr_dl.download(args.download)
    elif args.url:
        cr_dl = downloader.crunchyroll(config)
        cr_dl.url(args.url)
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
