from cepcenv.config.config_release import ConfigReleaseTransformError
from cepcenv.install import Install as CepcenvInstall

from cepcenv.logger import get_logger
_logger = get_logger()

class Install(object):
    def execute(self, config, config_version, source, force):
        transformer = []
        if source:
            transformer = [source + '_source']

        result = False
        obj = CepcenvInstall(config, config_version, transformer)
        try:
            result = obj.run(force)
        except ConfigReleaseTransformError as e:
            _logger.critical('Install source error: {0}'.format(source))

        if result:
            _logger.info('-'*16)
            _logger.info('Installation finished successfully')
            _logger.info('Version: {0}'.format(config_version.get('version')))
            _logger.info('Software root: {0}'.format(config_version.get('software_root')))
