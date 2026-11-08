"""
Unit tests for Network Probe module.
"""

import unittest
from unittest.mock import patch
from python.diagnostics.network_probe import probe_dns, probe_tcp_port


class TestNetworkProbe(unittest.TestCase):

    @patch("socket.gethostbyname")
    def test_probe_dns_success(self, mock_gethostbyname):
        mock_gethostbyname.return_value = "1.1.1.1"
        res = probe_dns("one.one.one.one")
        self.assertTrue(res["reachable"])
        self.assertEqual(res["resolved_ip"], "1.1.1.1")
        self.assertIsNone(res["error"])

    @patch("socket.gethostbyname")
    def test_probe_dns_failure(self, mock_gethostbyname):
        mock_gethostbyname.side_effect = Exception("Name or service not known")
        res = probe_dns("invalid-non-existent-domain.xyz")
        self.assertFalse(res["reachable"])
        self.assertIsNone(res["resolved_ip"])
        self.assertIsNotNone(res["error"])

    @patch("socket.socket")
    def test_probe_tcp_port_open(self, mock_socket_class):
        mock_sock = mock_socket_class.return_value
        mock_sock.connect_ex.return_value = 0

        res = probe_tcp_port("127.0.0.1", 8080)
        self.assertTrue(res["open"])
        self.assertEqual(res["error_code"], 0)


if __name__ == "__main__":
    unittest.main()
