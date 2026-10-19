#!/usr/bin/env bash
# Compile com.fruitfly.brain with the hhmi loader overlaid and run JUnit 5.
#
#   bash run_java_tests.sh            reuse /workspace/connectome_loader as the base tree
#   bash run_java_tests.sh --fresh    download main of AxiomicCoreness/hello_world.py
#                                     (codeload tarball, read-only), apply SovereignMain.diff
#                                     unless main already has it (applied in src/ at 1dfeaec)
#   BASE=/path bash run_java_tests.sh use another checkout (needs src/main/java, docs/katex_macros.yaml)
#
# Env: JAVA_HOME (default /opt/jdk-17), JUNIT_JAR (default the connectome_loader copy,
# else junit-platform-console-standalone 1.10.2 from Maven Central), WORK (default /tmp/hhmi_java).
# Builds in $WORK only; never writes to the base tree or any repo.
# Prints the JUnit summary, then a --chat smoke run against the placeholder.
# Exit: JUnit's exit code (0 = all passed), or 1 on a setup/compile/smoke failure.
set -euo pipefail
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAVA_HOME="${JAVA_HOME:-/opt/jdk-17}"
WORK="${WORK:-/tmp/hhmi_java}"
BASE="${BASE:-/workspace/connectome_loader}"
JUNIT_VER=1.10.2
JUNIT_JAR="${JUNIT_JAR:-/workspace/connectome_loader/junit.jar}"
[ -x "$JAVA_HOME/bin/javac" ] || { echo "[!] no JDK at $JAVA_HOME (see kernel skill kernel_scripts/install_jdk.sh)"; exit 1; }

rm -rf "$WORK"; mkdir -p "$WORK"
if [ "${1:-}" = "--fresh" ]; then
  curl -fsSL -o "$WORK/main.tgz" https://codeload.github.com/AxiomicCoreness/hello_world.py/tar.gz/refs/heads/main
  tar xzf "$WORK/main.tgz" -C "$WORK"
  BASE="$WORK/hello_world.py-main"
  if grep -q connectomeFile "$BASE/src/main/java/com/fruitfly/brain/SovereignMain.java"; then
    echo "[+] fresh main downloaded, SovereignMain.diff already applied in src/"
  else
    (cd "$BASE" && patch -p1 --forward < "$SKILL/java/SovereignMain.diff" >/dev/null) \
      || { echo "[!] SovereignMain.diff no longer applies to main"; exit 1; }
    echo "[+] fresh main downloaded, SovereignMain.diff applied"
  fi
fi
[ -d "$BASE/src/main/java/com/fruitfly/brain" ] || { echo "[!] no src tree at $BASE"; exit 1; }
if [ ! -f "$JUNIT_JAR" ]; then
  JUNIT_JAR="$WORK/junit.jar"
  curl -fsSL -o "$JUNIT_JAR" "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/$JUNIT_VER/junit-platform-console-standalone-$JUNIT_VER.jar"
fi

# Source set = base main + skill loader (skill copy wins); tests = base tests + skill test.
mkdir -p "$WORK/src/main" "$WORK/src/test" "$WORK/out/main" "$WORK/out/test"
cp -r "$BASE/src/main/java" "$WORK/src/main/"
cp -r "$BASE/src/test/java" "$WORK/src/test/" 2>/dev/null || mkdir -p "$WORK/src/test/java"
cp -r "$SKILL/java/src/." "$WORK/src/"
grep -q connectomeFile "$WORK/src/main/java/com/fruitfly/brain/SovereignMain.java" \
  || echo "[!] warning: SovereignMain has no --connectome-file (apply java/SovereignMain.diff)"

"$JAVA_HOME/bin/javac" -encoding UTF-8 -d "$WORK/out/main" $(find "$WORK/src/main/java" -name '*.java')
cp "$SKILL/java/src/main/resources/HHMIJaneliaMap.xml" "$WORK/out/main/"
[ -f "$BASE/docs/katex_macros.yaml" ] && cp "$BASE/docs/katex_macros.yaml" "$WORK/out/test/"
"$JAVA_HOME/bin/javac" -encoding UTF-8 -cp "$WORK/out/main:$JUNIT_JAR" -d "$WORK/out/test" \
  $(find "$WORK/src/test/java" -name '*.java')

set +e
"$JAVA_HOME/bin/java" -jar "$JUNIT_JAR" execute --disable-banner --details=summary \
  -cp "$WORK/out/main:$WORK/out/test" --scan-classpath "$WORK/out/test" 2>&1 \
  | grep -E 'tests (successful|failed|found)|✘|MethodSource' 
rc=${PIPESTATUS[0]}
set -e

reply=$("$JAVA_HOME/bin/java" -cp "$WORK/out/main" com.fruitfly.brain.SovereignMain \
  --chat hi --connectome-file "$SKILL/assets/HHMIJaneliaMap.xml" 2>"$WORK/smoke.err") \
  || { echo "[!] smoke run failed"; cat "$WORK/smoke.err"; exit 1; }
echo "[+] smoke: stdout lines=$(printf '%s\n' "$reply" | wc -l) stderr: $(tr '\n' ' ' < "$WORK/smoke.err")"
exit "$rc"
