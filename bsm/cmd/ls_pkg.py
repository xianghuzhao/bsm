import click

from bsm.env import Env

class LsPkg(object):
    def execute(self, config, config_version):
        env = Env()

        for name, info in env.package_info.items():
            click.echo('{name} @ {version} : {category} - {path}'.format(name=name, **info))
