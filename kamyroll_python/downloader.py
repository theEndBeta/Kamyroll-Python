import os
import sys
import requests
import converter
import extractor
import utils


def image(output, url):
    if not os.path.exists(output):
        response = requests.get(url)
        file = open(output, 'wb')
        file.write(response.content)
        file.close()


class crunchyroll:

    def __init__(self, config):
        self.config = config

    def __get_request(self, stream_id):
        (policy, signature, key_pair_id) = utils.get_token(self.config)
        self.config = utils.get_config()

        params = {
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/videos/{}/streams'.format(self.config.get('configuration').get('token').get('bucket'), stream_id)
        r = requests.get(endpoint, params=params).json()
        if utils.get_error(r):
            sys.exit(0)
        return r

    def url(self, stream_id):
        r = self.__get_request(stream_id)
        (video_url, subtitles_url, audio_language) = extractor.download_url(r, self.config)
        if not video_url is None:
            utils.print_msg('[debug] Video:', 0)
            utils.print_msg(video_url, 4)
        if not subtitles_url is None:
            utils.print_msg('[debug] Subtitles:', 0)
            utils.print_msg(subtitles_url, 4)
        sys.exit(0)

    def download(self, stream_id):
        r = self.__get_request(stream_id)
        (video_url, subtitles_url, audio_language) = extractor.download_url(r, self.config)
        (type, id) = utils.get_download_type(r)
        (metadata, cover, thumbnail, output, path) = extractor.get_metadata(type, id, self.config)
        utils.create_folder(path)

        if self.config.get('preferences').get('download').get('subtitles'):
            if subtitles_url is None:
                utils.print_msg('ERROR: No subtitles download link available.', 1)
                sys.exit(0)

            subtitle = converter.Subtitles(os.path.join(path, output), self.config.get('preferences').get('subtitles').get('language'))
            subtitle.download(subtitles_url)
            if self.config.get('preferences').get('subtitles').get('vtt'):
                subtitle.convert('vtt')
            if self.config.get('preferences').get('subtitles').get('srt'):
                subtitle.convert('srt')
            if not self.config.get('preferences').get('subtitles').get('ass'):
                subtitles_path = os.path.join(path, '{}{}.ass'.format(output, utils.get_language_title(self.config.get('preferences').get('subtitles').get('language'))))
                if os.path.exists(subtitles_path):
                    os.remove(subtitles_path)

            utils.print_msg('[debug] Downloaded subtitles', 0)

        if self.config.get('preferences').get('image').get('cover') or self.config.get('preferences').get('video').get('attached_picture'):
            image(os.path.join(path, 'cover.jpg'), cover)
            if self.config.get('preferences').get('image').get('cover'):
                utils.print_msg('[debug] Downloaded cover', 0)

        if self.config.get('preferences').get('image').get('thumbnail'):
            image(os.path.join(path, '{}.jpg'.format(output)), thumbnail)
            utils.print_msg('[debug] Downloaded thumbnail', 0)

        if self.config.get('preferences').get('download').get('video'):
            if video_url is None:
                utils.print_msg('ERROR: No video download link available.', 1)
                sys.exit(0)

            extension = self.config.get('preferences').get('video').get('extension')
            if extension == 'mkv' or extension == 'mp4':
                index = 0
                subs = list()

                command = [
                    'ffmpeg',
                    '-hide_banner',
                    '-v', 'warning',
                    '-stats',
                    '-reconnect', '1',
                    '-reconnect_streamed', '1',
                    '-reconnect_on_network_error', '1',
                    '-max_reload', '2147483647',
                    '-m3u8_hold_counters', '2147483647',
                    '-i', '"{}"'.format(video_url)
                ]
                if extension == 'mkv':
                    if self.config.get('preferences').get('download').get('subtitles'):
                        subtitles_path = os.path.join(path, '{}{}'.format(output, utils.get_language_title(self.config.get('preferences').get('subtitles').get('language'))))
                        subtitles = self.config.get('preferences').get('subtitles')

                        if subtitles.get('ass') and os.path.exists('{}.ass'.format(subtitles_path)):
                            command += ['-i', '"{}.ass"'.format(subtitles_path)]
                            index += 1
                            subs.append(index)
                        if subtitles.get('vtt') and os.path.exists('{}.vtt'.format(subtitles_path)):
                            command += ['-i', '"{}.vtt"'.format(subtitles_path)]
                            index += 1
                            subs.append(index)
                        if subtitles.get('srt') and os.path.exists('{}.srt'.format(subtitles_path)):
                            command += ['-i', '"{}.srt"'.format(subtitles_path)]
                            index += 1
                            subs.append(index)

                if self.config.get('preferences').get('video').get('attached_picture') and extension == 'mp4':
                    command += ['-i', '"{}"'.format(os.path.join(path, 'cover.jpg'))]
                    index += 1

                command += ['-map', '0:v', '-map', '0:a']

                for i in subs:
                    command += ['-map', str(i)]

                if self.config.get('preferences').get('video').get('attached_picture') and extension == 'mp4':
                    command += ['-map', str(index)]

                command += ['-c:v:0', 'copy', '-c:a:0', 'copy', '-c:s:0', 'copy', '-metadata:s:a:0', 'language={}'.format(utils.get_ffmpeg_language(audio_language))]

                for i in subs:
                    command += ['-metadata:s:s:{}'.format(i + 1), 'language="{}"'.format(utils.get_ffmpeg_language(self.config.get('preferences').get('subtitles').get('language')))]

                if self.config.get('preferences').get('video').get('attached_picture'):
                    if extension == 'mp4':
                        command += ['-c:v:{}'.format(index), 'mjpeg', '-disposition:v:{}'.format(index), 'attached_pic']
                    elif extension == 'mkv':
                        command += ['-attach', '"{}"'.format(os.path.join(path, 'cover.jpg')), '-metadata:s:t', 'mimetype="image/jpeg"']

                if self.config.get('preferences').get('video').get('metadata'):
                    command += metadata

                command += ['"{}"'.format(os.path.join(path, '{}.{}'.format(output, extension))), '-y']

                if os.path.exists(os.path.join(path, '{}.{}'.format(output, extension))):
                    utils.print_msg('WARRING: Video already exists.', 2)
                else:
                    utils.print_msg('[debug] Download resolution: [{}]'.format(
                        self.config.get('preferences').get('video').get('resolution')), 0)
                    try:
                        os.system(' '.join(command))
                        utils.print_msg('[debug] Downloaded video', 0)
                    except KeyboardInterrupt:
                        utils.print_msg('KeyboardInterrupt', 1)
                        sys.exit(0)
                    except Exception as e:
                        utils.print_msg(e, 1)
                        sys.exit(0)

                if not self.config.get('preferences').get('image').get('cover'):
                    if os.path.exists(os.path.join(path, 'cover.jpg')):
                        os.remove(os.path.join(path, 'cover.jpg'))
            else:
                utils.print_msg('ERROR: Video extension is not supported.', 1)
                sys.exit(0)

        # sys.exit(0)

    def download_season(self, season_id, playlist_episode):
        (policy, signature, key_pair_id) = utils.get_token(self.config)
        self.config = utils.get_config()

        params = {
            'season_id': season_id,
            'Policy': policy,
            'Signature': signature,
            'Key-Pair-Id': key_pair_id,
            'locale': utils.get_locale(self.config)
        }

        endpoint = 'https://beta-api.crunchyroll.com/cms/v2{}/episodes'.format(self.config.get('configuration').get('token').get('bucket'))
        r = requests.get(endpoint, params=params).json()
        if utils.get_error(r):
            sys.exit(0)

        playlist_id = extractor.playlist(r, self.config, playlist_episode)

        if playlist_id == []:
            utils.print_msg('ERROR: The playlist is empty.', 1)
            sys.exit(0)
        else:
            for i in range(len(playlist_id)):
                utils.print_msg('[debug] Download playlist: {}/{}'.format(i + 1, len(playlist_id)), 0)
                self.download(playlist_id[i])
            utils.print_msg('[debug] The playlist has been downloaded', 0)
            sys.exit(0)
