#!/usr/bin/env bash
# Idempotent JDK 17 install. Tries apt openjdk-17-jdk-headless first; Debian 13
# (trixie) does not ship it, so it falls back to an Eclipse Temurin 17 tarball in /opt.
set -euo pipefail
JDK_DIR=/opt/jdk-17
if [ -x "$JDK_DIR/bin/javac" ]; then echo "[=] JDK 17 already at $JDK_DIR"; "$JDK_DIR/bin/java" -version; exit 0; fi
if command -v javac >/dev/null 2>&1 && javac -version 2>&1 | grep -q ' 17\.'; then
  echo "[=] system javac 17 present"; javac -version; exit 0; fi
if apt-cache policy openjdk-17-jdk-headless 2>/dev/null | grep -q 'Candidate: [0-9]'; then
  sudo apt-get install -y -qq openjdk-17-jdk-headless
  sudo ln -sfn "$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")" "$JDK_DIR"
else
  ARCH=$(uname -m); case "$ARCH" in x86_64) A=x64;; aarch64) A=aarch64;; *) echo "unsupported $ARCH"; exit 1;; esac
  URL="https://api.adoptium.net/v3/binary/latest/17/ga/linux/$A/jdk/hotspot/normal/eclipse"
  TMP=$(mktemp -d); echo "[*] downloading $URL"
  curl -fsSL -o "$TMP/jdk.tar.gz" "$URL"
  sudo mkdir -p "$JDK_DIR"
  sudo tar -xzf "$TMP/jdk.tar.gz" -C "$JDK_DIR" --strip-components=1
  rm -rf "$TMP"
fi
"$JDK_DIR/bin/java" -version
