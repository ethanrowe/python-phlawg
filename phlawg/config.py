from __future__ import absolute_import

import json
import os
from logging import config as logconf

import six

import phlawg

METRIC_HANDLER_KEY = 'phlawg_metrics_handler'
METRIC_FORMATTER_KEY = 'phlawg_metrics_formatter'
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
    LOG_FORMAT_VAR = 'PHLAWG_LOG_FORMAT'
    DATE_FORMAT_VAR = 'PHLAWG_LOG_DATE_FORMAT'
    FULL_CONF_VAR = 'PHLAWG_LOG_CONFIG'

    def __init__(self, metric_packages=()):
        self.metric_packages = self.determine_metric_packages(*metric_packages)
        self.metric_fields = self.determine_metric_fields()
        self.log_format = self.determine_log_format()
        self.log_date_format = self.determine_log_date_format()
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
            self.apply_log_format(conf)
            self.apply_log_date_format(conf)
            self.apply_metric_date_format(conf)
        conf['version'] = 1
        return conf


def from_environment(*metric_packages):
    logconf.dictConfig(EnvConf(metric_packages).config)
    return True

