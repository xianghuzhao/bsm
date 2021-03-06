import os
import click

from bsm.cmd import Cmd
from bsm.util.option import parse_lines


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--verbose', '-v', is_flag=True, help='Verbose mode, also print debug information')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode, only print error information')
#@click.option('--app', '-a', type=str, help='Application ID')
#@click.option('--config-app', type=str, help='Application configuration file path')
@click.option('--app-root', type=str, hidden=True, help='Application configuration directory')
@click.option('--shell', type=str, hidden=True, help='Type of shell script')
@click.option('--config-user', type=str, help='User configuration file path')
@click.option('--output-format', type=str, default='plain', help='Output format')
@click.option('--output-env', is_flag=True, help='Also output environment')
@click.pass_context
def cli(ctx, verbose, quiet, app_root, shell, config_user, output_format, output_env):
    ctx.obj['config_entry']['verbose'] = verbose
    ctx.obj['config_entry']['quiet'] = quiet
    if config_user is not None:
        ctx.obj['config_entry']['config_user_file'] = config_user
    ctx.obj['output']['format'] = output_format
    ctx.obj['output']['env'] = output_env

    # app_root and shell could not be changed by arguments under shell command
    if 'app_root' not in ctx.obj['config_entry'] or ctx.obj['config_entry']['app_root'] is None:
        ctx.obj['config_entry']['app_root'] = app_root
    if 'shell' not in ctx.obj['output'] or ctx.obj['output']['shell'] is None:
        ctx.obj['output']['shell'] = shell


@cli.command()
@click.pass_context
def version(ctx):
    '''Display version information'''
    cmd = Cmd()
    cmd.execute('version', ctx.obj)


@cli.command()
@click.pass_context
def home(ctx):
    '''Display home directory of bsm'''
    cmd = Cmd()
    cmd.execute('home', ctx.obj)


@cli.command()
@click.option('--show-script', is_flag=True, help='Display the shell script')
@click.pass_context
def init(ctx, show_script):
    '''Initialize bsm environment'''
    cmd = Cmd()
    cmd.execute('init', ctx.obj, show_script=show_script, shell=ctx.obj['output']['shell'])


@cli.command()
@click.option('--show-script', is_flag=True, help='Display the shell script')
@click.pass_context
def exit(ctx, show_script):
    '''Exit bsm environment completely'''
    cmd = Cmd()
    cmd.execute('exit', ctx.obj, show_script=show_script, shell=ctx.obj['output']['shell'])


@cli.command()
@click.pass_context
def upgrade(ctx):
    '''Upgrade bsm to the latest version'''
    cmd = Cmd('upgrade')
    cmd.execute(ctx.obj)


@cli.command()
@click.option('--release-repo', '-t', type=str, help='Repository with release information')
@click.option('--all', '-a', 'list_all', is_flag=True, help='List all versions')
@click.option('--tag', '-g', is_flag=True, help='List tags')
@click.pass_context
def ls_remote(ctx, release_repo, list_all, tag):
    '''List all available release versions'''
    cmd = Cmd()
    ctx.obj['release_repo'] = release_repo
    cmd.execute('ls-remote', ctx.obj, list_all, tag)


@cli.command()
@click.option('--software-root', '-r', type=str, help='Local installed software root directory')
@click.pass_context
def ls(ctx, software_root):
    '''List installed release versions'''
    cmd = Cmd()
    ctx.obj['software_root'] = software_root
    cmd.execute('ls', ctx.obj)


@cli.command()
@click.option('--version', '-n', type=str, help='Release version')
@click.argument('config-type', type=str, required=False)
@click.argument('item-name', type=str, required=False)
@click.pass_context
def config(ctx, version, config_type, item_name):
    '''Display configuration, mostly for debug purpose'''
    cmd = Cmd()
    ctx.obj['config_entry']['scenario'] = version
    cmd.execute('config', ctx.obj, config_type, item_name)


@cli.command()
@click.option('--category', type=str, help='Category to be installed')
@click.option('--subdir', type=str, help='Sub directory for package')
@click.option('--version', type=str, help='Package version')
@click.argument('package', type=str)
@click.pass_context
def pkg_install(ctx, package):
    '''Install specified package'''
    cmd = Cmd()
    cmd.execute('pkg-install', ctx.obj)


@cli.command()
@click.pass_context
def ls_pkg(ctx):
    '''List all packages of the current release versions'''
    cmd = Cmd('ls-pkg')
    cmd.execute(ctx.obj)


@cli.command()
@click.option('--software-root', '-r', type=str, help='Local installed software root directory')
@click.option('--release-repo', '-t', type=str, help='Repository for retrieving release information')
@click.option('--release-source', '-i', type=str, help='Directory for retrieving release information. '
        'This will take precedence over "release-repo". Use this option only for debugging')
@click.option('--option', '-o', type=str, multiple=True, help='Options for installation')
@click.option('--reinstall', is_flag=True, help='Reinstall all packages')
@click.option('--update', is_flag=True, help='Update version information before installation')
@click.option('--no-software', is_flag=True, help='Do not install softwares, only install the release')
@click.option('--force', '-f', is_flag=True, help='Skip checking system requirements')
@click.option('--yes', '-y', is_flag=True, help='Install without confirmation')
@click.argument('version', type=str)
@click.pass_context
def install(ctx, software_root, release_repo, release_source, option, reinstall, update, no_software, force, yes, version):
    '''Install specified release version'''
    cmd = Cmd()
    ctx.obj['config_entry']['software_root'] = software_root
    ctx.obj['config_entry']['release_repo'] = release_repo
    ctx.obj['config_entry']['release_source'] = release_source
    ctx.obj['config_entry']['option'] = parse_lines(option)
    ctx.obj['config_entry']['scenario'] = version
    cmd.execute('install', ctx.obj, reinstall, update, no_software, force, yes)


@cli.command()
@click.option('--software-root', '-r', type=str, help='Local installed software root directory')
@click.option('--default', '-d', is_flag=True, help='Also set the version as default')
@click.option('--option', '-o', type=str, multiple=True, help='Options for installation')
@click.argument('version', type=str)
@click.pass_context
def use(ctx, software_root, default, option, version):
    '''Switch environment to given release version'''
    cmd = Cmd()
    ctx.obj['software_root'] = software_root
    ctx.obj['config_entry']['option'] = parse_lines(option)
    ctx.obj['config_entry']['scenario'] = version
    cmd.execute('use', ctx.obj, default=default)


@cli.command()
@click.pass_context
def clean(ctx):
    '''Clean the current release version environment'''
    cmd = Cmd('clean')
    cmd.execute(ctx.obj)


@cli.command()
@click.option('--destination', '-d', type=str, help='Directory for packing output')
@click.argument('version', type=str)
@click.pass_context
def pack(ctx, destination, version):
    '''Create tar packages for the specified release version'''
    cmd = Cmd('pack')
    cmd.execute(ctx.obj, destination=destination, version_name=version)


def main(cmd_name=None, app_root=None, output_shell=None, check_cli=False):
    '''The app_root and output_shell here take precedence over cli arguments'''
    cli(prog_name=cmd_name, obj={'config_entry': {'app_root': app_root}, 'output': {'shell': output_shell}, 'check_cli': check_cli})
