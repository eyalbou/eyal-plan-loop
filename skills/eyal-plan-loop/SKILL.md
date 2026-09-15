---
name: eyal-plan-loop
description: "Harden a plan with an independent in-product model (not another CLI), then optionally build in this chat and inspect with that same other model. Use for eyal plan loop, epl this plan, plan loop, or when the user wants a Claudex-style review without Codex/Claude CLIs. Not for typo-level edits."
version: 0.2.0
---

# Eyal Plan Loop

**Skill version 0.2.0** -- same value as [VERSION](VERSION) and the YAML `version` above.

This conversation plans, arbitrates, and builds. Exactly one **other** in-product model reviews the plan and later inspects the diff. No `claude` / `codex` CLI. One skill, not a set of aliases.

Read [protocol.md](references/protocol.md) before launching a reviewer. Read [models.json](references/models.json) before asking which model. Prompts: [reviewer-prompt.md](references/reviewer-prompt.md).

## Notifications (do not skip)

The user must see status **in chat** before long waits and before any edit. Post a short status block, then act.

```
STATUS: <phase>
ROUND: <n>/<max> (omit if not in review/inspect)
MODEL: host=<this chat> reviewer=<slug>
PLAN: <path> SHA256=<12+ chars or pending>
WHAT CHANGES: <none | bullet list of files/sections>
WAIT: <what you are about to do / what you need from the user>
```

Phases: `setup` | `recon` | `requirements` | `picking-model` | `reviewing` | `waiting-on-you` | `applying` | `building` | `inspecting` | `done` | `blocked`

Rules:

- Post `STATUS: reviewing` or `STATUS: inspecting` **before** launching the subagent. Do not go silent.
- Post `WHAT CHANGES` **before** editing the plan or any code. Wait if those edits are not already approved.
- On `waiting-on-you`, the next line is the question (model pick, finding dispositions, another round, build yes/no, proceed-unreviewed).
- After a subagent returns: status + verdict + finding count, then wait or continue.
- Never apply findings, start a build, or inspect without a visible status block in that turn.

## Roles

| Role | Who |
|---|---|
| Planner / coordinator / default builder | This chat |
| Reviewer | One other model, fresh session |
| Inspector | Same other model, **new** session after build |

Detect the host model from this runtime (system/model line), not from PATH or installed CLIs. Reviewer slug **must differ**. `inherit` is never a reviewer. If they pick the host model, refuse and re-ask.

## Tunables

| Argument | Default | Meaning |
|---|---|---|
| `plan` | `PLAN.md` | Plan path |
| `log` | `PLAN-REVIEW-LOG.md` next to the plan, or `~/.cursor/plans/` if the plan lives there | Append-only log |
| `rounds` / `MAX_ROUNDS` | `3` | Completed plan-review turns |
| `mode` | `full` | `review` starts from an existing plan |
| `inspect` | `on` | `off` only if the user opts out; log it |
| `MAX_INSPECTION_ROUNDS` | `2` | First inspect plus one after approved fixes |

Echo tunables in the first `STATUS: setup` block. `rounds=N` overrides the default.

Authorization: a request to **plan** or **review** does not authorize building. A request to **plan and implement** does. `APPROVED` does not authorize building unless they already said implement.

## Phase 0 -- Setup, picker, recon

`STATUS: setup` then `picking-model`.

0. **Task preflight.** If this session has no Task/subagent tool (Cursor `Task`, or Claude Code's equivalent agent spawn with a `model` argument), `STATUS: blocked`. Say the loop cannot run here. Do **not** review the plan in this same chat. Same-chat critique is not independent.
1. Resolve plan and log paths. Start the log (see protocol: log contents). Keep review JSON under the log directory or `/tmp`, not as clutter in the target repo.
2. Load [models.json](references/models.json) for this host. Merge Claude Code extras from `python3 scripts/config.py get` (`claude_code_models`) and any model ids advertised in this session. Drop the host model and `inherit`.
3. Ask **once** which model reviews **and** inspects. Order: last `reviewer_id` from config (if still valid) first, then `suggest_when_host_contains`, then the rest. Use AskQuestion when available.
4. After they pick: `python3 scripts/config.py set-reviewer <id> --host <cursor|claude-code>`. On Claude Code, also `python3 scripts/config.py add-claude-model <id> [label]` so the next run has a list.
5. If that model cannot start: `STATUS: blocked`. No silent fallback to another slug.
6. Hash nothing until the plan file exists.

`mode=full`: inspect relevant code and docs. Present an assumptions ledger with sources. Batch material questions. Discover **this host's** relevant skills only; do not assume they exist for the reviewer subagent.

`mode=review`: load the supplied plan, fill only gaps that block review, skip the interview.

## Phase 1 -- Requirements and plan

`STATUS: requirements`. Write the plan with: goal, observable acceptance checks, approach, key decisions, non-goals, proof command(s).

`STATUS: waiting-on-you` if consequential decisions remain. Silence is not approval of those.

Then `python3 scripts/validate.py hash <PLAN>` (scripts next to this SKILL.md). Put SHA256 in the log and the next status block.

## Phase 2 -- Independent review

For each round until `APPROVED`, `BLOCKED`, cap, or the user stops:

1. `STATUS: reviewing` / `ROUND: n/3` / `WHAT CHANGES: none` / `WAIT: sending plan to <slug>`.
2. Fresh Task (round 1) or `resume` (later rounds) with `model=<slug>`. Prompt = [reviewer-prompt.md](references/reviewer-prompt.md) + plan body + SHA + user dispositions. Read-only. The subagent does not get this chat's opinions as instructions. **Nit cap:** after 2 completed rounds, unless the user said `include-low`, tell the reviewer to return only high/medium findings.
3. Save JSON, run `python3 scripts/validate.py review <file>`. Failure = `BLOCKED` for this round; tell the user; do not silent-retry or switch models.
4. Log JSON path, SHA, requested vs observed model (unknown observed: say so).

**APPROVED:** show summary + leftover **low** advice. Ask if they want any of those lows. Approval is this SHA only.

**REVISE:** `STATUS: waiting-on-you`. List findings to gate (id, severity, path, evidence, fix). After 2 completed rounds, unless `include-low`, omit low from the implement/skip/reject ask; say how many lows were dropped. Ask implement / skip / reject, per finding or as a batch. Use AskQuestion when available. **Do not edit until they answer. Silence is not yes.**

Then if any `implement`: `STATUS: applying` / `WHAT CHANGES: ...` and edit only those. Re-hash. The previous approval is dead. Ask: another round on the new SHA? If they implement nothing, do not burn a round unless they ask.

**BLOCKED:** explain. Do not mint `APPROVED`.

Stop at `MAX_ROUNDS`. Present leftovers. Another round only if they raise the cap.

**Unreviewed build:** if they want to build without `APPROVED` on the current SHA, they must say so. Log `unreviewed-spec`. Never call that SHA approved.

## Phase 3 -- Build and inspect

`STATUS: waiting-on-you` with `WHAT CHANGES:` the intended file list, then wait unless already authorized.

`STATUS: building`. Host implements. Capture pre-build baseline (git HEAD when possible). Run the proof command from the plan. Independently, do not trust a success story without running it.

`STATUS: inspecting` / `WHAT CHANGES: none` / `WAIT: sending diff to <slug>`. **New** subagent, same slug, read-only, inspect prompt + diff vs baseline. Same JSON + user gate on findings. After approved fixes, at most one more **fresh** inspect (`MAX_INSPECTION_ROUNDS`).

If this chat writes extra code after inspect, say those lines are unreviewed until another inspect. Do not claim the earlier inspect covers later edits.

`STATUS: done`: diff, proof, inspect coverage, leftover findings, rounds used, reviewed vs unreviewed SHA. Commits / push / Stash only if already authorized.

## Scripts

Resolve from this skill directory, not from the target repo.

```
python3 scripts/validate.py hash PLAN.md
python3 scripts/validate.py review /tmp/review.json
python3 scripts/config.py get
python3 scripts/config.py set-reviewer gpt-5.6-sol-high --host cursor
```

## Out of scope (v1)

- Spawning Codex or Claude CLIs
- A panel of 2-3 reviewers
- Scraping Cursor's model picker (update [models.json](references/models.json) + VERSION when the roster changes)
- HTML dashboard of the loop
- Auto-applying reviewer findings
- Reviewing in the same chat when Task is missing

## Shipping

Local: `~/.cursor/skills/eyal-plan-loop` (also copy to `~/.claude/skills/` for Claude Code). Git: `eyalbou/eyal-plan-loop` and `eyalbou/eyal-personal-skills` at `skills/eyal-plan-loop/`. Bump `VERSION` + YAML `version` + the stamp under the h1 together. Then `scripts/ship.sh`. In Willow: resync From GitHub.

Do not spawn other CLIs. Do not claim Codex or Claude Code CLI reviewed a plan this skill handled.
