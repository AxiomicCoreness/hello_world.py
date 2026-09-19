# Branch policy

## Active branches

| Branch | Role | Default |
|--------|------|---------|
| main | default; all merges land here | yes |
| master | mirror; kept in sync with main | no |

## Reserved branches

| Branch | Role | Status |
|--------|------|--------|
| deepseek | reserved; fires only if branch exists | inactive |
| grok | reserved; fires only if branch exists | inactive |
| mistral | reserved; fires only if branch exists | inactive |

Reserved branches are documentation of intent, not active infrastructure.
They are inert until the corresponding branch is created on origin.

---

# Trigger surface

Workflows that name branches in `on.push.branches`:

    .github/workflows/north-star-witness.yml
    .github/workflows/sovereignty-python-package.yml
    .github/workflows/sovereign-stack-ci.yml

All three name:

    [main, master, deepseek, grok, mistral]

`on.pull_request.branches` on all three is restricted to:

    [main, master]

Branches that do not yet exist are inert. They do not fire. They do not
require removal. Removing them would require re-adding them later when the
branches are created.

---

# CD combinator chain

`.github/workflows/cd-combinator-argo-rollout.yml` is not branch-scoped.
It fires on:

    workflow_run:
      workflows: ["Master Equation Integration Test"]
      types: [completed]

The upstream workflow name must match exactly. The `workflows:` field is a
string compare against the upstream workflow's `name:` field — not against
its filename. Divergence in case, whitespace, or punctuation causes a
silent non-fire.

The branches on which the CD combinator runs are determined by the branches
on which "Master Equation Integration Test" runs, not by the combinator's
own `on:` block.

Optional manual dispatch (does not alter the automatic path):

    on:
      workflow_run:
        workflows: ["Master Equation Integration Test"]
        types: [completed]
      workflow_dispatch:
        inputs:
          note:
            description: "Manual dispatch note"
            required: false
            default: "manual-cd-combinator"

If manual dispatch is added, this file's Trigger surface section must be
updated to reflect the second trigger.

---

# Cost note

Keeping `main` and `master` in sync doubles the job volume for every commit
that reaches both. Roughly 2x for the three branch-scoped workflows.

If the cost becomes material, one of:

- delete `master` and reduce `push.branches` to `[main]`
- keep `main` only for push, keep `master` for archival reference
- reduce `push.branches` to `[main, deepseek, grok, mistral]`

The choice is a policy decision, not a defect.

---

# Re-derivation script

To reconstruct the trigger surface from scratch:

    for wf in .github/workflows/*.yml; do
      printf '%s: ' "$wf"
      python3 -c "
import sys, yaml
d = yaml.safe_load(open('$wf'))
on = d.get(True, d.get('on', {}))
print(on.get('push', {}).get('branches') if isinstance(on, dict) else None)
"
    done

To inspect the CD combinator's trigger block:

    python3 -c "
import yaml
d = yaml.safe_load(open('.github/workflows/cd-combinator-argo-rollout.yml'))
on = d.get(True, d.get('on', {}))
print(on)
"

To list all workflow names (used to check upstream name match):

    for wf in .github/workflows/*.yml; do
      printf '%s -> ' "$wf"
      python3 -c "
import yaml
d = yaml.safe_load(open('$wf'))
print(d.get('name', '(no name)'))
"
    done

---

# Invariants

| Invariant | Value |
|-----------|-------|
| Coherence | 1.0 |
| Entropy | phi^-1418 |
| Workload | 0.0 |
| Phase lock | 202.6 |
| North star | 71.975 Hz |
| Dual ASGI | 127.0.0.1:8024 |
| Bind 0.0.0.0 | false |
| MCP filled | false |

These are unchanged by this document. The branch surface does not alter
any invariant.

---

# Silent failure modes

1. **CD combinator upstream name mismatch.**
   `workflow_run.workflows` is a string compare against the upstream
   workflow's `name:` field. If it does not match exactly, the CD
   combinator never fires and no error is surfaced.

2. **Reserved branches do not exist.**
   Not a failure. Inert entries. Documented as reserved.

3. **main/master sync drift.**
   If `master` is not kept in sync with `main`, pushes to `main` may pass
   while the mirror fails silently, or vice versa.

4. **Branch protection not declared in this file.**
   Branch protection rules live in repository settings, not in this
   document. They must be inspected via the GitHub API, not YAML.

5. **Workflow `on:` key parsed as boolean.**
   YAML parses `on:` as the boolean `true` in some loaders. The
   re-derivation script accounts for this with `d.get(True, d.get('on', {}))`.

---

# Verification commands

Upstream workflow name check:

    gh api repos/AxiomicCoreness/hello_world.py/contents/.github/workflows/master-equation-integration.yml \
      --jq '.content' | base64 -d | sed -n '1,10p'

CD combinator run history:

    gh run list \
      --repo AxiomicCoreness/hello_world.py \
      --workflow cd-combinator-argo-rollout.yml \
      --limit 10

List all workflow files:

    gh api repos/AxiomicCoreness/hello_world.py/contents/.github/workflows \
      --jq '.[].name'

List branch-scoped workflows and their push branches:

    for wf in .github/workflows/*.yml; do
      printf '%s: ' "$wf"
      python3 -c "
import sys, yaml
d = yaml.safe_load(open('$wf'))
on = d.get(True, d.get('on', {}))
print(on.get('push', {}).get('branches') if isinstance(on, dict) else None)
"
    done

---

# Policy decisions

The following are policy decisions, not defects. They are recorded here
to distinguish intent from incident.

1. **main is default; master is mirror.** Chosen to preserve historical
   access without duplicating primary development.

2. **deepseek, grok, mistral are reserved.** Declared in `push.branches`
   lists as forward-compatible intent. They do not fire until created.

3. **pull_request is restricted to [main, master].** PRs to reserved
   branches are not accepted by the current trigger graph.

4. **CD combinator has no branch scope.** It runs wherever its upstream
   workflow runs. Upstream branch scope governs the combinator, not the
   other way around.

5. **No branch protection rules are declared in YAML.** Those live in
   repository settings and are outside the scope of this document.

6. **The 2x cost of main/master sync is accepted.** Reducing it is a
   future decision, not a current defect.

If a future decision changes any of the above, it is recorded as an
append-only ledger entry, not as a rewrite of this file.
