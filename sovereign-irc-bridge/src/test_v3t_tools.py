# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Offline tests for v3t_tools: fake-clock ISO 8601 formatting, SSRF blocking, tool-call parsing."""
from __future__ import annotations

import os
import socket
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import v3t_tools as vt  # noqa: E402


def fake_resolver(ip):
    return lambda host, port, proto=0: [(socket.AF_INET6 if ":" in ip else socket.AF_INET, 1, 6, "", (ip, port))]


class ClockTest(unittest.TestCase):
    def test_winter_est(self):
        self.assertEqual(vt.now_line(datetime(2026, 11, 2, 20, 30, 0, 123, tzinfo=timezone.utc)),
                         "Current time: 2026-11-02T15:30:00-05:00 (UTC 2026-11-02T20:30:00Z). "
                         "Always write timestamps in ISO 8601 with explicit offset.")

    def test_summer_edt_and_day_rollover(self):
        line = vt.now_line(datetime(2026, 7, 1, 2, 15, 0, tzinfo=timezone.utc))
        self.assertIn("2026-06-30T22:15:00-04:00 (UTC 2026-07-01T02:15:00Z)", line)

    def test_dst_boundaries(self):
        # 2026-03-08 07:00Z = 03:00 EDT (just after spring forward); 06:59Z = 01:59 EST
        self.assertIn("2026-03-08T03:00:00-04:00", vt.now_line(datetime(2026, 3, 8, 7, 0, tzinfo=timezone.utc)))
        self.assertIn("2026-03-08T01:59:00-05:00", vt.now_line(datetime(2026, 3, 8, 6, 59, tzinfo=timezone.utc)))

    def test_non_utc_input_normalised(self):
        t = datetime(2026, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=9)))
        self.assertIn("(UTC 2025-12-31T15:00:00Z)", vt.now_line(t))


class SsrfTest(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.pop("V3T_FETCH_ALLOW_NETS", None)

    def tearDown(self):
        if self._env is not None:
            os.environ["V3T_FETCH_ALLOW_NETS"] = self._env

    def test_schemes_and_userinfo(self):
        for u in ("file:///etc/passwd", "ftp://x.example/", "gopher://x/", "https://user:pw@example.com/",
                  "javascript:alert(1)", "http:///nohost"):
            with self.assertRaises(vt.BlockedURL, msg=u):
                vt.check_url(u, resolver=fake_resolver("93.184.215.14"))

    def test_private_and_loopback_blocked(self):
        for ip in ("127.0.0.1", "10.1.2.3", "192.168.0.10", "172.16.5.5", "169.254.169.254", "0.0.0.0",
                   "100.64.0.1", "::1", "fe80::1", "fc00::1", "::ffff:127.0.0.1", "224.0.0.1", "198.18.0.1"):
            with self.assertRaises(vt.BlockedURL, msg=ip):
                vt.check_url("http://evil.example/", resolver=fake_resolver(ip))

    def test_public_allowed(self):
        self.assertEqual(vt.check_url("https://example.com/x", resolver=fake_resolver("93.184.215.14"))[1],
                         "example.com")

    def test_allow_nets_opt_in_never_loopback(self):
        os.environ["V3T_FETCH_ALLOW_NETS"] = "198.18.0.0/15,127.0.0.0/8"
        vt.check_url("http://x.example/", resolver=fake_resolver("198.18.0.1"))
        with self.assertRaises(vt.BlockedURL):
            vt.check_url("http://x.example/", resolver=fake_resolver("127.0.0.1"))

    def test_literal_ip_loopback_blocked_live_resolver(self):
        with self.assertRaises(vt.BlockedURL):
            vt.web_fetch("http://127.0.0.1:8085/health")

    def test_run_tool_reports_block_not_raise(self):
        self.assertTrue(vt.run_tool("web_fetch", {"url": "http://127.0.0.1/"}).startswith("blocked:"))


class ToolParseTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(vt.parse_tool_call('x <tool_call>{"name": "web_search", "arguments": {"query": "q"}}</tool_call>'),
                         ("web_search", {"query": "q"}))
        self.assertIsNone(vt.parse_tool_call('<tool_call>{"name": "rm", "arguments": {}}</tool_call>'))
        self.assertIsNone(vt.parse_tool_call("plain answer"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
