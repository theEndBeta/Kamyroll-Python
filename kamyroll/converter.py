import logging
import os
import sys
import requests
import kamyroll.utils as utils

log = logging.getLogger(__name__)


class Subtitles:

    def __init__(self, output, language):
        self.output = output
        self.language = language

    def download(self, subtitles_url):
        output = '{}{}.{}'.format(self.output, utils.get_language_title(self.language), 'ass')
        if os.path.exists(output):
            os.remove(output)

        r = requests.get(subtitles_url)
        file = open(output, 'wb')
        file.write(r.content)
        file.close()

    def convert(self, extension):
        output = '{}{}.{}'.format(self.output, utils.get_language_title(self.language), extension)
        if os.path.exists('{}{}.{}'.format(self.output, utils.get_language_title(self.language), 'ass')):
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
