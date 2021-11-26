import logging
import os
import sys
from typing import Sequence
import requests
import kamyroll.converter as converter
import kamyroll.extractor as extractor
import kamyroll.utils as utils
from kamyroll.config import KamyrollConf
from kamyroll.api import crunchyroll as KamyAPI
import subprocess

log = logging.getLogger(__name__)


def image(output, url):
    if not os.path.exists(output):
        response = requests.get(url)
        with open(output, 'wb') as file:
            file.write(response.content)


class crunchyroll:

    def __init__(self, api: KamyAPI):
        self.config = api.config
        self.api = api


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


    def download(self, episode_id: str) -> None:
        """Download a video and accoutrements from stream id
        """
        episode_data = self.api.getEpisodeData(episode_id)
        if episode_data is None:
            log.error("No data found for episode: ", episode_id)
            return

        playback_response = self.api.session.get(
                'https://playback.prd.funimationsvc.com/v1/play/{}'.format(episode_data.get('externalItemId')),
                params={ 'deviceType': 'web' }
            ).json()

        log.warning(playback_response)

        language_code = str(self.config.preference('video', 'language_code'))
        experience = extractor.getEpisodeExperience(episode_data, language_code=language_code)

        media = experience.get('mediaChildren', [])

        metadata = extractor.getEpisodeMetadata(episode_data, self.config)
        utils.create_folder(metadata.path)

        if self.config.preference('download', 'subtitles'):
            self._download_subtitles(metadata, [item for item in media if item.get('mediaType', '') == 'subtitle'])

        # if self.config.preference('image', 'cover') or self.config.preference('video', 'attached_picture'):
        #     image(os.path.join(metadata.path, 'cover.jpg'), metadata.cover)
        #     if self.config.preference('image', 'cover'):
        #         log.info('Downloaded cover')

        # if metadata.thumbnail != "":
        #     image(os.path.join(metadata.path, '{}.jpg'.format(metadata.output)), metadata.thumbnail)
        #     log.info('Downloaded thumbnail')

        manifest_url = playback_response.get('primary', {}).get('manifestPath')
        (video_url, audio_url) = extractor.streamURLsFromIndex(manifest_url, self.config)

        auth_tokens_resp = self.api.session.get('https://frps.prd.funimationsvc.com/v1/get-auth-tokens', params={'user_id':2080499})
        log.warn(auth_tokens_resp.json())

        # video_url = extractor.getVideoURL(
        #     [item for item in media if item.get('mediaType', '') == 'video'],
        #     self.config
        # )
        if self.config.preference('download', 'video'):
            if video_url is None:
                log.error('No video download link available.')
                sys.exit(0)

            extension = str(self.config.preference('video', 'extension'))
            if extension == 'mkv' or extension == 'mp4':
                self._download_video(metadata, video_url, extension, language_code, audio_url)
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


    def _download_video(self,
        metadata: extractor.Metadata,
        video_url: str,
        extension: str,
        audio_language: str,
        audio_url: str = ''
    ) -> None:
        """Download a single video
        """
        index = 0
        subs = list()
        log.warn(video_url)
        command = [
            'ffmpeg',
            '-hide_banner',
            '-user_agent', utils.get_headers(self.config, with_auth=False).get('user-agent', ''),
            # '-v', 'trace',
            '-stats',
            '-y',
            '-i', video_url,
        ]

        if audio_url != '':
            command += [
                '-user_agent', utils.get_headers(self.config, with_auth=False).get('user-agent', ''),
                '-i', audio_url,
            ]

        log.debug('Download Video URL: %s', video_url)

        sub_language_code = self.config.preference('subtitles', 'language_code')
        subtitle_extensions = str(self.config.preference('subtitles', 'ext')).split(',')
        if extension == 'mkv':
            if self.config.preference('download', 'subtitles'):
                subtitles_path = os.path.join(metadata.path, '{}.{}'.format(metadata.output, sub_language_code))

                for sub_ext in subtitle_extensions:
                    if os.path.exists('{}.{}'.format(subtitles_path, sub_ext)):
                        command += ['-i', '{}.{}'.format(subtitles_path, sub_ext)]
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
                    'language={}'.format(utils.get_ffmpeg_language(self.config.preference('subtitles', 'language_code')))]

        # if self.config.preference('video', 'attached_picture'):
        #     if extension == 'mp4':
        #         command += ['-c:v:{}'.format(index), 'mjpeg', '-disposition:v:{}'.format(index), 'attached_pic']
        #     elif extension == 'mkv':
        #         command += ['-attach', '{}'.format(os.path.join(metadata.path, 'cover.jpg')), '-metadata:s:t', 'mimetype="image/jpeg"']

        command += [
            '{}'.format(os.path.join(metadata.path, '{}.{}'.format(metadata.output, extension))),
        ]

        if os.path.exists(os.path.join(metadata.path, '{}.{}'.format(metadata.output, extension))):
            log.warn('Video already exists.')
        else:
            log.info('Download resolution: [{}]'.format(self.config.preference('video', 'resolution')))
            try:
                # log.info(command)
                log.info(' '.join(command))
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


    def _download_subtitles(self, metadata: extractor.Metadata, subtitle_media: list[dict]) -> None:
        language_code = str(self.config.preference('subtitles', 'language_code'))
        exts_prefs = str(self.config.preference('subtitles', 'ext'))
        def _filter(item: dict):
            return (
                item.get('languages', [{}])[0].get('code', '') == language_code
                and item.get('ext', 'N/A') in exts_prefs
                and item.get('filePath', '') != ''
            )
        subtitles = [(sub.get('filePath', ''), sub.get('ext', '')) for sub in subtitle_media if _filter(sub)]

        if len(subtitles) == 0:
            log.error('No subtitles download link available.')
            sys.exit(0)

        subtitle = converter.Subtitles(
            os.path.join(metadata.path, metadata.output),
            language_code,
        )
        for sub in subtitles:
            subtitle.download(sub[0], sub[1])
        # if self.config.preference('subtitles', 'vtt'):
        #     subtitle.convert('vtt')
        # if self.config.preference('subtitles', 'srt'):
        #     subtitle.convert('srt')
        # if not self.config.preference('subtitles', 'ass'):
        #     subtitles_path = os.path.join(
        #         metadata.path,
        #         '{}{}.ass'.format(
        #             metadata.output,
        #             utils.get_language_title(self.config.preference('subtitles', 'language'))
        #         )
        #     )
        #     if os.path.exists(subtitles_path):
        #         os.remove(subtitles_path)
        log.info('Downloaded subtitles')
