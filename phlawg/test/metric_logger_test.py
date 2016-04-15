from nose import tools
from six import moves
import mock

import phlawg

LEVELS = [
   'critical',
   'debug',
   'error',
   'fatal',
   'info',
   'warn',
   'warning',
]

class TestPhlawgMetricLogger(object):
    def setup(self):
        self.base_logger = mock.Mock(name='BaseLogger')
        self.logger = phlawg.MetricLogger(self.base_logger)

    def metrics(self, count=3):
        # Produces a dictionary of metrics as key/value pairs, with each
        # key having a dynamic name (by stringifying a mock) and a dynamic
        # integer value (the id of a new mock).
        # The dictionary will have `count` pairs.
        return dict((str(mock.Mock(name='metricName')), id(mock.Mock()))
                    for i in moves.xrange(count))

    def check_metrics(self, level, **metrics):
        pass

    def check_unordered_calls(self, calls, expectation):
        tools.assert_equal(
                sorted(calls),
                sorted(expectation))


    def test_log_method(self):
        level = mock.Mock(name='LogLevel')
        metrics = self.metrics()
        self.logger.log(level, **metrics)

        self.check_unordered_calls(
            self.base_logger.log.call_args_list,
            [((level, '%s=%s' % (name, val)), {'extra': {'metric': name, 'value': val}})
             for name, val in metrics.items()])

    def test_level_methods(self):
        for level in LEVELS:
            yield self.verify_level_method, level

    def verify_level_method(self, level):
        emitter = getattr(self.logger, level)
        receiver = getattr(self.base_logger, level)
        metrics = self.metrics()
        emitter(**metrics)
        self.check_unordered_calls(
            receiver.call_args_list,
            [(('%s=%s' % (name, val),), {'extra': {'metric': name, 'value': val}})
             for name, val in metrics.items()])

