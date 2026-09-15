# Eyal Plan Loop

In-product plan loop: this chat plans and builds; one other model in Cursor (or Claude Code) reviews and inspects. No Codex or Claude CLI.

## Install

Copy this directory to `~/.cursor/skills/eyal-plan-loop/` and `~/.claude/skills/eyal-plan-loop/`. Open a new chat.

Triggers: `eyal plan loop`, `epl this plan`, `plan loop`.

## Behavior

- Default 3 review rounds (`rounds=N` to override). Round 3+ drops low nits unless you say `include-low`.
- Remembers the last reviewer in `~/.cursor/eyal-plan-loop.json`.
- One other model, must differ from this chat. You pick from the suggested list each run.
- Findings are not applied until you say implement / skip / reject.
- Status is posted in chat before waits and before edits (`STATUS`, `WHAT CHANGES`, `WAIT`).
- A changed plan SHA is not approved until it is reviewed again, unless you explicitly override.
- If Task/subagent is missing, the loop blocks instead of self-reviewing.

## Ship

After remotes exist: `scripts/ship.sh` to `eyalbou/eyal-plan-loop` and `eyalbou/eyal-personal-skills`. Then resync From GitHub in Willow.
