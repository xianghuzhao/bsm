import os
import sys
import copy

from bsm.config.common import Common

from bsm.handler import Handler
from bsm.handler import HandlerNotFoundError

from bsm.util import is_str
from bsm.util import ensure_list
from bsm.util import safe_mkdir

from bsm.util.config import load_config
from bsm.util.config import dump_config
from bsm.util.config import ConfigError

from bsm.logger import get_logger
_logger = get_logger()


class ConfigPackageInstallError(Exception):
    pass

class ConfigPackageInstallParamError(Exception):
    pass


def _config_from_file(config_file):
    try:
        loaded_data = load_config(config_file)
        if isinstance(loaded_data, dict):
            return loaded_data
        else:
            _logger.warn('Config file is not a dict: {0}'.format(config_file))
            _logger.warn('Use empty dict instead')
    except ConfigError as e:
        return dict()

def _package_param(identifier, pkg_cfg):
    frag = identifier.split(os.sep)

    # Use the last part as default package name
    if 'name' in pkg_cfg:
        pkg_name = pkg_cfg['name']
    elif frag[-1]:
        pkg_name = frag[-1]
    else:
        _logger.error('Package name not found for {0}'.format(identifier))
        raise ConfigPackageInstallParamError

    frag = frag[:-1]

    # Use the first part as default category name
    if 'category' in pkg_cfg:
        category_name = pkg_cfg['category']
    elif len(frag) > 0:
        category_name = frag[0]
    else:
        _logger.warn('Category not specified for {0}'.format(identifier))
        raise ConfigPackageInstallParamError

    frag = frag[1:]

    # Use the middle part as default subdir
    if 'subdir' in pkg_cfg:
        subdir = pkg_cfg['subdir']
    elif frag:
        subdir = os.path.join(*frag)
    else:
        subdir = ''

    return (category_name, pkg_name, subdir)

def _step_param(config_action):
    if not config_action:
        return None, {}

    if is_str(config_action):
        return config_action, {}

    if isinstance(config_action, dict):
        if len(config_action) > 1:
            _logger.warn('More than one actions found in the install action dictionary. Will only randomly choose one!')
            _logger.debug('config_action: {0}'.format(config_action))
        handler = next(iter(config_action))
        return handler, config_action[handler]

    return None, {}


class PackageInstall(Common):
    def load(self, config_entry, config_app, config_output, config_scenario, config_release_path, config_attribute, config_release, config_release_install, config_category):
        if not ('version' in config_scenario and config_scenario['version']):
            _logger.debug('"version" not specified in config install')
            return

        reinstall = config_entry.get('reinstall', False)

        category_install = [ctg for ctg, ctg_cfg in config_category.items() if ctg_cfg['install']]

        sys.path.insert(0, config_release_path['handler_python_dir'])

        for identifier, pkg_cfg in config_release.get('package', {}).items():
            try:
                category_name, pkg_name, subdir = _package_param(identifier, pkg_cfg)
            except ConfigPackageInstallParamError:
                continue

            if category_name not in category_install:
                _logger.warn('Category "{0}" could not be installed for package "{1}"'.format(category_name, pkg_name))
                continue

            version = ensure_list(pkg_cfg.get('version', []))

            version_dir = config_category[category_name]['version_dir']
            if (not version_dir) and len(version) > 1:
                _logger.warn('Only one version could be installed when category version_dir is false')
                version = version[:1]

            if not version:
                _logger.warn('No version is specified for category({0}), package({1})'.format(category_name, pkg_name))

            for ver in version:
                self.setdefault(category_name, {})
                self[category_name].setdefault(subdir, {})
                self[category_name][subdir].setdefault(pkg_name, {})
                if ver in self[category_name][subdir][pkg_name]:
                    _logger.warn('Duplicated package found: category({0}), subdir({1}), package({2}), version({3})'.format(category_name, subdir, pkg_name, ver))
                self[category_name][subdir][pkg_name].setdefault(ver, {})
                final_config = self[category_name][subdir][pkg_name][ver]

                final_config['config_origin'] = copy.deepcopy(pkg_cfg)
                final_config['config_origin']['version'] = ver

                final_config['config'] = self.__transform_package(category_name, subdir, pkg_name, ver, pkg_cfg,
                        config_app, config_output, config_scenario, config_release_path, config_attribute, config_release, config_release_install, config_category)
                final_config['config']['name'] = pkg_name
                final_config['config']['category'] = category_name
                final_config['config']['subdir'] = subdir
                if 'version' not in final_config['config']:
                    final_config['config']['version'] = ver

                final_config['package_path'] = self.__package_path(config_category, final_config['config'])
                self.__expand_package_path(final_config['package_path']['main_dir'], final_config['config'])
                self.__expand_env(final_config['config'])

                final_config['install_status'] = self.__install_status(final_config['package_path']['status_install_file'])

                final_config['step'] = self.__install_step(config_release_install, final_config['config'], final_config['install_status'], reinstall)

        sys.path.remove(config_release_path['handler_python_dir'])

    def package_install_config(self, category, subdir, name, version):
        if category not in self or subdir not in self[category] or name not in self[category][subdir] or version not in self[category][subdir][name]:
            _logger.error('Package not found for installation: {0}.{1}.{2}.{3}'.format(category, name, subdir, version))
            raise ConfigPackageInstallError
        return self[category][subdir][name][version]

    def save_install_status(self, category, subdir, name, version):
        pkg_install_cfg = self.package_install_config(category, subdir, name, version)
        safe_mkdir(pkg_install_cfg['package_path']['status_dir'])
        dump_config(pkg_install_cfg['install_status'], pkg_install_cfg['package_path']['status_install_file'])

    def save_package_config(self, category, subdir, name, version):
        pkg_install_cfg = self.package_install_config(category, subdir, name, version)
        safe_mkdir(pkg_install_cfg['package_path']['config_dir'])
        dump_config(pkg_install_cfg['config_origin'], pkg_install_cfg['package_path']['config_file'])

    def __transform_package(self, category, subdir, name, version, pkg_cfg,
            config_app, config_output, config_scenario, config_release_path, config_attribute, config_release, config_release_install, config_category):
        param = {}
        param['operation'] = 'install'

        param['category'] = category
        param['subdir'] = subdir
        param['name'] = name
        param['version'] = version

        param['config_package'] = copy.deepcopy(pkg_cfg)
        param['config_app'] = config_app.data_copy()
        param['config_output'] = config_output.data_copy()
        param['config_scenario'] = config_scenario.data_copy()
        param['config_release_path'] = config_release_path.data_copy()
        param['config_attribute'] = config_attribute.data_copy()
        param['config_release'] = config_release.data_copy()
        param['config_category'] = config_category.data_copy()

        try:
            with Handler() as h:
                result = h.run('transform_package', param)
                if isinstance(result, dict):
                    return result
        except HandlerNotFoundError as e:
            _logger.debug('Transformer for package not found: {0}'.format(e))

        return copy.deepcopy(pkg_cfg)

    def __package_path(self, config_category, pkg_cfg):
        result = {}
        ctg_cfg = config_category[pkg_cfg['category']]
        if ctg_cfg['version_dir']:
            result['main_dir'] = os.path.join(ctg_cfg['root'], pkg_cfg['subdir'], pkg_cfg['name'], pkg_cfg['version'])
            result['work_dir'] = os.path.join(ctg_cfg['install_dir'], pkg_cfg['subdir'], pkg_cfg['name'], 'versions', pkg_cfg['version'])
            result['config_dir'] = os.path.join(ctg_cfg['config_package_dir'], pkg_cfg['subdir'], pkg_cfg['name'], 'versions', pkg_cfg['version'])
        else:
            result['main_dir'] = os.path.join(ctg_cfg['root'], pkg_cfg['subdir'], pkg_cfg['name'])
            result['work_dir'] = os.path.join(ctg_cfg['install_dir'], pkg_cfg['subdir'], pkg_cfg['name'], 'head')
            result['config_dir'] = os.path.join(ctg_cfg['config_package_dir'], pkg_cfg['subdir'], pkg_cfg['name'], 'head')
        result['config_file'] = os.path.join(result['config_dir'], 'package.yml')
        result['temp_dir'] = os.path.join(result['work_dir'], 'temp')
        result['status_dir'] = os.path.join(result['work_dir'], 'status')
        result['status_install_file'] = os.path.join(result['status_dir'], 'install.yml')
        result['log_dir'] = os.path.join(result['work_dir'], 'log')
        return result

    def __expand_package_path(self, package_main_dir, pkg_cfg):
        pkg_path = pkg_cfg.get('path', {})
        for k, v in pkg_path.items():
            pkg_path[k] = os.path.join(package_main_dir, v)

    def __expand_env(self, pkg_cfg):
        format_dict = {}
        format_dict['name'] = pkg_cfg['name']
        format_dict['category'] = pkg_cfg['category']
        format_dict['subdir'] = pkg_cfg['subdir']
        format_dict['version'] = pkg_cfg['version']
        format_dict.update(pkg_cfg.get('path', {}))

        env_prepend_path = pkg_cfg.get('env', {}).get('prepend_path', {})
        for k, v in env_prepend_path.items():
            result = []
            for i in ensure_list(v):
                result.append(i.format(**format_dict))
            env_prepend_path[k] = result

        env_append_path = pkg_cfg.get('env', {}).get('append_path', {})
        for k, v in env_append_path.items():
            result = []
            for i in ensure_list(v):
                result.append(i.format(**format_dict))
            env_append_path[k] = result

        env_set_env = pkg_cfg.get('env', {}).get('set_env', {})
        for k, v in env_set_env.items():
            env_set_env[k] = v.format(**format_dict)

        env_alias = pkg_cfg.get('env', {}).get('alias', {})
        for k, v in env_alias.items():
            env_alias[k] = v.format(**format_dict)

    def __install_status(self, status_install_file):
        return _config_from_file(status_install_file)

    def __install_step(self, config_release_install, pkg_cfg, install_status, reinstall):
        result = {}

        for step in config_release_install['steps']:
            finished = install_status.get('steps', {}).get(step, {}).get('finished', False)
            install = reinstall or not finished

            config_action = ensure_list(pkg_cfg.get('install', {}).get(step, []))

            sub_index = 0
            for cfg_action in config_action:
                handler, param = _step_param(cfg_action)
                if handler:
                    result.setdefault(step, [])
                    result[step].append({'handler': handler, 'param': param, 'install': install})
                    sub_index += 1

            if sub_index == 0:
                result.setdefault(step, [])
                result[step].append({'handler': '', 'param': {}, 'install': False})
                sub_index += 1

        return result
