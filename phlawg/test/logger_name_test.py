from nose import tools
import mock
import six

import phlawg

NAME_MAP = {
    # Empty name goes to "metrics"
    '': 'metrics',
    # Single-level name gets "metrics" as sublevel
    'fooey': 'fooey.metrics',
    # Multi-level names get "metrics" as second level, regardless of depth
    'these.two': 'these.metrics.two',
    'this.has.three': 'this.metrics.has.three',
    'but.he.got.four': 'but.metrics.he.got.four',
}

class TestLoggerNames(object):
    def test_name_to_metric_name_translation(self):
        for original_name, expected_name in six.iteritems(NAME_MAP):
            yield self.verify_name_translation, original_name, expected_name

    def verify_name_translation(self, original, expected):
        tools.assert_equal(
            expected,
            phlawg.to_metric_logger_name(original))


    def test_logger_to_metric_name_translation(self):
        for original_name, expected_name in six.iteritems(NAME_MAP):
            yield self.verify_logger_translation, original_name, expected_name


    def verify_logger_translation(self, original, expected):
        logger = mock.Mock(name='Logger')
        logger.name = original
        tools.assert_equal(
            expected,
            phlawg.to_metric_logger_name(logger))

