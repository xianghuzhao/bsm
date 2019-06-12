from bsm.config.common import Common

from bsm.logger import get_logger
_logger = get_logger()


class Option(Common):
    def __init__(self, config_user, config_entry, config_env, config_option_list):
        super(Option, self).__init__()

        self.__update_option(config_user)

        if 'scenario' in config_entry and config_entry['scenario']:
            scenario = config_entry['scenario']

            if 'scenario' in config_user and scenario in config_user['scenario']:
                self.__update_option(config_user['scenario'][scenario])

        self.__update_option(config_env)

        self.__update_option(config_entry)

        self.__check_option(config_option_list)

    def __update_option(self, config_container):
        if 'option' not in config_container:
            return

        option = config_container['option']
        if isinstance(option, dict):
            self.update(option)

    def __check_option(self, config_option_list):
        for k, v in self.items():
            if k not in config_option_list:
                _logger.warn('Option "{0}" is not in the option list'.format(k))