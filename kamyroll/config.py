from dataclasses import dataclass
import json
import logging
import os
import sys
from typing import Type, TypeVar, Union

log = logging.getLogger(__name__)

DEFAULT_CONFIG_LOC = os.path.join(os.getcwd(), 'config', 'kamyroll.json')

KamyConf = TypeVar('KamyConf', bound='KamyrollConf')

@dataclass()
class KamyrollConf:
    _path: str
    configuration: dict
    preferences: dict


    @classmethod
    def load(cls: Type[KamyConf], config_file: str = DEFAULT_CONFIG_LOC) -> KamyConf:
        """Load a KamyrollConf from a json config file
        """
        log.debug("Reading config file: %s", config_file)
        if os.path.exists(config_file):
            config_json = {}
            with open(config_file, 'r') as file:
                config_json = json.load(file)
                log.debug("Reading config: %s", config_json)
            return cls(
                _path = config_file,
                configuration=config_json.get('configuration', {}),
                preferences=config_json.get('preferences', {}),
            )
        else:
            log.error('Configuration file not found: ', config_file)
            sys.exit(0)


    def _to_json_dict(self) -> dict:
        """Return self as dictionary ready for dumping to external config file"""
        return {
            'configuration': self.configuration,
            'preferences': self.preferences,
        }


    def save(self) -> None:
        """Write self back to json config file"""
        log.info("Writing config to %s", self._path)
        with open(self._path, 'w', encoding='utf8') as file:
            file.write(json.dumps(self._to_json_dict(), indent=4, sort_keys=False, ensure_ascii=False))

    def preference(self, *args: str) -> Union[str, bool]:
        """Recusively get preference entry as str"""
        level = self._get_entry(self.preferences, *args)
        if not isinstance(level, (str, bool)):
            return str(level)
        return level


    def _get_entry(self, segment: dict, *args: str):
        log.debug("args: %s\nsegment: %s", '.'.join(args), segment)
        level = segment
        for entry in args:
            if entry not in level:
                raise KeyError('Entry not found: `{}`'.format('.'.join(args)))
            level = level[entry]
        return level


    def config(self, *args: str) -> str:
        """Recusively get configuration entry as bool or str"""
        level = self._get_entry(self.configuration, *args)
        return str(level)

    def set_preference(self, val: Union[str, bool, dict], *args) -> None:
        """Set a preference"""
        self._set_entry(self.preferences, val, *args)


    def set_conf(self, val: Union[str, dict], *args) -> None:
        """Set a config value"""
        self._set_entry(self.configuration, val, *args)


    def _set_entry(self, segment: dict, val: Union[str, bool, dict], *args: str) -> None:
        log.debug("value: %s\nargs: %s\nsegment: %s", val, '.'.join(args), segment)
        level = segment
        for entry in args[:-1]:
            if entry not in level:
                raise KeyError('Entry not found: `{}`'.format('.'.join(args)))
            level = level[entry]
        level[args[-1]] = val
