import collections

from bsm.config.common import Common as ConfigCommon
from bsm.config.app import App as ConfigApp
from bsm.config.user import User as ConfigUser
from bsm.config.release import Release as ConfigRelease
from bsm.config.package import Package as ConfigPackage

from bsm.util import expand_path


class ConfigNotValidError(Exception):
    pass

class ConfigNoDirectModError(Exception):
    pass


class Config(collections.MutableMapping):
    def __init__(self, config_entry={}):
        self.__config = {}
        self.__config['entry'] = ConfigCommon(config_entry)


    def __getitem__(self, key):
        def method_not_found():
            raise ConfigNotValidError('No such config: {0}'.format(key))

        if key not in self.__config:
            load_method = getattr(self, '__load_' + key, method_not_found)
            load_method()

        return self.__config[key]

    def __setitem__(self, key, value):
        raise ConfigNoDirectModError('Can not modify config value directly')
        self.__config[key] = value

    def __delitem__(self, key):
        del self.__config[key]

    def __iter__(self):
        return iter(self.__config)

    def __len__(self):
        return len(self.__config)


    def __load_app(self):
        self.__config['app'] = ConfigApp()

        if 'config_app_file' in self['entry']:
            self['app'].load_from_file(expand_path(self['entry']['config_app_file']))
        if 'config_app' in self['entry']:
            self['app'].update(self['entry']['config_app'])
        if 'app_id' in self['entry']:
            self['app']['id'] = self['entry']['app_id']

        self['app'].load_app()

    def __load_user(self):
        self.__config['user'] = ConfigCommon()

        config_user_file = self['app']['config_user_file']
        if 'config_user_file' in self['entry']:
            config_user_file = self['entry']['config_user_file']
        self['user'].load_from_file(expand_path(self['entry']['config_user_file']))

        if 'config_user' in self['entry']:
            self['user'].update(self['entry']['config_user'])

    def __load_output(self):
        self.__config['output'] = ConfigCommon()

        # verbose
        self['output']['verbose'] = False
        if 'verbose' in self['user']:
            self['output']['verbose'] = self['user']['verbose']
        if 'verbose' in self['entry']:
            self['output']['verbose'] = self['entry']['verbose']

        # format
        self['output']['format'] = 'python'
        if 'output_format' in self['entry']:
            self['output']['format'] = self['entry']['output_format']

    def __load_info(self):
        self.__config['info'] = ConfigCommon()
        self['info'].load_from_file(expand_path(self['app']['user_info_file']))

    def __load_scenario(self):
        self.__config['scenario'] = ConfigScenario()
        self['scenario'].load_scenario(self['entry'], self['user'], self['app'])

    def __load_release(self):
        self.__config['release'] = ConfigRelease()
        self['release'].load_release(self['scenario'], self['user'], self['app'])


    @property
    def config(self):
        return dict(self.__config)

    @property
    def config_copy(self):
        return copy.deepcopy(dict(self.__config))
