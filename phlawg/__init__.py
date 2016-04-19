import six

class MetricLogger(object):
    """A wrapper class for logging.Loggers for metric propagation through log streams.

    A MetricLogger may be used mostly like a traditional logging.Logger, as it has the
    same event emission methods as the logging.Logger it wraps (methods either corresponding
    to a logging level name or the generic `log` method).

    Metrics are expressed as keyword parameters, with a keyword being a simple name,
    and the corresponding value being the numeric metric value.

    Each metric results in its own log record at the specified level, transmitted through
    the wrapped logger, with the metric being expressed both as a simple "key=value" string
    in the log message, and with the "extra" dictionary having 'metric' and 'value' members.
    Consequently, every metric can be extracted from the log lines provided those log lines
    capture either the "extra" dictionary structure or the message field.

    While the MetricLogger does not enforce this convention, the intended use is for the
    metric keys to be thought of as simple names within an overall namespace, determined
    by the name of the logger itself.  So, I might do something like this:

            logger = phlawg.MetricLogger(logging.getLogger('foo.metrics.bar'))
            logger.info(metric_a=0, metric_b=-6.5)

    And I would logically think of the metrics as "foo.metrics.bar.metric_a" and
    "foo.metrics.bar.metric_b".

    Extend MetricLogger and override `message` and or `extra` to control how the log lines
    are formatted.
    """

    def __init__(self, logger):
        """Wrap a logging.Logger-like `logger` with metrics-emitting behaviors."""
        self.logger = logger

    def message_and_extra(self, metrics):
        """For each metric/value pair in `metrics`, yields the log message and 'extra' dictionary."""
        for name, value in six.iteritems(metrics):
            yield self.message(name, value), self.extra(name, value)

    def message(self, name, value):
        """Formats and returns a log message string for the metric name,value pair"""
        return "%s=%s" % (name, value)

    def extra(self, name, value):
        """Returns a dictionary suitable for use as the log's `extra` keyword parameter for the
        name,value metric pair."""
        return {'metric': name, 'value': value}


    def log(self, level, **metrics):
        """Log the metrics expressed in keyword arguments using the specified log `level`."""
        for msg, xtra in self.message_and_extra(metrics):
            self.logger.log(level, msg, extra=xtra)


    def _level_emit(self, emitter, metrics):
        for msg, xtra in self.message_and_extra(metrics):
            emitter(msg, extra=xtra)

    def critical(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.CRITICAL level."""
        return self._level_emit(self.logger.critical, metrics)

    def debug(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.DEBUG level."""
        return self._level_emit(self.logger.debug, metrics)

    def error(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.ERROR level."""
        return self._level_emit(self.logger.error, metrics)

    def fatal(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.CRITICAL level."""
        return self._level_emit(self.logger.fatal, metrics)

    def info(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.INFO level."""
        return self._level_emit(self.logger.info, metrics)

    def warn(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.WARN level."""
        return self._level_emit(self.logger.warn, metrics)

    def warning(self, **metrics):
        """Log the metrics expressed in keyword arguments at logging.WARN level."""
        return self._level_emit(self.logger.warning, metrics)


def to_metric_logger_name(logger_or_name):
    """Translates a `logger_or_name` to a standardized metrics-oriented logger name.

    If `logger_or_name` is a `logging.Logger`-like object, its `name` is used as the
    original name string; otherwise, `logger_or_name` is assumed to be a logger name
    string.

    The metrics logger name translation rules attempt to work well with the hierarchical
    naming of loggers enforced by the `logging` subsystem.  It will attempt to preserve
    the base package name of `logger_name` ("foo", in the case of a logger name "foo.blah").
    But it will attempt to put "metrics" into the name as the second level, such that it is
    easy within your application logging configuration to handle metrics as a separate stream
    from standard logs.

    Thus "foo" would go to "foo.metrics", while "foo.bar.baz" would go to "foo.metrics.bar.baz".

    If the logger name is the empty string, then it simply goes to "metrics".

    Parameters:
        logger_or_name: A standard name string for a logging.Logger, of the sort one
                        would use with logging.getLogger(), or a logging.Logger-like
                        object (the name of which is used as the name string).

    Returns the "metrics" name for logger_or_name, according to the rules stated above.
    """

    if hasattr(logger_or_name, 'name'):
        logger_or_name = logger_or_name.name

    if len(logger_or_name) > 0:
       idx = logger_or_name.find('.')
       if idx == -1:
           return "%s.metrics" % logger_or_name
       else:
           return "%s.metrics%s" % (logger_or_name[:idx], logger_or_name[idx:])
    else:
        return 'metrics'


