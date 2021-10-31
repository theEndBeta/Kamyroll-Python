#!/user/bin/env python

import argparse
import sys
import logging
import os

import kamyroll.api as api
import kamyroll.downloader as downloader
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def run():
    config_file_default: str = os.path.join(os.getcwd(), 'config', 'kamyroll.json')

    parser = argparse.ArgumentParser()
    parser.add_argument('--authenticate', '-a',   action='store_true',    help='Authenticate with configured ID')
    parser.add_argument('--login',    '-l',   type=str,     help='Login with ID (`<username>:<password>`)')
    parser.add_argument('--search',           type=str,     help='Search a series, films, episode')
    parser.add_argument('--season',   '-s',   type=str,     help='Show seasons of a series (by series id)')
    parser.add_argument('--episode',  '-e',   type=str,     help='Show episodes of a season (by season id)')
    parser.add_argument('--movie',    '-m',   type=str,     help='Show movies from a movie list (by movie id)')
    parser.add_argument('--download', '-d',   type=str,     help='Download an episode or movie (by episode  or movie id)')
    parser.add_argument('--url',      '-u',   type=str,     help='Show m3u8 url of episode or movie (by episode id)')
    parser.add_argument('--playlist', '-p',   type=str,     nargs="+", help='Download episode list')
    parser.add_argument(
        '--config',
        '-c',
        nargs='?',
        type=str,
        const=config_file_default,
        default=config_file_default,
        help='Location of the config file',
    )
    args = parser.parse_args()

    cr_api = api.crunchyroll(KamyrollConf.load(args.config))

    if args.login:
        (username, password) = utils.get_login_form(args.login)
        cr_api.login(username, password)
    elif args.authenticate:
        username = str(cr_api.config.config('account', 'email'))
        password = str(cr_api.config.config('account', 'password'))
        if username is None or password is None:
            log.error('No login is configured.')
            sys.exit(0)
        cr_api.login(username, password)
    elif args.search:
        cr_api.search(args.search)
    elif args.season:
        cr_api.season(args.season)
    elif args.episode:
        cr_api.episode(args.episode)
    elif args.movie:
        cr_api.movie(args.movie)
    elif args.download:
        cr_dl = downloader.crunchyroll(cr_api.config)
        if args.playlist:
            cr_dl.download_season(args.download, args.playlist)
        else:
            cr_dl.download(args.download)
    elif args.url:
        cr_dl = downloader.crunchyroll(cr_api.config)
        cr_dl.url(args.url)
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
