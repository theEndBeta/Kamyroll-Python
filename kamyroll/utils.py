import base64
import math
from datetime import datetime
import os
import json
import sys
import logging
import requests
from pathlib import Path
from typing import Sequence, Tuple
from requests.structures import CaseInsensitiveDict
from kamyroll.config import KamyrollConf

src_path = Path(__file__).parent.absolute()
log = logging.getLogger(__name__)



def get_login_form(args_login: str) -> Tuple[str, str]:
    try:
        username = args_login.split(':')[0].strip()
        password = args_login.split(':')[1].strip()
        return username, password
    except Exception as e:
        log.error('Invalid login form:', e)
        sys.exit(0)


def decrypt_base64(data):
    key_bytes = data.encode('ascii')
    base64_bytes = base64.b64decode(key_bytes)
    return base64_bytes.decode('ascii')


def get_episode_list(episodes: str, episode_count: int) -> Sequence[int]:
    playlist_episode = []

    if '[' in episodes and ']' in episodes:
        if episodes.startswith('[-'):
            if episodes.endswith(':]'):
                number = int(episodes.split('[-')[1].split(':]')[0]) - 1
                playlist_episode = get_numbers(episode_count - number, episode_count)
                return playlist_episode
            else:
                number = int(episodes.split('[-')[1].split(']')[0]) - 1
                playlist_episode.append(str(episode_count - number))
                return playlist_episode
        elif episodes.startswith('[') and episodes.endswith(':]'):
            number = int(episodes.split('[')[1].split(':]')[0]) + 1
            playlist_episode = get_numbers(number, episode_count)
            return playlist_episode
        elif episodes.startswith('[:-') and episodes.endswith(']'):
            number = int(episodes.split('[:-')[1].split(']')[0])
            playlist_episode = get_numbers(0, episode_count - number)
            return playlist_episode
        else:
            start = int(episodes.split('[')[1].split(':')[0])
            end = int(episodes.split(':')[1].split(']')[0])
            if start <= end and end <= episode_count:
                playlist_episode = get_numbers(start, end)
                return playlist_episode
            else:
                log.error('Invalid interval')
                sys.exit(0)
    else:
        log.error('Invalid playlist format.')
        sys.exit(0)


def get_numbers(start: int, end: int) -> Sequence[int]:
    if start > end:
        log.error('Ending episode number must be greater than starting', start, end)
    return range(start, end + 1)


def get_episode_count(episode_list: list[int]) -> int:
    count = 0
    for i in range(len(episode_list)):
        episode = int(episode_list[i])
        if episode > count:
            count = episode
    return count


def get_authorization(config: KamyrollConf) -> dict[str, str]:
    token_type = config.config('token', 'token_type')
    access_token = config.config('token', 'access_token')
    return {'Authorization': '{} {}'.format(token_type, access_token)}


def check_error(json_request: dict) -> bool:
    if 'error' in json_request:
        log.debug("JSON error: %s", json_request)

        error_code = json_request.get('error')

        msg = 'ERROR: Status code: {}'.format(error_code)
        if error_code == 'invalid_grant':
            msg = 'ERROR: Invalid login information.'

        log.error(msg)
        return True
    elif 'message' in json_request and 'code' in json_request:
        log.error(json_request.get('message'))
        return True
    else:
        return False


def get_headers(config: KamyrollConf, with_auth: bool = True) -> CaseInsensitiveDict[str]:
    headers = CaseInsensitiveDict({
        'User-Agent': config.config('headers', 'user_agent'),
        'devicetype': config.config('headers', 'devicetype'),
        # 'Content-Type': 'application/x-www-form-urlencoded',
    })

    if with_auth:
        headers.update(get_authorization(config))

    return headers


def get_locale(config: KamyrollConf):
    bucket = config.config('token', 'bucket')
    country_code = bucket.split('/')[1]
    items = ['en-US', 'en-GB', 'es-419', 'es-ES', 'pt-BR', 'pt-PT', 'fr-FR', 'de-DE', 'ar-SA', 'it-IT', 'ru-RU']
    locale = items[0]
    for item in items:
        country = item.split('-')[1].strip()
        if country_code == country:
            locale = item
            break
    return locale


def get_metadata_genre(config: KamyrollConf):
    bucket = config.config('token', 'bucket')
    country_code = bucket.split('/')[1]
    list_language = ['en-US', 'en-GB', 'es-419', 'es-ES', 'pt-BR', 'pt-PT', 'fr-FR', 'de-DE', 'ar-SA', 'it-IT', 'ru-RU']
    list_genre = ['Animation', 'Animation', 'Animación', 'Animación', 'Animação', 'Animação', 'Animation', 'Animation',
                  'أنيميشن', 'Animazione', 'Анимация']
    genre = list_genre[0]
    for i in range(len(list_language)):
        country = list_language[i].split('-')[1].strip()
        if country_code == country:
            genre = list_genre[i]
            break
    return genre


def get_token(config: KamyrollConf):
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    minute = datetime.now().minute
    second = datetime.now().second

    current_time = datetime.strptime('{}-{}-{}T{}:{}:{}Z'.format(year, month, day, hour, minute, second),'%Y-%m-%dT%H:%M:%SZ')
    expires_time = datetime.strptime(str(config.config('token', 'expires')), '%Y-%m-%dT%H:%M:%SZ')

    if current_time >= expires_time:
        policy = config.config('token', 'policy')
        signature = config.config('token', 'signature')
        key_pair_id = config.config('token', 'key_pair_id')
        return policy, signature, key_pair_id
    else:
        authorization = get_authorization(config, True)
        headers = get_headers(config)
        headers.update(authorization)

        session = get_session(config)
        session.headers = headers

        r = session.get('https://beta-api.crunchyroll.com/index/v2').json()
        if check_error(r):
            sys.exit(0)

        cms = r.get('cms')
        bucket = cms.get('bucket')
        policy = cms.get('policy')
        signature = cms.get('signature')
        key_pair_id = cms.get('key_pair_id')
        expires = cms.get('expires')

        json_token = config.config('token')
        config.set_conf(bucket, 'token', 'bucket')
        config.set_conf(policy, 'token', 'policy')
        config.set_conf(signature, 'token', 'signature')
        config.set_conf(key_pair_id, 'token', 'key_pair_id')
        config.set_conf(expires, 'token', 'expires')
        config.save()
        return policy, signature, key_pair_id


def boolean_to_str(boolean: bool) -> str:
    if boolean:
        return 'True'
    else:
        return 'False'


def get_session(config: KamyrollConf):
    session = requests.session()
    if config.preference('proxy', 'is_proxy'):
        uuid = config.preference('proxy', 'uuid')
        agent_key = config.preference('proxy', 'agent_key')
        host = config.preference('proxy', 'host')
        port = config.preference('proxy', 'port')
        proxy_type = config.preference('proxy', 'type')

        if not proxy_type or proxy_type == 'https' or proxy_type == 'http':
            proxies = {
                'http': 'https://user-uuid-{}:{}@{}:{}'.format(uuid, agent_key, host, port),
                'https': 'https://user-uuid-{}:{}@{}:{}'.format(uuid, agent_key, host, port)
            }
        elif proxy_type == 'socks4' or proxy_type == 'socks5':
            if uuid and agent_key:
                proxies = {
                    'http': '{}://{}:{}@{}:{}'.format(proxy_type, uuid, agent_key, host, port),
                    'https': '{}://{}:{}@{}:{}'.format(proxy_type, uuid, agent_key, host, port),
                }
            else:
                proxies = {
                    'http': '{}://{}:{}'.format(proxy_type, host, port),
                    'https': '{}://{}:{}'.format(proxy_type, host, port),
                }
        else:
            log.error('Unknown proxy type {}'.format(proxy_type))
            sys.exit(0)
        session.proxies.update(proxies)

    session.get("https://www.funimation.com/log-in")
    return session


def has_premium(config: KamyrollConf):
    if 'crunchyroll' in config.config('token', 'bucket'):
        return True
    else:
        return False


def get_stream_id(json_stream):
    items = json_stream.get('__links__').get('streams').get('href').split('videos/')[1].split('/')
    id = 'None'
    for i in range(len(items)):
        if items[i + 1] == 'streams':
            id = items[i]
            break
    return id


def get_download_type(json_download):
    href = json_download.get('__links__').get('resource').get('href')
    type = None
    if 'episodes' in href:
        type = 'episodes'
    if 'movies' in href:
        type = 'movies'
    id = href.split('/')[-1]
    return type, id


def get_language_available(json_language) -> list[str]:
    language_available = list()
    items = ['', 'en-US', 'en-GB', 'es-419', 'es-ES', 'pt-BR', 'pt-PT', 'fr-FR', 'de-DE', 'ar-SA', 'it-IT', 'ru-RU']
    for item in items:
        if item in json_language:
            language_available.append(item)
    return language_available


def check_characters(title):
    characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']
    if not title: return title
    for character in characters:
        if character in title:
            title = title.replace(character, '')
    return title.strip()


def get_ffmpeg_language(code):
    language = 'jpn'
    language_code = ['en-US', 'en-GB', 'es-419', 'es-ES', 'pt-BR', 'pt-PT', 'fr-FR', 'de-DE', 'ar-SA', 'it-IT', 'ru-RU', 'jp-JP']
    ffmpeg_language = ['eng', 'bre', 'spa', 'spa', 'por', 'por', 'fra', 'deu', 'ara', 'ita', 'rus', 'jpn']
    for i in range(len(language_code)):
        if code == language_code[i]:
            language = ffmpeg_language[i]
            break
    return language


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_language_title(code):
    language_code = ['en-US', 'en-GB', 'es-419', 'es-ES', 'pt-BR', 'pt-PT', 'fr-FR', 'de-DE', 'ar-SA', 'it-IT', 'ru-RU']
    language_titles = ['English (US)', 'English (UK)', 'Español', 'Español (España)', 'Português (Brasil)', 'Português (Portugal)', 'Français (France)', 'Deutsch', 'العربية', 'Italiano', 'Русский']
    language = ''
    for i in range(len(language_code)):
        if code == language_code[i]:
            language = ' [{}]'.format(language_titles[i])
            break
    return language


def get_duration(duration_ms: int) -> str:
    hours = int((duration_ms / 3.6e6) % 24)
    minutes = int( (duration_ms / 60000) % 60)
    seconds = int((duration_ms / 1000) % 60)
    return '{} h {} min {} sec'.format(math.floor(hours), math.floor(minutes), math.floor(seconds))
