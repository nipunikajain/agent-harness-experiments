Run the skill scout.

Use the skill-scout subagent to propose vetted skills my agents could use. It must:

- prefer the official Anthropic marketplace and security-scanned sources (see the
  `skill_sources` section of `.claude/scout/sources.yaml`),
- dedupe against the skills I already have installed,
- return a short ranked list where each entry says what the skill does, its source (and
  whether it is vetted), which agent would use it, and any permission or security concern,
- then stop.

It proposes only: never install a skill or change settings.

$ARGUMENTS

Show me the list. I review and install myself.
