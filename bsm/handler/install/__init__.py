from bsm.loader import load_relative
from bsm.loader import LoadError

from bsm.handler import HandlerNotAvailableError

def run(action, param):
    try:
        run_func = load_relative('install.'+action, 'run')
    except LoadError as e:
        raise HandlerNotAvailableError

    if not callable(run_func):
        raise HandlerNotAvailableError

    return run_func(param)
