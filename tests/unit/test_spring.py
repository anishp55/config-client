"""Test spring module."""
import unittest
from unittest.mock import PropertyMock, patch

from config.spring import ConfigClient, create_config_client, config_client


class ResponseMock:
    config = {
        "health": {
            "config": {
                "enabled": False
            }
        },
        "spring": {
            "cloud": {
                "consul": {
                    "discovery": {
                        "health-check-interval": "10s",
                        "health-check-path": "/manage/health",
                        "instance-id": "pecas-textos:${random.value}",
                        "prefer-ip-address": True,
                        "register-health-check": True
                    },
                    "host": "discovery",
                    "port": 8500
                }
            }
        }
    }

    def __init__(self, code=200, ok=True):
        self.status_code = code
        self.ok = ok

    def json(self):
        return self.config


class TestConfigClient(unittest.TestCase):
    """Unit tests to spring module."""

    def setUp(self):
        """Mock of responses generated by Spring Cloud Config."""
        self.config_example = {
            "health": {
                "config": {
                    "enabled": False
                }
            },
            "spring": {
                "cloud": {
                    "consul": {
                        "discovery": {
                            "health-check-interval": "10s",
                            "health-check-path": "/manage/health",
                            "instance-id": "pecas-textos:${random.value}",
                            "prefer-ip-address": True,
                            "register-health-check": True
                        },
                        "host": "discovery",
                        "port": 8500
                    }
                }
            }
        }
        self.obj = ConfigClient(
            app_name='test-app',
            url='{address}/{branch}/{app_name}-{profile}.yaml'
        )

    def test_get_config_failed(self):
        """Test failed to connect on ConfigClient."""
        with self.assertRaises(SystemExit):
            self.obj.get_config()

    @patch('config.spring.requests.get', return_value=ResponseMock())
    def test_get_config(self, RequestMock):
        self.obj.get_config()
        self.assertDictEqual(self.obj.config, self.config_example)

    @patch('config.spring.requests.get', return_value=ResponseMock(code=402, ok=False))
    def test_get_config_response_failed(self, RequestMock):
        with self.assertRaises(SystemExit):
            self.obj.get_config()

    def test_config_property(self):
        self.assertIsInstance(self.obj.config, dict)

    def test_default_url_property(self):
        self.assertIsInstance(self.obj.url, str)
        self.assertEqual(
            self.obj.url,
            "http://localhost:8888/configuration/master/test-app-development.json"
        )

    def test_custom_url_property(self):
        obj = ConfigClient(
            app_name='test-app',
            branch='development',
            url="{address}/{branch}/{profile}-{app_name}.json"
        )
        self.assertIsInstance(obj.url, str)
        self.assertEqual(obj.branch, 'development')
        self.assertEqual(
            obj.url,
            "http://localhost:8888/configuration/development/development-test-app.json"
        )

    def test_get_attribute(self):
        type(self.obj)._config = PropertyMock(return_value=self.config_example)
        response = self.obj.get_attribute('spring.cloud.consul.host')
        self.assertIsNotNone(response)
        self.assertEqual(response, "discovery")

    def test_get_keys(self):
        type(self.obj)._config = PropertyMock(return_value=self.config_example)
        self.assertEqual(self.obj.get_keys(), self.config_example.keys())

    @patch('config.spring.requests.get', return_value=ResponseMock())
    def test_decorator(self, RequestMock):
        @config_client(app_name='myapp')
        def inner_method(c=None):
            self.assertIsInstance(c, ConfigClient)
            return c

        response = inner_method()
        self.assertIsNotNone(response)

    def test_decorator_failed(self):
        @config_client()
        def inner_method(c=None):
            self.assertEqual(ConfigClient(), c)

        with self.assertRaises(SystemExit):
            inner_method()

    def test_fix_valid_url_extension(self):
        self.assertTrue(self.obj.url.endswith('json'))

    def test_create_config_client_with_singleton_decorator(self):
        client1 = create_config_client()
        client2 = create_config_client()

        self.assertEqual(client1, client2)
