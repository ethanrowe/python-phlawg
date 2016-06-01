"""
Functions for configuring the logging system in phlawg-friendly ways.
"""

from __future__ import absolute_import

import json
import os
from logging import config as logconf

import six

import phlawg

METRIC_HANDLER_KEY = 'phlawg_metrics_handler'
METRIC_FORMATTER_KEY = 'phlawg_metrics_formatter'
LOG_HANDLER_KEY = 'phlawg_default_handler'
LOG_FORMATTER_KEY = 'phlawg_default_formatter'

DEFAULT_METRIC_FIELDS = (
    'asctime', 'name', 'levelname', 'process', 'thread', 'message')

def metric_logger_specification(name):
    return {"qualname": name,
            "level": "INFO",
            "propagate": False,
            "handlers": [METRIC_HANDLER_KEY],
            }

def metric_formatter_specification():
    return {'()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': metric_field_format(DEFAULT_METRIC_FIELDS),
            }

def metric_handler_specification():
    return {'formatter': 'phlawg_metrics_formatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            }

def metric_field_format(fields):
    return ' '.join('(%s)' % fld for fld in fields)


def default_config():
    return {
        'loggers': {},
        'root': {
            'level': 'INFO',
            'handlers': ['phlawg_default_handler'],
            },
        'formatters': {
            'phlawg_metrics_formatter': metric_formatter_specification(),
            'phlawg_default_formatter': {
                'format': '%(asctime)s %(levelname)s #%(process)d %(thread)d %(name)s %(message)s'
                },
            },
        'handlers': {
            'phlawg_metrics_handler': metric_handler_specification(),
            'phlawg_default_handler': {
                'formatter': 'phlawg_default_formatter',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr',
                },
            },
        }

def env_list(variable):
    val = os.getenv(variable)
    return val.split(',') if val else []


def env_var(variable, default=None, handler=lambda x: x):
    val = os.getenv(variable)
    if val is not None and val != '':
        return handler(val)
    return default


class EnvConf(object):
    METRIC_PACKAGES_VAR = 'PHLAWG_METRIC_PACKAGES'
    METRIC_FIELDS_VAR = 'PHLAWG_METRIC_FIELDS'
    METRIC_DATE_FORMAT_VAR = 'PHLAWG_METRIC_DATE_FORMAT'
    METRIC_LEVEL_VAR = 'PHLAWG_METRIC_LEVEL'
    LOG_FORMAT_VAR = 'PHLAWG_LOG_FORMAT'
    DATE_FORMAT_VAR = 'PHLAWG_LOG_DATE_FORMAT'
    LOG_LEVEL_VAR = 'PHLAWG_LOG_LEVEL'
    FULL_CONF_VAR = 'PHLAWG_LOG_CONFIG'

    def __init__(self, metric_packages=()):
        self.metric_packages = self.determine_metric_packages(*metric_packages)
        self.metric_fields = self.determine_metric_fields()
        self.metric_level = self.determine_metric_level()
        self.log_format = self.determine_log_format()
        self.log_date_format = self.determine_log_date_format()
        self.log_level = self.determine_log_level()
        self.metric_date_format = self.determine_metric_date_format()
        self.specification = self.determine_specification()


    @classmethod
    def determine_metric_packages(cls, *app_metric_packages):
        app_metric_packages += tuple(env_list(cls.METRIC_PACKAGES_VAR))
        if app_metric_packages:
            return [phlawg.to_metric_logger_name(name)
                    for name in app_metric_packages]
        return ['metrics']

    @classmethod
    def determine_specification(cls):
        val = env_var(cls.FULL_CONF_VAR, default=None, handler=json.loads)
        if val:
            cls.ensure_metric_handler(val)
            cls.ensure_metric_formatter(val)
        return val


    @classmethod
    def ensure_metric_handler(cls, conf):
        if METRIC_HANDLER_KEY not in conf["handlers"]:
            conf["handlers"][METRIC_HANDLER_KEY] = \
                    metric_handler_specification()

    @classmethod
    def ensure_metric_formatter(cls, conf):
        if METRIC_FORMATTER_KEY not in conf["formatters"]:
            conf["formatters"][METRIC_FORMATTER_KEY] = \
                    metric_formatter_specification()

    @classmethod
    def determine_metric_fields(cls):
        return env_list(cls.METRIC_FIELDS_VAR)

    @classmethod
    def determine_metric_level(cls):
        return env_var(cls.METRIC_LEVEL_VAR)

    @classmethod
    def determine_log_level(cls):
        return env_var(cls.LOG_LEVEL_VAR)

    @classmethod
    def determine_log_format(cls):
        return env_var(cls.LOG_FORMAT_VAR)

    @classmethod
    def determine_log_date_format(cls):
        return env_var(cls.DATE_FORMAT_VAR)

    @classmethod
    def determine_metric_date_format(cls):
        return env_var(cls.METRIC_DATE_FORMAT_VAR)

    def apply_metric_loggers(self, conf):
        for name in self.metric_packages:
            if name not in conf["loggers"]:
                conf["loggers"][name] = metric_logger_specification(name)

    def apply_metric_fields(self, conf):
        if self.metric_fields:
            conf["formatters"][METRIC_FORMATTER_KEY]['format'] = (
                    metric_field_format(self.metric_fields))

    def apply_metric_level(self, conf):
        if self.metric_level:
            conf["handlers"][METRIC_HANDLER_KEY]['level'] = self.metric_level

    def apply_log_level(self, conf):
        if self.log_level:
            conf["handlers"][LOG_HANDLER_KEY]['level'] = self.log_level

    def apply_log_format(self, conf):
        if self.log_format:
            conf["formatters"][LOG_FORMATTER_KEY]['format'] = self.log_format

    def apply_log_date_format(self, conf):
        if self.log_date_format:
            conf["formatters"][LOG_FORMATTER_KEY]['datefmt'] = \
                    self.log_date_format

    def apply_metric_date_format(self, conf):
        if self.metric_date_format:
            conf["formatters"][METRIC_FORMATTER_KEY]['datefmt'] = \
                    self.metric_date_format


    @property
    def config(self):
        conf = self.specification if self.specification else default_config()
        self.apply_metric_loggers(conf)
        if not self.specification:
            self.apply_metric_fields(conf)
            self.apply_metric_level(conf)
            self.apply_log_level(conf)
            self.apply_log_format(conf)
            self.apply_log_date_format(conf)
            self.apply_metric_date_format(conf)
        conf['version'] = 1
        return conf


def from_environment(*metric_packages):
    """
    Configures python's logging system based on environment variables.

    Supported environment variables:
        ``PHLAWG_METRIC_FIELDS``: Comma-separated list of log record field names
            to include in the JSON metric output.

        ``PHLAWG_METRIC_PACKAGES``: Python package/subpackage/module names under
            which metrics are expected to be logged.  Loggers with suitable
            qualnames, using the "phlawg_metric_handler" handler, will be added
            to the configuration.  Names will be converted to metric logger names
            based on :func:`phlawg.to_metric_logger_name`.

        ``PHLAWG_METRIC_DATE_FORMAT``: The date formatting string to use for the
            time field within metric logs.

        ``PHLAWG_METRIC_LEVEL``: The logging level name to use for metric logs.

        ``PHLAWG_LOG_FORMAT``: The log format string to use for regular log lines.

        ``PHLAWG_LOG_DATE_FORMAT``: The date formatting string to use for the
            time field within regular logs.

        ``PHLAWG_LOG_LEVEL``: The logging level name to use for regular logs.

        ``PHLAWG_LOG_CONFIG``: a full log configuration dictionary as would be
            passed to :func:`logging.config.dictConfig`, encoded as JSON.  Note
            that this will be subject to some modification; the
            "phlawg_metric_handler" and "phlawg_metric_formatter" structures will
            be ensured, with default definitions if not already present.  Any
            metric logger names determined via metric package name resolution
            will be ensured as well within the "loggers" dict.

    Defaults are provided for everything such that no environmental configuration
    is strictly required in order to use this and get a sensible behavior.

    Metric package names can be expressed both in the ``PHLAWG_METRIC_PACKAGES``
    environment variable and in the call to this function as positional parameters;
    these will be merged, and all subject to :func:`phlawg.to_metric_logger_name`
    in determining the logger/qualname.

    Metric loggers will use the :class:`pythonjsonlogger.jsonlogger.JsonFormatter`
    formatter to express themselves as JSON dictionaries in the logstream.

    Logging levels are applied to the log handlers, not the loggers themselves.

    All logs will go to STDERR by default.

    Returns ``True``.
    """
    logconf.dictConfig(EnvConf(metric_packages).config)
    return True

