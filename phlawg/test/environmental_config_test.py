import os
import json
from nose import tools
import mock
import six

from phlawg import config

FULL_CONF_VAR = 'PHLAWG_LOG_CONFIG'
LOG_FORMAT_VAR = 'PHLAWG_LOG_FORMAT'
DATE_FORMAT_VAR = 'PHLAWG_LOG_DATE_FORMAT'
METRIC_FIELDS_VAR = 'PHLAWG_METRIC_FIELDS'
METRIC_PACKAGES_VAR = 'PHLAWG_METRIC_PACKAGES'
METRIC_DATE_FORMAT_VAR = 'PHLAWG_METRIC_DATE_FORMAT'
LOG_LEVEL_VAR = 'PHLAWG_LOG_LEVEL'
METRIC_LEVEL_VAR = 'PHLAWG_METRIC_LEVEL'

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
    @six.wraps(fn)
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
def test_log_level(env, logconf):
    env[LOG_LEVEL_VAR] = str(mock.Mock(name='SomeLogLevelName'))
    config.from_environment()
    expect = default_config()
    expect["handlers"]["phlawg_default_handler"]["level"] = env[LOG_LEVEL_VAR]
    comparable_call(logconf, expect)

@mocks
def test_metric_level(env, logconf):
    env[METRIC_LEVEL_VAR] = str(mock.Mock(name='SomeLogLevelName'))
    config.from_environment()
    expect = default_config()
    expect["handlers"]["phlawg_metrics_handler"]["level"] = \
            env[METRIC_LEVEL_VAR]
    comparable_call(logconf, expect)

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


@mocks
def test_metric_fields_var(env, logconf):
    fields = ['some', 'other', 'fields']
    # We express the desired fields in a comma-separated list.
    env[METRIC_FIELDS_VAR] = ','.join(fields)
    expect = default_config()
    # And in the log formatter, the JsonFormatter just needs to see
    # the field names in parentheses.
    expect['formatters']['phlawg_metrics_formatter']['format'] = \
            ' '.join('(%s)' % fld for fld in fields)
    config.from_environment()
    comparable_call(logconf, expect)


@mocks
def test_log_format_var(env, logconf):
    format_str = str(mock.Mock(name='AFakeLogFormatString'))
    env[LOG_FORMAT_VAR] = format_str
    expect = default_config()
    expect['formatters']['phlawg_default_formatter']['format'] = format_str
    config.from_environment()
    comparable_call(logconf, expect)


@mocks
def test_date_format_var(env, logconf):
    fmt = str(mock.Mock(name='AFakeDateFormatString'))
    env[DATE_FORMAT_VAR] = fmt
    expect = default_config()
    expect['formatters']['phlawg_default_formatter']['datefmt'] = fmt
    config.from_environment()
    comparable_call(logconf, expect)


@mocks
def test_metric_date_format_var(env, logconf):
    fmt = str(mock.Mock(name='AnotherFakeDateFormatString'))
    env[METRIC_DATE_FORMAT_VAR] = fmt
    expect = default_config()
    expect['formatters']['phlawg_metrics_formatter']['datefmt'] = fmt
    config.from_environment()
    comparable_call(logconf, expect)


def mock_dict():
    return {
            str(mock.Mock(name='AKey')): str(mock.Mock(name='AValue'))}


def override_case(spec):
    def wrapper(fn):
        @six.wraps(fn)
        @mocks
        def wrapped(env, logconf):
            # Put the specification into the variable as JSON.
            env[FULL_CONF_VAR] = json.dumps(spec)
            # Build expectation from JSON (so we get a copy).
            expect = json.loads(env[FULL_CONF_VAR])
            expect, packages = fn(expect, env, logconf)
            # Apply the configuration and verify our expectation.
            config.from_environment(*packages)
            comparable_call(logconf, expect)
        return wrapped
    return wrapper

@override_case({
    "loggers": {
        "metrics": mock_dict(),
        },
    "handlers": {
        "phlawg_metrics_handler": mock_dict(),
        },
    "formatters": {
        "phlawg_metrics_formatter": mock_dict(),
        },
    })
def test_override_full_definition(spec, env, logconf):
    # If all the metrics needed have loggers, and
    # metric handler and formatter are both present,
    # we accept the override JSON definition as-is.
    
    # We expect it to add a version for us.
    spec["version"] = 1
    return spec, ()


@override_case({
    "loggers": {
        # It'll accept this
        "fromenv.metrics.defined": mock_dict(),
        # And this.
        "fromapp.metrics.defined": mock_dict(),
        },
    "handlers": {
        "phlawg_metrics_handler": mock_dict(),
        },
    "formatters": {
        "phlawg_metrics_formatter": mock_dict(),
        },
    })
def test_override_with_metric_names(spec, env, logconf):
    # In this case, we check that it adds a metric logger
    # for one that was missing, but leaves the ones it
    # finds alone.

    # Env-level metrics packages requested.
    env[METRIC_PACKAGES_VAR] = 'fromenv.defined,fromenv.undefined'

    # These guys will be added by the system based on the metrics
    # packages we requested.
    for name in ("fromenv.metrics.undefined",
                 "fromapp.metrics.undefined"):
        spec["loggers"][name] = metric_log_spec(qualname=name)

    # And of course we expect version 1.
    spec["version"] = 1

    # App-level metrics packages requested
    return spec, ("fromapp.defined", "fromapp.undefined")


@override_case({
    "loggers": {
        "metrics": mock_dict(),
        },
    "handlers": {
        "phlawg_metrics_handler": mock_dict(),
        "other_metrics_handler": mock_dict(),
        },
    "formatters": {
        "some_formtter": mock_dict(),
        },
    })
def test_override_with_metric_handler(spec, env, logconf):
    # We should see that it accepts the given metrics handler,
    # but provides the standard metrics formatter.
    spec["formatters"]["phlawg_metrics_formatter"] = metric_formatter_spec()
    spec["version"] = 1
    return spec, ()


@override_case({
    "loggers": {
        "metrics": mock_dict(),
        },
    "handlers": {
        "other_handler": mock_dict(),
        },
    "formatters": {
        "phlawg_metrics_formatter": mock_dict(),
        "other_formatter": mock_dict(),
        },
    })
def test_override_with_metric_formatter(spec, env, logconf):
    # We should see that it accepts the given metric formatter,
    # but adds the standard metrics handler.
    spec["handlers"]["phlawg_metrics_handler"] = metric_handler_spec()
    spec["version"] = 1
    return spec, ()


@override_case({
    "loggers": {
        "some_logger": mock_dict(),
        "other_logger": mock_dict(),
        },
    "handlers": {
        "some_handler": mock_dict(),
        "other_handler": mock_dict(),
        },
    "formatters": {
        "some_formatter": mock_dict(),
        "other_formatter": mock_dict(),
        },
    })
def test_override_with_no_metrics(spec, env, logconf):
    # In this case, the override configuration doesn't deal with our metrics
    # structures at all, so we expect the system to provide for them.
    spec["loggers"]["metrics"] = metric_log_spec()
    spec["handlers"]["phlawg_metrics_handler"] = metric_handler_spec()
    spec["formatters"]["phlawg_metrics_formatter"] = metric_formatter_spec()
    spec["version"] = 1
    return spec, ()

