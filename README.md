python-phlawg
=============

[![Build Status](https://travis-ci.org/ethanrowe/python-phlawg.svg)](https://travis-ci.org/ethanrowe/python-phlawg)

Python utilities for distributing metrics within log streams.

## Get configuration from environment

Formats metric log lines as JSON via the `pythonjsonlogger` pip.  Provides
reasonable system-wide logging defaults, which you can configure with environment
variables.

```python
from phlawg import config

# Configures the logging system based on environment variables, with defaults.
# Ensures metric-oriented loggers for packages specified.
config.from_environment('myapp', 'other.subsystem')
```

## Use a metric logger

Whether you configured things via the environment, or by some other means,
use the logging system to emit metrics through the log streams.

```python
import phlawg
import logging

# Determine the logger name for metrics under pacakge name "myapp"
logger_name = phlawg.to_metric_logger_name('myapp')
# Wrap the regular logger up in a MetricLogger.
metric_logger = phlawg.MetricLogger(logging.getLogger(logger_name))

# Emit metrics at a log level of INFO.
metric_logger.info(metric_a=0.6, metric_b=2)

# How about a root-level log line?
logging.getLogger().info('foo?')
```

With a default setup, this gives you STDERR output of:

```
{"asctime": "2016-05-31 18:53:41,955", "name": "myapp.metrics", "levelname": "INFO", "process": 161, "thread": 140224607975232, "message": "metric_a=0.6", "metric": "metric_a", "value": 0.6}
{"asctime": "2016-05-31 18:53:41,956", "name": "myapp.metrics", "levelname": "INFO", "process": 161, "thread": 140224607975232, "message": "metric_b=2", "metric": "metric_b", "value": 2}
2016-05-31 18:55:32,175 INFO #161 140224607975232 root foo?
```
