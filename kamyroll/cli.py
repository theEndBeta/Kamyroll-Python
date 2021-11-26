#!/user/bin/env python

import argparse
import sys
import logging
import os
from typing import Optional

import kamyroll.api as api
import kamyroll.downloader as downloader
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf


def run():
    config_file_default: str = os.path.join(os.getcwd(), 'config', 'kamyroll.json')

    parser = argparse.ArgumentParser()
    parser.add_argument('--authenticate', '-a',   action='store_true',    help='Authenticate with configured ID')
    parser.add_argument('--verbose',      '-v',   action='count', default=0, help='Increase verbosity')
    parser.add_argument('--quiet',        '-q',   action='count', default=0, help='Decrease verbosity')


    parser.add_argument('--login',    '-l',   type=str,     help='Login with ID (`<username>:<password>`)')
    parser.add_argument('--search',           type=str,     help='Search a series, films, episode')
    parser.add_argument('--series',           type=str,     help='Show seasons for the given series id')
    parser.add_argument('--season',   '-s',   type=str,     help='Show episodes of a season (for given season id)')
    parser.add_argument('--episode',  '-e',   type=str,     help='Show episodes of a season (by season id)')
    parser.add_argument('--movie',    '-m',   type=str,     help='Show movies from a movie list (by movie id)')
    parser.add_argument('--url',      '-u',   type=str,     help='Show m3u8 url of episode or movie (by episode id)')
    # parser.add_argument('--playlist', '-p',   type=str,     nargs="+", help='Download episode list')
    parser.add_argument(
        '--config',
        '-c',
        nargs='?',
        type=str,
        const=config_file_default,
        default=config_file_default,
        help='Location of the config file',
    )
    parser.add_argument(
        '--download',
        '-d',
        type=str,
        nargs='?',
        const="",
        help='Download an episode or movie (by episode  or movie id) or associated episode search'
    )
    args = parser.parse_args()

    # Set dynamic loq level
    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    verbosity_index = 2 + (args.verbose - args.quiet)
    if verbosity_index >= len(log_levels):
        verbosity_index = len(log_levels) - 1
    elif verbosity_index < 0:
        verbosity_index = 0


    logging.basicConfig(level=log_levels[verbosity_index])
    log = logging.getLogger(__name__)


    cr_api = api.crunchyroll(KamyrollConf.load(args.config))
    cr_dl = None
    if args.download is not None:
        cr_dl = downloader.crunchyroll(cr_api)

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
        cr_api.searchShows(args.search)
    elif args.series:
        cr_api.getShowData(args.series)
    elif args.season:
        season_data = cr_api.getSeasonData(args.season)
        if cr_dl is not None and season_data is not None:
            cr_dl.download_all([ep.get('id', '') for ep in season_data.get('children', [])])
    elif args.episode:
        episode_data = cr_api.getEpisodeData(args.episode)
        if episode_data is not None and cr_dl is not None:
            cr_dl.download(episode_data.get('id', ''))
    elif args.movie:
        cr_api.movie(args.movie)
    elif args.download:
        if args.download == "":
            parser.error("--download/-d must have an argument if used alone")
        cr_dl = downloader.crunchyroll(cr_api)
        # if args.playlist:
        #     if len(args.playlist)
        #     cr_dl.download_season(args.download, args.playlist)
        # else:
        cr_dl.download(args.download)
    else:
        parser.print_help()


if __name__ == '__main__':
    run()
