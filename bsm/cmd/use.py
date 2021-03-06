from bsm.cmd import Base

from bsm.logger import get_logger
_logger = get_logger()

class Use(Base):
    def execute(self, default=False):
        return self._bsm.use()


        obj = BsmUse(config_user, config_version, config_release)

        missing_pkg, install_cmd, pkg_install_name = obj.check()
        if missing_pkg:
            _logger.warn('Missing package(s): {0}'.format(', '.join(missing_pkg)))
            _logger.warn('Suggest installing with the following command:')
            _logger.warn(' '.join(install_cmd+pkg_install_name))

        set_env, unset_env = obj.run()

        shell.clear_script()
        for e in unset_env:
            shell.unset_env(e)
        for k, v in set_env.items():
            shell.set_env(k, v)

        if default:
            info = Info()
            version_name = config_version.get('version_name')
            if version_name:
                info.set_default_version(version_name)
            else:
                _logger.warn('Could not setup default version')

        click.echo(shell.script, nl=False)
