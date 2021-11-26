import logging
import os
import sys
import re
import requests
from typing import Tuple, NamedTuple
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf

log = logging.getLogger(__name__)

res_pat = re.compile(r'RESOLUTION=(\d+)x(\d+),', re.IGNORECASE)
uri_pat = re.compile(r'URI="(.*?)"', re.IGNORECASE)
audio_pat = re.compile(r'AUDIO="(.*?)"', re.IGNORECASE)
group_pat = re.compile(r'GROUP-ID="(.*?)"', re.IGNORECASE)


class Metadata(NamedTuple):
    metadata: list[str] = []
    thumbnail: str = ""
    output: str = ""
    path: str = ""


def outputShow(show: dict, with_children: bool=False) -> str:
    """Print information for a single show"""
    fields = {
        'id': 'ID',
        'externalItemId': 'ExternalID',
        'order': 'Order',
        'number': 'Number',
        'releaseYear': 'ReleaseYear',
        'title': 'Title',
        'type': 'Type',
        'subtitles': 'Subs',
        'audio': 'Audio',
    }

    for (field, display) in fields.items():
        print('{:>20}: {}'.format(display, show.get(field, '')))

    if with_children:
        outputSeasonList(show.get('children', []))

    return show.get('id', '')


def outputShowsList(show_results: list[dict]) -> list[str]:
    """Print a table containing a list of shows"""
    header_fields = ('ID', 'ExternalID', 'Year', 'Title')
    table_format_list = ['{:<10}']*(len(header_fields) - 1)
    table_format_list.append('{:<40}')
    table_format = ' '.join(table_format_list)

    print(table_format.format(*header_fields))
    for show in show_results:
        print(table_format.format(
            show.get('venueId', ''),
            show.get('id', ''),
            show.get('releaseYear', ''),
            show.get('title', ''),
        ))

    return [show.get('id', '') for show in show_results]


def outputSeason(season: dict, with_children: bool=False) -> str:
    """Print information for a single season"""
    fields = {
        'id': 'ID',
        'externalItemId': 'ExternalID',
        'order': 'Order',
        'number': 'Number',
        'title': 'Title',
    }

    print('{:>20}: {}'.format('Show', season.get('item', {}).get('titleName', '')))
    for (field, display) in fields.items():
        print('{:>20}: {}'.format(display, season.get(field, '')))

    if with_children:
        outputEpisodeList(season.get('children', []))

    return season.get('id', '')


def outputSeasonList(season_results: list[dict]) -> list[str]:
    """Print a table containing a list of seasons"""
    header_fields = ('ID', 'ExternalID', 'Order', 'Episodes', 'Title')
    table_format_list = ['{:<15}']*(len(header_fields) - 1)
    table_format_list.append('{:<40}')
    table_format = ' '.join(table_format_list)

    print(table_format.format(*header_fields))
    for season in season_results:
        print(table_format.format(
            season.get('id', ''),
            season.get('externalItemId', ''),
            season.get('order'),
            season.get('childCount'),
            season.get('title', ''),
        ))
    return [season.get('id', '') for season in season_results]


def outputEpisode(episode: dict) -> str:
    """Print information for a single episode"""
    fields = {
        'id': 'ID',
        'externalItemId': 'ExternalID',
        'order': 'Order',
        'number': 'Number',
        'quality': 'Quality',
        'releaseDate': 'ReleaseDate',
        'subscriptionRequired': 'SubscriptionRequired',
        'title': 'Title',
        'seasonTitle': 'SeasonTitle',
        'seriesTitle': 'SeriesTitle',
        'description': 'Description',
    }

    for (field, display) in fields.items():
        print('{:>20}: {}'.format(display, episode.get(field, '')))

    return episode.get('id', '')


def outputEpisodeList(episode_results: list[dict]) -> list[str]:
    """Print a table containing a list of episodes"""
    header_fields = ('ID', 'ExternalID', 'Order', 'Number', 'Quality', 'Release', 'Premium?' , 'Title')
    table_format_list = ['{:<10}']*(len(header_fields) - 1)
    table_format_list.append('{:<40}')
    table_format = ' '.join(table_format_list)

    print(table_format.format(*header_fields))
    for episode in episode_results:
        print(table_format.format(
            episode.get('id', ''),
            episode.get('externalItemId', ''),
            episode.get('order'),
            episode.get('number'),
            str(list(episode.get('quality', {}).values())),
            episode.get('releaseDate'),
            episode.get('subscriptionRequired'),
            episode.get('title', ''),
        ))

    return [episode.get('id', '') for episode in episode_results]


def outputSearchShowsResults(json_search: dict):
    items = json_search.get('items', {}).get('hits', [])

    if len(items) == 0:
        log.warn('No results found')
    else:
        return outputShowsList(items)


# def seasons_for_series(json_season: dict, series_id: str) -> None:
#     items = json_season.get('items', [])

#     log.debug("SeasonsData: %s", items)

#     seasons_info = [(item.get('id'), item.get('title'), item.get('season_number')) for item in items]

#     print('Season for: %s', series_id)
#     if len(seasons_info) == 0:
#         log.warn('No season found for this series.')
#     else:
#         print('{0:<15} {1:<10} {2:<40}'.format('ID', 'Season', 'Title'))
#         for info_tuple in seasons_info:
#             print('{0:<15} {1:<10} {2:<40}'.format(*info_tuple))


def movie(json_movie: dict, movie_id: str, config: KamyrollConf):
    items = json_movie.get('items', [])
    premium = utils.has_premium(config)

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

    print('Movie for: %s', movie_id)
    if len(list_id) == 0:
        log.warn('No movie found for this id.')
    else:
        print('{0:<15} {1:<15} {2:<20} {3:<40}'.format('ID', 'Premium only', 'Duration', 'Title'))
        for i in range(len(list_id)):
            print(
                '{0:<15} {1:<15} {2:<20} {3:<40}'.format(list_id[i], utils.boolean_to_str(list_premium_only[i]), utils.get_duration(list_duration_ms[i]), list_title[i]))


def episodes_for_season(json_episode, season_id, config: KamyrollConf) -> list[str]:
    items = json_episode.get('items')
    premium = utils.has_premium(config)

    log.debug("EpisodesData: %s", items)

    episodes = [
        (
            None if item.get("is_premium_only") and not premium else utils.get_stream_id(item),
            item.get('season_number'),
            item.get('episode'),
            item.get('sequence_number'),
            bool(item.get("is_premium_only")),
            item.get('title'),
        ) 
        for item in items
    ]

    print('Episode for: %s', season_id)
    if len(episodes) == 0:
        log.warn('No episode found for this season.')
    else:
        print(
            '{0:<15} {1:<10} {2:<10} {3:<10} {4:<15} {5:<40}'.format('Stream ID', 'Season', 'Episode', 'Sequence', 'Premium only', 'Title'))
        for info in episodes:
            print('{0:<15} {1:<10} {2:<10} {3:<10} {4:<15} {5:<40}'.format(*info))

    return([info[0] for info in episodes if info[0] is not None])


# def playlist(json_episode, config, episode_range: Sequence[int]):
#     playlist_id = list()
#     items = json_episode.get('items')
#     is_premium = utils.has_premium(config)

#     list_id = list()
#     list_title = list()
#     list_episode = list()
#     list_season = list()
#     list_premium_only = list()
#     for item in items:
#         premium_only = item.get('is_premium_only')
#         if premium_only:
#             if is_premium:
#                 id = utils.get_stream_id(item)
#             else:
#                 id = 'None'
#         else:
#             id = utils.get_stream_id(item)

#         list_id.append(id)
#         list_title.append(item.get('title'))
#         list_episode.append(item.get('episode'))
#         list_season.append(item.get('season_number'))
#         list_premium_only.append(premium_only)

#     episode_count = utils.get_episode_count(list_episode)
#     episode_range = utils.get_episode_list(episode_range, episode_count)
#     if len(list_id) == 0:
#         log.warn('No episode found for this season.')
#     else:
#         for i in range(len(episode_range)):
#             if episode_range[i] in list_episode:
#                 for e in range(len(list_episode)):
#                     if list_episode[e] == episode_range[i]:
#                         if list_premium_only[e] and is_premium == False:
#                             log.warn('Premium only: S{i:02}.Ep{i:02} - {}'.format(list_season[e], list_episode[e], list_title[e]))
#                         else:
#                             log.info('Added to playlist: S{}.Ep{} - {}'.format(list_season[e], list_episode[e], list_title[e]))
#                             playlist_id.append(list_id[e])
#                         break
#             else:
#                 log.warn('Not found : Ep{}'.format(episode_range[i]))
#     return playlist_id


def getVideoURL(video_options: list[dict], config: KamyrollConf) -> str:
    resolution = str(config.preference('video', 'resolution'))
    def _filter(video):
        return str(video.get('mediaInfo', {}).get('frameHeight', 0)) == resolution

    return next(
            (video.get('filePath', '') for video in video_options if _filter(video)),
            video_options[0].get('filePath', '')
        )


def streamURLsFromIndex(index_m3u8_url: str, config: KamyrollConf) -> Tuple[str, str]:
    requested_resolution = str(config.preference('video', 'resolution'))
    video_url = ""
    audio_group = ""
    resolution_option = set()
    index = requests.get(index_m3u8_url).text
    entries = index.split('\n')

    items = index.split('#EXT-X-STREAM')

    log.debug(items)

    audio_options = {}
    for idx, item in enumerate(entries):
        if item.startswith('#EXT-X-MEDIA') and "TYPE=AUDIO" in item:
            group_match = group_pat.search(item)
            uri_match = uri_pat.search(item)
            if group_match and uri_match:
                audio_options[group_match.group(1)] = uri_match.group(1)
        elif item.startswith('#EXT-X-STREAM-INF'):
            res_match = res_pat.search(item)
            audio_match = audio_pat.search(item)
            if res_match is not None:
                match_resolution = res_match.group(2)
                resolution_option.add(match_resolution)
                if match_resolution == requested_resolution:
                    video_url = entries[idx + 1].strip()
                    if audio_match:
                        audio_group = audio_match.group(1)

    log.info('Video resolution available: {}'.format(resolution_option))
    return (video_url, audio_options.get(audio_group, ''))


def getEpisodeExperience(episode_data: dict, language_code: str='ja') -> dict:
    media_info = episode_data.get('media', {})
    if len(media_info) == 0:
        return {}

    def _mediaFilter(media: dict) -> bool:
        return (
            media.get('mediaType', '') == 'experience'
            and media.get('languages', [{}])[0].get('code', '').lower() == language_code.lower()
        )

    return next((media for media in media_info if _mediaFilter(media)), {})


def getEpisodeMetadata(episode_data: dict, config: KamyrollConf) -> Metadata:

    metadata = []

    if episode_data.get('type', '') == 'episode':
        parent = episode_data.get('parent', {})
        series_title = parent.get('title', '')
        season_number = parent.get('seasonNumber', '')
        episode_number = episode_data.get('number', '')
        order = episode_data.get('order', -1)
        title = episode_data.get('title', '')
        description = episode_data.get('description', '')
        release_date = episode_data.get('releaseDate', '')

        series_title = utils.check_characters(series_title)
        title = utils.check_characters(title)
        description = utils.check_characters(description)

        # (cover, metadata) = get_cover(series_id, 'series', config)
        thumbnail = episode_data.get('filename', '')

        path = str(config.preference('download', 'path'))
        if path is None:
            path = os.path.join(series_title, 'Season {:0>2}'.format(season_number))
        else:
            path = os.path.join(path, series_title, 'Season {:0>2}'.format(season_number))

        # # Handle episide 11.5, etc
        # episode_str: str = str(sequence_number)
        # if isinstance(sequence_number, float):
        #     episode_str = "{:03.1f}".format(sequence_number)
        # else:
        #     episode_str = "{:02d}".format(sequence_number)

        # if str(sequence_number) != str(episode):
        #     episode_str = "{} ({})".format(episode_str, episode)

        output = '{} S{:0>2}.E{:0>2} - {}'.format(series_title, season_number, episode_number, title)

        metadata += [
            '-metadata', 'date="{}"'.format(release_date),
            '-metadata', 'show="{}"'.format(series_title),
            '-metadata', 'season_number="{}"'.format(season_number),
            '-metadata', 'episode_sort="{}"'.format(order),
            '-metadata', 'episode="{}"'.format(episode_number),
            '-metadata', 'title="{}"'.format(title),
            '-metadata', 'description="{}"'.format(description),
        ]

    # elif type == 'movies':
    #     listing_id = experience.get('listing_id')
    #     title = experience.get('title')
    #     description = experience.get('description')
    #     (cover, metadata) = get_cover(listing_id, 'movie_listings', config)
    #     thumbnail = experience.get('images').get('thumbnail')[0][-1].get('source')

    #     title = utils.check_characters(title)
    #     description = utils.check_characters(description)

    #     path = str(config.preference('download', 'path'))
    #     if path is None:
    #         path = os.path.join(title)
    #     else:
    #         path = os.path.join(path, title)

    #     output = '[Movie] {}'.format(title)
    #     metadata += ['-metadata', 'genre="{}"'.format(utils.get_metadata_genre(config)),
    #                  '-metadata', 'title="{}"'.format(title),
    #                  '-metadata', 'description="{}"'.format(description)]
    else:
        return Metadata(
            metadata = [],
            thumbnail = "",
            output = "",
            path = "",
        )

    return Metadata(
        metadata,
        thumbnail,
        output,
        path
    )


def get_cover(media_id, type, config: KamyrollConf) -> Tuple[str, list[str]]:
    (policy, signature, key_pair_id) = utils.get_token(config)

    params = {
        'Policy': policy,
        'Signature': signature,
        'Key-Pair-Id': key_pair_id,
        'locale': utils.get_locale(config)
    }

    endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/{}/{}'.format(config.config('token', 'bucket'), type, media_id)
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
