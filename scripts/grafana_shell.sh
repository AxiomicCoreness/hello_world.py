#!/bin/sh
# Grafana shell wrapper. Anonymous access. No password is read or set.
set -eu
export GF_AUTH_ANONYMOUS_ENABLED=true
export GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
export GF_AUTH_DISABLE_LOGIN_FORM=true
export GF_AUTH_BASIC_ENABLED=false
unset GRAFANA_PASSWORD || true
exec grafana-server --homepath /usr/share/grafana
