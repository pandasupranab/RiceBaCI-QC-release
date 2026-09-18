# /analysis — Reproducibility harness, decisions, deviations

**Current status:** `current_audit_status.md` is the live correction/acceptance
ledger. The entries below include historical planning items and are not proof
that those items were completed or that any OSF registration exists.

| File | Purpose |
|---|---|
| `decisions_log.md` | Append-only record of every framework-level decision (committed) |
| `deviation_log.md` | Append-only record of changes from successive working protocols; the historical OSF-labelled draft was never registered and is not evidence of prospective status |
| `anticipated_critiques.md` | Reviewer-anticipated critiques + responses (Week 3 deliverable) |
| `../run_all.sh` | Root-level reproducibility harness — orchestrates the executable pipeline stages and stops on missing external inputs |
| `../requirements.txt` | Compatibility union of exact direct-package versions; the separately checked profiles are in `../environments/` |

The decisions log is committed first because it captures the user-locked decisions on 15 Jun 2026 that drove the entire framework design.
