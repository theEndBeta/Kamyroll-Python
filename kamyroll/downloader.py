import logging
import os
import sys
from typing import Sequence
import requests
import kamyroll.converter as converter
import kamyroll.extractor as extractor
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf
import subprocess

log = logging.getLogger(__name__)


def image(output, url):
    if not os.path.exists(output):
        response = requests.get(url)
        with open(output, 'wb') as file:
            file.write(response.content)


class crunchyroll:

    def __init__(self, config: KamyrollConf):
        self.config = config


    def __request_stream_data(self, stream_id: str):
        (policy, signature, key_pair_id) = utils.get_token(self.config)

        params = {
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/videos/{}/streams'.format(self.config.config('token', 'bucket'), stream_id)
        response_json = requests.get(endpoint, params=params).json()
        if utils.check_error(response_json):
            sys.exit(0)
        # log.debug("StreamData: %s", response_json)
        return response_json


    def url(self, stream_id: str):
        r = self.__request_stream_data(stream_id)
        (video_url, subtitles_url, audio_language) = extractor.download_url(r, self.config)
        log.info('Video: ', video_url)
        log.info('Subtitles:', subtitles_url)
        log.info('Audio Lang:', audio_language)
        sys.exit(0)


    def download(self, stream_id: str) -> None:
        """Download a video and accoutrements from stream id
        """
        response = self.__request_stream_data(stream_id)
        (video_url, subtitles_url, audio_language) = extractor.download_url(response, self.config)
        (type, id) = utils.get_download_type(response)
        metadata = extractor.get_metadata(type, id, self.config)
        utils.create_folder(metadata.path)

        if self.config.preference('download', 'subtitles'):
            self._download_subtitles(metadata, subtitles_url)

        if self.config.preference('image', 'cover') or self.config.preference('video', 'attached_picture'):
            image(os.path.join(metadata.path, 'cover.jpg'), metadata.cover)
            if self.config.preference('image', 'cover'):
                log.info('Downloaded cover')

        if metadata.thumbnail != "":
            image(os.path.join(metadata.path, '{}.jpg'.format(metadata.output)), metadata.thumbnail)
            log.info('Downloaded thumbnail')

        if self.config.preference('download', 'video'):
            if video_url is None:
                log.error('No video download link available.')
                sys.exit(0)

            extension = str(self.config.preference('video', 'extension'))
            if extension == 'mkv' or extension == 'mp4':
                self._download_video(metadata, video_url, extension, audio_language)
            else:
                log.error('Video extension is not supported.')
                sys.exit(0)


    def download_all(self, stream_ids: Sequence[str]) -> None:
        """Download a list of stream ids
        """
        total: int = len(stream_ids)
        for idx, stream_id in enumerate(stream_ids):
            log.info('Download playlist: {}/{}'.format(idx + 1, total))
            self.download(stream_id)


    # def download_season(self, season_id: str, episode_range: Sequence[int]):
    #     (policy, signature, key_pair_id) = utils.get_token(self.config)

    #     params = {
    #         'season_id': season_id,
    #         'Policy': policy,
    #         'Signature': signature,
    #         'Key-Pair-Id': key_pair_id,
    #         'locale': utils.get_locale(self.config)
    #     }

    #     endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/episodes'.format(self.config.config('token', 'bucket'))
    #     response_json = requests.get(endpoint, params=params).json()
    #     if utils.check_error(response_json):
    #         sys.exit(0)

    #     playlist_id = extractor.playlist(response_json, self.config, episode_range)

    #     if playlist_id == []:
    #         log.error('The playlist is empty.')
    #         sys.exit(0)
    #     else:
    #         self.download_all(playlist_id)
    #         log.info('The playlist has been downloaded')
    #         sys.exit(0)


    def _download_video(self, metadata: extractor.Metadata, video_url: str, extension: str, audio_language: str) -> None:
        """Download a single video
        """
        index = 0
        subs = list()

        command = [
            'ffmpeg',
            '-hide_banner',
            '-v', 'warning',
            '-stats',
            '-i', video_url,
        ]
        log.debug('Download Video URL: %s', video_url)
        language_title = utils.get_language_title(self.config.preference('subtitles', 'language'))
        if extension == 'mkv':
            if self.config.preference('download', 'subtitles'):
                subtitles_path = os.path.join(metadata.path, '{}{}'.format(metadata.output, language_title))

                if self.config.preference('subtitles', 'ass') and os.path.exists('{}.ass'.format(subtitles_path)):
                    command += ['-i', '{}.ass'.format(subtitles_path)]
                    index += 1
                    subs.append(index)
                if self.config.preference('subtitles', 'vtt') and os.path.exists('{}.vtt'.format(subtitles_path)):
                    command += ['-i', '{}.vtt'.format(subtitles_path)]
                    index += 1
                    subs.append(index)
                if self.config.preference('subtitles', 'srt') and os.path.exists('{}.srt'.format(subtitles_path)):
                    command += ['-i', '{}.srt'.format(subtitles_path)]
                    index += 1
                    subs.append(index)

        if self.config.preference('video', 'attached_picture') and extension == 'mp4':
            command += ['-i', '{}'.format(os.path.join(metadata.path, 'cover.jpg'))]
            index += 1

        command += ['-c', 'copy']
        # command += ['-map', '0:v', '-map', '0:a']

        # for i in subs:
        #     command += ['-map', str(i)]

        if self.config.preference('video', 'attached_picture') and extension == 'mp4':
            command += ['-map', str(index)]

        command += ['-metadata:s:a:0', 'language={}'.format(utils.get_ffmpeg_language(audio_language))]

        for i in subs:
            command += ['-metadata:s:s:{}'.format(i + 1),
                    'language="{}"'.format(utils.get_ffmpeg_language(self.config.preference('subtitles', 'language')))]

        if self.config.preference('video', 'attached_picture'):
            if extension == 'mp4':
                command += ['-c:v:{}'.format(index), 'mjpeg', '-disposition:v:{}'.format(index), 'attached_pic']
            elif extension == 'mkv':
                command += ['-attach', '{}'.format(os.path.join(metadata.path, 'cover.jpg')), '-metadata:s:t', 'mimetype="image/jpeg"']

        command += metadata.metadata

        command += ['{}'.format(os.path.join(metadata.path, '{}.{}'.format(metadata.output, extension))), '-y']

        if os.path.exists(os.path.join(metadata.path, '{}.{}'.format(metadata.output, extension))):
            log.warn('Video already exists.')
        else:
            log.info('Download resolution: [{}]'.format(self.config.preference('video', 'resolution')))
            try:
                log.debug(command)
                # log.debug(' '.join(command))
                subprocess.call(command)
                log.info('Downloaded video')
            except KeyboardInterrupt:
                log.error('KeyboardInterrupt')
                sys.exit(0)
            except Exception as e:
                log.error(e, 1)
                sys.exit(0)

        if not self.config.preference('image', 'cover'):
            if os.path.exists(os.path.join(metadata.path, 'cover.jpg')):
                os.remove(os.path.join(metadata.path, 'cover.jpg'))


    def _download_subtitles(self, metadata: extractor.Metadata, subtitles_url: str) -> None:
        if subtitles_url is None:
            log.error('No subtitles download link available.')
            sys.exit(0)

        subtitle = converter.Subtitles(
            os.path.join(metadata.path, metadata.output),
            self.config.preference('subtitles', 'language')
        )
        subtitle.download(subtitles_url)
        if self.config.preference('subtitles', 'vtt'):
            subtitle.convert('vtt')
        if self.config.preference('subtitles', 'srt'):
            subtitle.convert('srt')
        if not self.config.preference('subtitles', 'ass'):
            subtitles_path = os.path.join(
                metadata.path,
                '{}{}.ass'.format(
                    metadata.output,
                    utils.get_language_title(self.config.preference('subtitles', 'language'))
                )
            )
            if os.path.exists(subtitles_path):
                os.remove(subtitles_path)
        log.info('Downloaded subtitles')
