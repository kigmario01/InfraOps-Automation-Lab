"""
Unit tests for Service Checker module.
"""

import unittest
from unittest.mock import patch, MagicMock
from python.monitoring.service_checker import (
    check_http_endpoint,
    check_all_services,
)


class TestServiceChecker(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_check_http_endpoint_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = check_http_endpoint(
            name="Test Service",
            url="http://mock-service:8080/health",
            expected_code=200,
        )
        self.assertEqual(res["state"], "UP")
        self.assertEqual(res["http_code"], 200)

    @patch("urllib.request.urlopen")
    def test_check_http_endpoint_unexpected_code(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 500
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = check_http_endpoint(
            name="Failing Service",
            url="http://mock-service:8080/health",
            expected_code=200,
        )
        self.assertEqual(res["state"], "UNEXPECTED_STATUS")
        self.assertEqual(res["http_code"], 500)

    @patch("python.monitoring.service_checker.check_http_endpoint")
    def test_check_all_services(self, mock_check_single):
        mock_check_single.side_effect = [
            {"name": "S1", "state": "UP"},
            {"name": "S2", "state": "UP"},
        ]
        res = check_all_services([
            {"name": "S1", "url": "http://s1"},
            {"name": "S2", "url": "http://s2"},
        ])
        self.assertEqual(res["overall_status"], "HEALTHY")
        self.assertEqual(res["up"], 2)
        self.assertEqual(res["down"], 0)


if __name__ == "__main__":
    unittest.main()
