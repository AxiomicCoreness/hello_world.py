#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mTLS plugin."""

from .base import Plugin


class MTLSPlugin(Plugin):
    name = "mtls"
    description = "mTLS extract and verify_client_cert"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            from quantum.mtls_extract_and_config import verify_client_cert

            assert callable(verify_client_cert)
            result["message"] = "mTLS module loaded, verify_client_cert is callable"
        except Exception as e:
            result["passed"] = False
            result["message"] = f"mTLS check failed: {e}"
        return result
