import click

from bsm.env import Env

class Clean(object):
    def execute(self, config_version, shell):
        shell.clear_script()

        env = Env()
        env.clean()
        set_env, unset_env = env.env_change()

        for e in unset_env:
            shell.unset_env(e)
        for k, v in set_env.items():
            shell.set_env(k, v)

        click.echo(shell.script, nl=False)
