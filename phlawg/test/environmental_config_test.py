import os
import functools
from nose import tools
import mock
import six

from phlawg import config

tools.assert_equal.im_class.maxDiff = None

FULL_CONF_VAR = 'PHLAWG_LOG_CONFIG'
LOG_FORMAT_VAR = 'PHLAWG_LOG_FORMAT'
DATE_FORMAT_VAR = 'PHLAWG_LOG_DATE_FORMAT'
METRIC_FIELDS_VAR = 'PHLAWG_METRIC_FIELDS'
METRIC_PACKAGES_VAR = 'PHLAWG_METRIC_PACKAGES'

ALL_VARS = [
        FULL_CONF_VAR, LOG_FORMAT_VAR, DATE_FORMAT_VAR,
        METRIC_FIELDS_VAR, METRIC_PACKAGES_VAR]

DEFAULT_FORMAT = '%(asctime)s %(levelname)s #%(process)d %(thread)d %(name)s ' \
        '%(message)s'

# The pythonjsonlogger.jsonlogger.JsonFormatter identifies the
# required JSON fields from the format string, but doesn't apply
# formatting specifications (the formatting comes from the JSONification).
# So we just identify fields of interest.
METRIC_FORMAT = '(asctime) (name) (levelname) (process) (thread) (message)'

# The default config specs for the various portions of the
# logging.  We have a "metric" and a "default" path through
# the logs, each with their own handlers.  We have a "phlawg_"
# prefix so we can isolate things.
def default_log_spec(handlers=['phlawg_default_handler'],
        level='INFO', **kw):
    return dict(kw, handlers=handlers, level=level)

def metric_log_spec(handlers=['phlawg_metrics_handler'], propagate=False,
        qualname='metrics', **kw):
    return default_log_spec(
        **dict(kw, handlers=handlers, propagate=propagate, qualname=qualname))

def default_handler_spec(formatter='phlawg_default_formatter',
        stream='ext://sys.stderr', **kw):
    if 'class' not in kw:
        kw['class'] = 'logging.StreamHandler'
    return dict(kw, formatter=formatter, stream=stream)

def metric_handler_spec(formatter='phlawg_metrics_formatter', **kw):
    return default_handler_spec(**dict(kw, formatter=formatter))

def default_formatter_spec(format=DEFAULT_FORMAT, datefmt=None, **kw):
    r = dict(kw, format=format, datefmt=datefmt)
    if not r['datefmt']:
        del r['datefmt']
    return r

def metric_formatter_spec(format=METRIC_FORMAT, **kw):
    if '()' not in kw:
        kw['()'] = 'pythonjsonlogger.jsonlogger.JsonFormatter'
    return default_formatter_spec(**dict(kw, format=format))

def default_config():
    return {
        "version": 1,
        "root": default_log_spec(),
        "loggers": {
            "metrics": metric_log_spec(),
            },
        "handlers": {
            "phlawg_default_handler": default_handler_spec(),
            "phlawg_metrics_handler": metric_handler_spec(),
            },
        "formatters": {
            "phlawg_default_formatter": default_formatter_spec(),
            "phlawg_metrics_formatter": metric_formatter_spec(),
            },
        }


def mocks(fn):
    @functools.wraps(fn)
    def wrapped(*a, **kw):
        with mock.patch.dict(os.environ):
            with mock.patch('logging.config.dictConfig') as dictconf:
                for var in ALL_VARS:
                    if var in os.environ:
                        del os.environ[var]
                return fn(*(a + (os.environ, dictconf)), **kw)
    return wrapped


def add_metric_loggers(conf, *names):
    for name in names:
        conf['loggers'][name] = metric_log_spec(qualname=name)
    return conf


# This gives a more detailed comparison on failure than the
# usual assert_called_once_with() does.
def comparable_call(logconf, expect):
    tools.assert_equal(1, len(logconf.call_args_list))
    # Further verify the shape of the call arguments.
    tools.assert_equal(
            (1, {}), (
                len(logconf.call_args_list[0][0]),
                logconf.call_args_list[0][1]))
    # Now directly compare the dicts.
    val = logconf.call_args_list[0][0][0]
    # Verify top-level keys
    tools.assert_equal(
            sorted(expect.keys()), sorted(val.keys()))
    # Verify each value
    for k in sorted(expect.keys()):
        tools.assert_equal(expect[k], val[k])


@mocks
def test_default_config(env, logconf):
    # With nothing in the environment, we should get the default specification.
    config.from_environment()
    comparable_call(logconf, default_config())


@mocks
def test_default_config_with_app_metric_names(env, logconf):
    # Default config (nothing in environment), but the app specifies
    # additional metric packages, so we expect additional metric-handled
    # loggers to result.
    config.from_environment('topguy', 'second.guy')
    expect = default_config()
    add_metric_loggers(expect, 'topguy.metrics', 'second.metrics.guy')
    # But in specifying packages, we throw away the default one
    del expect['loggers']['metrics']
    comparable_call(logconf, expect)


@mocks
def test_default_config_with_env_metric_names(env, logconf):
    # comma-separated list of packages with metrics.
    env[METRIC_PACKAGES_VAR] = 'envguy,other.guy'
    expect = default_config()
    add_metric_loggers(expect, 'envguy.metrics', 'other.metrics.guy')
    # Throw out the default, as before.
    del expect['loggers']['metrics']
    config.from_environment()
    comparable_call(logconf, expect)


@mocks
def test_default_config_with_both_metric_names(env, logconf):
    # Some packages from the environment
    env[METRIC_PACKAGES_VAR] = 'envguy,env.other,common'
    expect = default_config()
    add_metric_loggers(expect,
            'envguy.metrics', 'env.metrics.other', 'common.metrics',
            'appguy.metrics', 'app.metrics.other')
    # Again, no default
    del expect['loggers']['metrics']
    # The app specifies two names.
    config.from_environment('appguy', 'app.other')
    comparable_call(logconf, expect)

