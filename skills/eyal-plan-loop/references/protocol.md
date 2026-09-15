# Review and inspect protocol

Read from SKILL.md. Do not spawn `claude` or `codex` CLIs.

## Verdict JSON (plan review and inspect)

Exactly these keys:

```json
{
  "verdict": "APPROVED | REVISE | BLOCKED",
  "summary": "one paragraph",
  "findings": [
    {
      "id": "EPL-001",
      "severity": "high | medium | low",
      "path": "file or plan path",
      "evidence": "what you observed",
      "fix": "concrete change"
    }
  ],
  "coverage": ["what was actually inspected"],
  "limitations": ["what was not"]
}
```

Rules:

- `APPROVED` cannot include unresolved high or medium findings. Low leftover advice is allowed.
- `REVISE` needs at least one finding.
- `BLOCKED` needs a limitation (missing evidence, model failed to start, malformed output).
- Finding ids unique. All five finding fields non-empty strings.
- Empty coverage is only allowed on `BLOCKED`.

Validate with:

```
python3 <skill>/scripts/validate.py review path/to/review.json
python3 <skill>/scripts/validate.py hash path/to/PLAN.md
```

Approval is the pair `(plan path, sha256)`. Any `implement` edit changes the SHA. Never label a new SHA `APPROVED` without a new review, unless the user explicitly overrides (`unreviewed-spec` in the log).

## Log file

Append-only. Start with: host model, requested reviewer slug, rounds, mode, inspect on/off, authorization (review / plan / plan-and-implement).

Each review round: SHA256, artifact JSON path, verdict, finding ids, requested vs observed model, user dispositions (`implement` / `skip` / `reject` + short reason if given), nit-cap on/off.

Each inspect: baseline commit, files in the diff, verdict, dispositions.

Do not commit diagnostics into a random project checkout.

## Subagent contract

Launch a **fresh** Task/subagent (or the host's equivalent). Pass `model` = the chosen slug. Never `inherit`.

Reviewer/inspector prompt must include:

- Plan body, or inspect: diff vs pre-build baseline plus file list.
- This schema.
- Read/search only. No edits, no commits, no extra skills, no MCP writes.
- Return only the JSON object (optionally fenced). Host extracts JSON and runs `validate.py review`.

Malformed JSON, failed validation, or a model that will not start = `BLOCKED` for that turn. Do not retry blindly. Do not switch slugs. Report and ask the user.

If the host session has no Task/subagent tool, do not start a review. Same-chat review is forbidden.

Resume the **same** reviewer subagent for later **plan-review** rounds (`resume` + host-authored dispositions: what was implemented, skipped, rejected). Do not relitigate skips without new evidence.

Inspect is always a new session. Never resume a review session as an inspect, or an inspect as a review.

## User-gated dispositions

On `REVISE` the host does not accept findings. Present them, then wait.

Allowed answers per finding: `implement` / `skip` / `reject`. Batch ok (`do 1 and 3`). Silence is not yes.

Only then edit for `implement`. Record skips/rejects in the log.

After any `implement`: re-hash, then ask whether to send the new SHA back (if rounds remain). If they implement nothing, do not spend another round unless they ask.

Same gate after inspect findings, before code fixes.

## Round cap

Default `MAX_ROUNDS = 3` completed plan-review turns. Override at start (`rounds=N`). Cap hit with leftovers: stop, no fake `APPROVED`. Another round only if the user raises the cap.

**Nit cap:** rounds 1 and 2 may include low findings. From round 3 onward (after two completed turns), unless the user said `include-low` / `nits=on`, the reviewer prompt forbids low findings and the host does not ask implement/skip/reject on lows (report the omitted count only).

Inspect: `MAX_INSPECTION_ROUNDS = 2` (first inspect plus one after user-approved fixes). Same user gate. Nit cap does not apply to inspect (code review still reports lows; user still gates them).
