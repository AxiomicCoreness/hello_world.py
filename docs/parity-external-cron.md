# parity-external-cron.md

**Purpose.** Move the `workflow-parity.yml` trigger off GitHub's throttled
`schedule` cron and onto a host you control. The workflow itself does not
change. Only the trigger moves.

**Why.** GitHub degrades sub-hourly `schedule:` crons under load, and the
degradation is not documented in terms of rate or duration. For a
round-robin dispatcher that assumes one tick per 15 minutes, any missed
tick shifts the slot sequence. Observing the actual tick rate is
necessary before drawing conclusions, but the general problem is real.

**What stays the same.**

- The workflow file at `.github/workflows/workflow-parity.yml`.
- The 55-entry case statement.
- The `concurrency: workflow-parity` group.
- The `contents: read` / `actions: write` permissions.

**What changes.**

- The `schedule:` block becomes vestigial. You may leave it (it will
  fire when GitHub deigns to) or remove it. Leaving it causes double
  dispatch if the external scheduler and GitHub's scheduler both fire
  near the same quarter-hour. Remove it if you want the external
  scheduler to be authoritative.

---

## 1. Create a PAT

**Fine-grained PAT** (recommended):

- Owner: `AxiomicCoreness`
- Repository access: only `hello_world.py`
- Permissions:
  - **Actions**: Read and write
  - Everything else: No access
- Expiration: 90 days, rotate on schedule.

**Classic PAT** (alternative):

- Scope: `workflow`
- This scope is broad — it grants push access to `.github/workflows/`
  across every repo the token can reach. Fine-grained is preferred.

Store the token wherever your scheduler reads secrets. On a systemd
host, `/etc/parity/token` with mode `0600`. On a real cron, in
`/etc/environment` is common but file-permission hygiene matters.

---

## 2. The trigger command

```bash
#!/bin/sh
# /usr/local/bin/parity-tick.sh

set -eu

REPO="AxiomicCoreness/hello_world.py"
REF="main"
WORKFLOW="workflow-parity.yml"

# Compute slot from the scheduler's clock, not the runner's.
slot=$(( $(date -u +%s) / 900 % 55 ))

curl -sS -X POST \
  -H "Authorization: Bearer ${GH_PAT}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches" \
  -d "{\"ref\":\"${REF}\",\"inputs\":{\"slot\":\"${slot}\"}}"

echo "dispatched slot ${slot} at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

Why pass slot explicitly. The workflow falls back to computing the
slot from date -u on the runner if inputs.slot is blank. But the
runner's clock is read after GitHub queues and starts the job, which
can be seconds to minutes after the dispatch. If the dispatch lands near
a quarter-hour boundary, the runner computes a different slot than the
scheduler intended. Passing slot explicitly pins the sequence to the
scheduler's clock, which is the one under your control.

The workflow already supports this — inputs.slot is honored when
non-empty, and the fallback is only used when it is blank.

---

## 3. Schedule it

### Systemd timer (recommended on Linux)

`/etc/systemd/system/parity-tick.service`:

```ini
[Unit]
Description=Workflow parity tick
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=/etc/parity/env
ExecStart=/usr/local/bin/parity-tick.sh
User=parity
Group=parity
```

`/etc/systemd/system/parity-tick.timer`:

```ini
[Unit]
Description=Workflow parity tick every 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true
AccuracySec=5s
Unit=parity-tick.service

[Install]
WantedBy=timers.target
```

`Persistent=true` makes systemd run a missed tick after downtime, which
partially compensates for host outages. `AccuracySec=5s` keeps the timer
from drifting into the next quarter-hour.

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now parity-tick.timer
systemctl list-timers parity-tick.timer
```

### Real cron (alternative)

```cron
*/15 * * * * /usr/local/bin/parity-tick.sh >> /var/log/parity-tick.log 2>&1
```

Cron does not catch up on missed ticks after downtime. If the host is
down at 09:15 and up again at 09:30, that slot is skipped.

---

## 4. Verify

After the first tick:

```bash
# Confirm the workflow run was created
gh run list --workflow workflow-parity.yml --limit 5 \
  --json createdAt,conclusion,event \
  --jq '.[] | "\(.createdAt)  \(.event)  \(.conclusion)"'
```

The event field should read `workflow_dispatch`, not `schedule`. If
you kept the `schedule:` block in the workflow, you will see both events
interleaved — one from GitHub, one from the external trigger. Remove the
`schedule:` block to make the external trigger authoritative.

Confirm the slot computed by the runner matches the slot passed:

```bash
gh run view <run-id> --log | grep -E '^slot='
```

The printed slot should equal `$(( $(date -u +%s) / 900 % 55 ))` at the
time of the dispatch, not at the time of the job start.

---

## 5. Operational notes

**Rotation.** A fine-grained PAT expires. Set a calendar reminder for
30 days before expiry. When the token rotates, update
`/etc/parity/env` and restart the timer unit (not required for real
cron, which re-reads the file on each invocation).

**Failure mode.** If the curl returns a non-2xx, the script exits
non-zero (because of `-sS` and `set -e`). Systemd will mark the service
failed; check `journalctl -u parity-tick.service`. A 401 means the PAT
expired. A 404 means the workflow file was renamed on the default
branch. A 422 means the inputs payload did not match the workflow's
`workflow_dispatch` schema.

**Rate limit.** Authenticated requests to the Actions API have a
5,000/hour limit per PAT. One dispatch every 15 minutes is 4/hour.
Non-binding.

**Not a substitute for the slot list.** The case statement with 55 file
names is still in `workflow-parity.yml`. If a workflow file is renamed
on main, the parity tick will still dispatch the old name and fail with
404. This is a separate problem from cron throttling and is not solved
by moving the trigger off GitHub.

**Slot 40 note.** `e2e-key-check.yml` is still a Python file at a `.yml`
path. With `set -e` now active, a dispatch of that file fails the tick
instead of reporting success. Fix or rename the file, or accept the
periodic failure until it is corrected.

---

## 6. Why not self-hosted runner

Some accounts report better schedule adherence with
`runs-on: self-hosted`. This is not documented by GitHub, and the
throttling mechanism operates on the scheduler before the runner is
selected, so the mechanism by which self-hosted would bypass throttling
is unclear. Treat the empirical reports as anecdotal. Moving to
self-hosted trades uncertain schedule reliability for a certain
operational cost: you now own the machine's uptime, patching, and
network. If you need reliable sub-hourly scheduling, moving the trigger
off GitHub Actions entirely — as above — is the deterministic fix.
