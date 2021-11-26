import logging
import os
import sys
import requests
import kamyroll.utils as utils

log = logging.getLogger(__name__)


class Subtitles:

    def __init__(self, output: str, language: str):
        self.output = output
        self.language = language

    def download(self, subtitles_url: str, ext: str):
        output = '{}.{}.{}'.format(self.output, self.language, ext)
        if os.path.exists(output):
            os.remove(output)

        r = requests.get(subtitles_url)
        with open(output, 'wb') as file:
            file.write(r.content)

    def convert(self, extension: str):
        output = '{}.{}.{}'.format(self.output, self.language, extension)
        if os.path.exists('{}.{}.{}'.format(self.output, self.language, 'ass')):
            if os.path.exists(output):
                os.remove(output)

            command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', '"{}{}.{}"'.format(self.output, utils.get_language_title(self.language), 'ass'), '"{}"'.format(output), '-n']
            try:
                os.system(' '.join(command))
            except KeyboardInterrupt:
                log.error('KeyboardInterrupt')
                sys.exit(0)
            except Exception as e:
                log.error(e)
                sys.exit(0)
        else:
            log.warning('Source subtitle file is unavailable.')
