import logging
import os
import sys
from datetime import datetime
import requests
from typing import Tuple, Optional, NamedTuple
import kamyroll.utils as utils

log = logging.getLogger(__name__)

class Metadata(NamedTuple):
    metadata: list[str] = []
    cover: str = ""
    thumbnail: str = ""
    output: str = ""
    path: str = ""


def search(json_search, config):
    result_type = json_search.get('type')
    items = json_search.get('items')
    premium = utils.get_premium(config)

    list_type = list()
    list_id = list()
    list_title = list()
    list_episode = list()
    list_season = list()
    for item in items:
        item_type = item.get('type')
        if item_type == 'series':
            list_type.append(item_type)
            list_id.append(item.get('id'))
            list_title.append(item.get('title'))
            list_episode.append(item.get('series_metadata').get('episode_count'))
            list_season.append(item.get('series_metadata').get('season_count'))
        elif item_type == 'episode':
            list_type.append(item_type)
            premium_only = item.get('episode_metadata').get('is_premium_only')
            if premium_only:
                if premium:
                    id = utils.get_stream_id(item)
                else:
                    id = 'None'
            else:
                id = utils.get_stream_id(item)

            list_id.append(id)
            list_title.append(item.get('title'))
            list_episode.append(item.get('episode_metadata').get('episode'))
            list_season.append(item.get('episode_metadata').get('season_number'))
        elif item_type == 'movie_listing':
            list_type.append(item_type)
            list_id.append(item.get('id'))
            list_title.append(item.get('title'))
            list_episode.append('None')
            list_season.append('None')

    log.info('Result for: ', result_type)
    if len(list_id) == 0:
        log.warn('No media found for this category.')
    else:
        log.info('{0:<15} {1:<20} {2:<10} {3:<10} {4:<40}'.format('ID', 'Type', 'Season', 'Episode', 'Title'))
        for i in range(len(list_id)):
            log.info('{0:<15} {1:<20} {2:<10} {3:<10} {4:<40}'.format(list_id[i], list_type[i], list_season[i], list_episode[i], list_title[i]))


def season(json_season, series_id):
    items = json_season.get('items')

    list_id = list()
    list_title = list()
    list_season = list()
    for item in items:
        list_id.append(item.get('id'))
        list_title.append(item.get('title'))
        list_season.append(item.get('season_number'))

    log.info('Season for: ', series_id)
    if len(list_id) == 0:
        log.warn('No season found for this series.')
    else:
        log.info('{0:<15} {1:<10} {2:<40}'.format('ID', 'Season', 'Title'))
        for i in range(len(list_id)):
            log.info('{0:<15} {1:<10} {2:<40}'.format(list_id[i], list_season[i], list_title[i]))


def movie(json_movie, movie_id, config):
    items = json_movie.get('items')
    premium = utils.get_premium(config)

    list_id = list()
    list_title = list()
    list_duration_ms = list()
    list_premium_only = list()
    for item in items:
        premium_only = item.get('is_premium_only')
        if premium_only:
            if premium:
                id = utils.get_stream_id(item)
            else:
                id = 'None'
        else:
            id = utils.get_stream_id(item)

        list_id.append(id)
        list_title.append(item.get('title'))
        list_duration_ms.append(item.get('duration_ms'))
        list_premium_only.append(premium_only)

    log.info('Movie for: ', movie_id)
    if len(list_id) == 0:
        log.warn('No movie found for this id.')
    else:
        log.info('{0:<15} {1:<15} {2:<20} {3:<40}'.format('ID', 'Premium only', 'Duration', 'Title'))
        for i in range(len(list_id)):
            log.info(
                '{0:<15} {1:<15} {2:<20} {3:<40}'.format(list_id[i], utils.boolean_to_str(list_premium_only[i]), utils.get_duration(list_duration_ms[i]), list_title[i]))


def episode(json_episode, season_id, config):
    items = json_episode.get('items')
    premium = utils.get_premium(config)

    list_id = list()
    list_title = list()
    list_episode = list()
    list_season = list()
    list_premium_only = list()
    for item in items:
        premium_only = item.get('is_premium_only')
        if premium_only:
            if premium:
                id = utils.get_stream_id(item)
            else:
                id = 'None'
        else:
            id = utils.get_stream_id(item)

        list_id.append(id)
        list_title.append(item.get('title'))
        list_episode.append(item.get('episode'))
        list_season.append(item.get('season_number'))
        list_premium_only.append(premium_only)

    log.info('Episode for: {}'.format(season_id))
    if len(list_id) == 0:
        log.warn('No episode found for this season.')
    else:
        log.info(
            '{0:<15} {1:<10} {2:<10} {3:<15} {4:<40}'.format('ID', 'Season', 'Episode', 'Premium only', 'Title'))
        for i in range(len(list_id)):
            log.info(
                '{0:<15} {1:<10} {2:<10} {3:<15} {4:<40}'.format(list_id[i], list_season[i], list_episode[i], utils.boolean_to_str(list_premium_only[i]), list_title[i]))


def playlist(json_episode, config, playlist_episode):
    playlist_id = list()
    items = json_episode.get('items')
    premium = utils.get_premium(config)

    list_id = list()
    list_title = list()
    list_episode = list()
    list_season = list()
    list_premium_only = list()
    for item in items:
        premium_only = item.get('is_premium_only')
        if premium_only:
            if premium:
                id = utils.get_stream_id(item)
            else:
                id = 'None'
        else:
            id = utils.get_stream_id(item)

        list_id.append(id)
        list_title.append(item.get('title'))
        list_episode.append(item.get('episode'))
        list_season.append(item.get('season_number'))
        list_premium_only.append(premium_only)

    episode_count = utils.get_episode_count(list_episode)
    playlist_episode = utils.get_playlist_episode(playlist_episode, episode_count)
    if len(list_id) == 0:
        log.warn('No episode found for this season.')
    else:
        for i in range(len(playlist_episode)):
            if playlist_episode[i] in list_episode:
                for e in range(len(list_episode)):
                    if list_episode[e] == playlist_episode[i]:
                        if list_premium_only[e] and premium == False:
                            log.warn('Prmeium only: S{}.Ep{} - {}'.format(list_season[e], list_episode[e], list_title[e]))
                        else:
                            log.info('Added to playlist: S{}.Ep{} - {}'.format(list_season[e], list_episode[e], list_title[e]))
                            playlist_id.append(list_id[e])
                        break
            else:
                log.warn('Not found : Ep{}'.format(playlist_episode[i]))
    return playlist_id


def download_url(json_stream, config):
    video_url = None
    subtitles_url = None
    subtitles_language = config.get('preferences').get('subtitles').get('language')
    video_hardsub = config.get('preferences').get('video').get('hardsub')

    json_video = json_stream.get('streams').get('adaptive_hls')
    json_subtitles = json_stream.get('subtitles')
    audio_language = json_stream.get('audio_locale')

    log.info('Audio language: [{}]'.format(audio_language))
    log.info('Available subtitle language: {}'.format(utils.get_language_available(json_video)))

    if video_hardsub:
        if subtitles_language in json_video:
            video_url = json_video.get(subtitles_language).get('url')
        else:
            if config.get('preferences').get('download').get('video'):
                log.warn('The language of the settings subtitles is not available for the hardsub.')
    else:
        video_url = json_video.get('').get('url')

    if subtitles_language in json_subtitles:
        subtitles_url = json_subtitles.get(subtitles_language).get('url')
    else:
        if config.get('preferences').get('download').get('subtitles'):
            log.warn('The language of the settings subtitles is not available.')

    if not video_url is None:
        video_url = get_m3u8_url(video_url, config)

    return video_url, subtitles_url, audio_language


def get_m3u8_url(video_url, config):
    resolution = str(config.get('preferences').get('video').get('resolution'))
    m3u8_url = None
    resolution_available = list()
    r = requests.get(video_url).text
    items = r.split('#EXT-X-STREAM')
    for item in items:
        if 'RESOLUTION' in item:
            m3u8_resolution = item.split('RESOLUTION=')[1].split(',')[0].split('x')[1].strip()
            if not m3u8_resolution in resolution_available:
                resolution_available.append(m3u8_resolution)
            if resolution in item:
                m3u8_url = 'http{}'.format(item.split('http')[1].strip())

    log.info('Video resolution available: {}'.format(resolution_available))
    return m3u8_url


def get_metadata(type, id, config) -> Metadata:
    (policy, signature, key_pair_id) = utils.get_token(config)
    config = utils.get_config()


    params = {
        'Policy': policy,
        'Signature': signature,
        'Key-Pair-Id': key_pair_id,
        'locale': utils.get_locale(config)
    }

    endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/{}/{}'.format(config.get('configuration').get('token').get('bucket'), type, id)
    r = requests.get(endpoint, params=params).json()
    if utils.check_error(r):
        sys.exit(0)

    if type == 'episodes':
        series_id = r.get('series_id')
        series_title = r.get('series_title')
        season_number = r.get('season_number')
        episode = r.get('episode')
        title = r.get('title')
        description = r.get('description')

        episode_air_date = r.get('episode_air_date')
        if '+' in episode_air_date:
            episode_air_date = '{}Z'.format(episode_air_date.split('+')[0])
        episode_air_date = datetime.strptime(episode_air_date, '%Y-%m-%dT%H:%M:%SZ')

        series_title = utils.check_characters(series_title)
        title = utils.check_characters(title)
        description = utils.check_characters(description)

        (cover, metadata) = get_cover(series_id, 'series', config)
        thumbnail = r.get('images').get('thumbnail')[0][-1].get('source')

        path = config.get('preferences').get('download').get('path')
        if path is None:
            path = os.path.join(series_title, 'Season {}'.format(season_number))
        else:
            path = os.path.join(path, series_title, 'Season {}'.format(season_number))

        output = '[S{}.Ep{}] {} - {}'.format(season_number, episode, series_title, title)

        metadata += ['-metadata', 'genre="{}"'.format(utils.get_metadata_genre(config)),
                     '-metadata', 'date="{}"'.format(episode_air_date),
                     '-metadata', 'show="{}"'.format(series_title),
                     '-metadata', 'season_number="{}"'.format(season_number),
                     '-metadata', 'episode_sort="{}"'.format(episode),
                     '-metadata', 'title="{}"'.format(title),
                     '-metadata', 'description="{}"'.format(description)]

    elif type == 'movies':
        listing_id = r.get('listing_id')
        title = r.get('title')
        description = r.get('description')
        (cover, metadata) = get_cover(listing_id, 'movie_listings', config)
        thumbnail = r.get('images').get('thumbnail')[0][-1].get('source')

        title = utils.check_characters(title)
        description = utils.check_characters(description)

        path = config.get('preferences').get('download').get('path')
        if path is None:
            path = os.path.join(title)
        else:
            path = os.path.join(path, title)

        output = '[Movie] {}'.format(title)
        metadata += ['-metadata', 'genre="{}"'.format(utils.get_metadata_genre(config)),
                     '-metadata', 'title="{}"'.format(title),
                     '-metadata', 'description="{}"'.format(description)]
    else:
        return Metadata(
            metadata = [],
            cover = "",
            thumbnail = "",
            output = "",
            path = "",
        )

    return Metadata(
        metadata,
        cover,
        thumbnail,
        output,
        path
    )


def get_cover(media_id, type, config) -> Tuple[str, list[str]]:
    (policy, signature, key_pair_id) = utils.get_token(config)
    config = utils.get_config()

    params = {
        'Policy': policy,
        'Signature': signature,
        'Key-Pair-Id': key_pair_id,
        'locale': utils.get_locale(config)
    }

    endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/{}/{}'.format(config.get('configuration').get('token').get('bucket'), type, media_id)
    r = requests.get(endpoint, params=params).json()
    if utils.check_error(r):
        sys.exit(0)

    if type == 'series':
        cover = r.get('images').get('poster_tall')[0][-1].get('source')
        content_provider = r.get('content_provider')

        content_provider = utils.check_characters(content_provider)
        metadata = ['-metadata', 'publisher="{}"'.format(content_provider)]
    elif type == 'movie_listings':
        cover = r.get('images').get('poster_tall')[0][-1].get('source')
        movie_release_year = r.get('movie_release_year')
        content_provider = r.get('content_provider')

        content_provider = utils.check_characters(content_provider)
        metadata = ['-metadata', 'date="{}"'.format(movie_release_year), '-metadata', 'publisher="{}"'.format(content_provider)]
    else:
        cover = ""
        metadata = []

    return cover, metadata
