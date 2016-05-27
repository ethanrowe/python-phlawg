from __future__ import absolute_import

import os
from logging import config as logconf

import six

import phlawg

METRIC_HANDLER_KEY = 'phlawg_metrics_handler'

def metric_logger_specification(name):
    return {"qualname": name,
            "level": "INFO",
            "propagate": False,
            "handlers": [METRIC_HANDLER_KEY],
            }

DEFAULT_CONFIG = {
        'loggers': {},
        'root': {
            'level': 'INFO',
            'handlers': ['phlawg_default_handler'],
            },
        'formatters': {
            'phlawg_metrics_formatter': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '(asctime) (name) (levelname) (process) (thread) (message)',
                },
            'phlawg_default_formatter': {
                'format': '%(asctime)s %(levelname)s #%(process)d %(thread)d %(name)s %(message)s'
                },
            },
        'handlers': {
            'phlawg_metrics_handler': {
                'formatter': 'phlawg_metrics_formatter',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stderr',
                },
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

class EnvConf(object):
    METRIC_PACKAGES_VAR = 'PHLAWG_METRIC_PACKAGES'
    METRIC_FIELDS_VAR = 'PHLAWG_METRIC_FIELDS'
    LOG_FORMAT_VAR = 'PHLAWG_LOG_FORMAT'
    DATE_FORMAT_VAR = 'PHLAWG_LOG_DATE_FORMAT'
    FULL_CONF_VAR = 'PHLAWG_LOG_CONFIG'

    def __init__(self, metric_packages=()):
        self.metric_packages = self.determine_metric_packages(*metric_packages)

    def determine_metric_packages(self, *app_metric_packages):
        print "From environment:", env_list(self.METRIC_PACKAGES_VAR)
        print "From app:", app_metric_packages
        app_metric_packages += tuple(env_list(self.METRIC_PACKAGES_VAR))
        if app_metric_packages:
            return [phlawg.to_metric_logger_name(name)
                    for name in app_metric_packages]
        return ['metrics']


    def apply_metric_loggers(self, conf):
        for name in self.metric_packages:
            conf["loggers"][name] = metric_logger_specification(name)

    @property
    def config(self):
        conf = dict((k, dict(v)) for k, v in six.iteritems(DEFAULT_CONFIG))
        self.apply_metric_loggers(conf)
        conf['version'] = 1
        return conf


def from_environment(*metric_packages):
    logconf.dictConfig(EnvConf(metric_packages).config)
    return True

