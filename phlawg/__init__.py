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
        for name, value in metrics.iteritems():
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

