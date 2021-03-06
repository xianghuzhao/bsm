import collections
import copy

from bsm.util import expand_path


class ConfigNotValidError(Exception):
    pass

class ConfigNoDirectModError(Exception):
    pass


from bsm.config.common import Common as ConfigCommon
from bsm.config.app import App as ConfigApp
from bsm.config.env import Env as ConfigEnv
from bsm.config.scenario import Scenario as ConfigScenario
from bsm.config.release_path import ReleasePath as ConfigReleasePath
from bsm.config.release import Release as ConfigRelease
from bsm.config.category import Category as ConfigCategory
from bsm.config.package_install import PackageInstall as ConfigPackageInstall
from bsm.config.packages import Packages as ConfigPackages

from bsm.handler import Handler
from bsm.handler import HandlerNotFoundError

from bsm.logger import get_logger
_logger = get_logger()


class Config(collections.MutableMapping):
    def __init__(self, config_entry={}, initial_env=None):
        self.__initial_env = initial_env
        self.reset(config_entry)

    def reset(self, config_entry=None):
        if config_entry is None and 'entry' in self:
            config_entry = self['entry']
        self.__config = {}
        self.__config['entry'] = ConfigCommon()
        for k, v in config_entry.items():
            if v is not None:
                self['entry'][k] = v


    # This method implements the lazy load of configs
    # Configs are only loaded when accessed
    def __getitem__(self, key):
        def method_not_found():
            raise ConfigNotValidError('No such config: {0}'.format(key))

        if key not in self.__config:
            load_method = getattr(self, '_Config__load_' + key, method_not_found)
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
        self['app'].load(self['entry'].get('app_root', ''))

    def __load_example(self):
        self.__config['example'] = ConfigCommon()
        self['example']['path'] = self['app']['example_config_user']
        try:
            self['example']['content'] = open(self['app']['example_config_user']).read()
        except Exception as e:
            _logger.warn('Open user config example failed: %s' % e)
            self['example']['content'] = ''

    def __load_env(self):
        self.__config['env'] = ConfigEnv()
        self['env'].load(self.__initial_env, self['app']['env_prefix'])

    def __load_user(self):
        self.__config['user'] = ConfigCommon()

        config_user_file = self['app']['config_user_file']
        if 'config_user_file' in self['entry']:
            config_user_file = self['entry']['config_user_file']
        self['user'].load_from_file(expand_path(config_user_file))

        if 'config_user' in self['entry']:
            self['user'] = copy.deepcopy(self['entry']['config_user'])

    def __load_output(self):
        self.__config['output'] = ConfigCommon()

        # verbose
        self['output']['verbose'] = False
        if 'verbose' in self['user']:
            self['output']['verbose'] = self['user']['verbose']
        if 'verbose' in self['entry']:
            self['output']['verbose'] = self['entry']['verbose']

        # quiet
        self['output']['quiet'] = False
        if 'quiet' in self['user']:
            self['output']['quiet'] = self['user']['quiet']
        if 'quiet' in self['entry']:
            self['output']['quiet'] = self['entry']['quiet']

    def __load_info(self):
        self.__config['info'] = ConfigCommon()
        self['info'].load_from_file(expand_path(self['app']['config_info_file']))

    def __load_scenario(self):
        self.__config['scenario'] = ConfigScenario()
        self['scenario'].load(self['entry'], self['app'], self['env'], self['user'])

    def __load_release_path(self):
        self.__config['release_path'] = ConfigReleasePath()
        self['release_path'].load(self['scenario'], self['app']['release_work_dir'])

    def __load_release_status(self):
        self.__config['release_status'] = ConfigCommon()
        self['release_status'].load_from_file(self['release_path']['status_file'])

    def __load_attribute(self):
        self.__config['attribute'] = ConfigCommon()
        if 'handler_python_dir' not in self['release_path']:
            return
        try:
            with Handler(self['release_path']['handler_python_dir']) as h:
                self['attribute'].update(h.run('attribute'))
        except HandlerNotFoundError:
            _logger.debug('Handler for attribute not found')

    # Release defined options, for display purpose only
    def __load_option_list(self):
        self.__config['option_list'] = ConfigCommon()
        if 'handler_python_dir' not in self['release_path']:
            return
        try:
            with Handler(self['release_path']['handler_python_dir']) as h:
                self['option_list'].update(h.run('option'))
        except HandlerNotFoundError:
            _logger.debug('Handler for option not found')

    def __load_release(self):
        self.__config['release'] = ConfigRelease()
        self['release'].load(self['app'], self['scenario'], self['release_path'], self['attribute'])

    def __load_category(self):
        self.__config['category'] = ConfigCategory()
        self['category'].load(self['app'], self['scenario'], self['release'])

    def __load_package_install(self):
        self.__config['package_install'] = ConfigPackageInstall()
        self['package_install'].load(self['app'], self['scenario'], self['release_path'], self['attribute'], self['release'], self['category'])

    def __load_packages(self):
        self.__config['packages'] = ConfigPackages()
        self['packages'].load(self['app'], self['env'], self['release'], self['category'])


    def config(self, config_type):
        if isinstance(self[config_type], ConfigCommon):
            return self[config_type].data
        return self[config_type]

    @property
    def data(self):
        return {k: self.config(k) for k in self}
