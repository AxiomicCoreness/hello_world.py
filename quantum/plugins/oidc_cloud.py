#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OIDC cloud providers plugin — soft status check."""

from .base import Plugin


class OIDCCloudPlugin(Plugin):
    name = "oidc_cloud"
    description = "OIDC cloud provider client status"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            from quantum.security.oidc_cloud import (
                OIDCCloudClient,
                mint_offline_token,
                verify_offline_token,
            )

            st = OIDCCloudClient(prefer_offline=True).status()
            cred = mint_offline_token("plugin-probe")
            claims = verify_offline_token(cred.access_token)
            result["message"] = (
                f"offline_ok={claims.verified} crypto={st.get('crypto_available')} "
                f"gha={st.get('github_actions')}"
            )
        except Exception as e:
            result["passed"] = False
            result["message"] = f"oidc_cloud check failed: {e}"
        return result
