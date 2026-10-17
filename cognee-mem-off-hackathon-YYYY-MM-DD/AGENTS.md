<!-- cognee-hackathon-feedback -->
## cognee feedback (hackathon)

This project uses cognee at the "Mem Off (date TBD)" hackathon. Follow the
`cognee-hackathon-feedback` skill (`.claude/skills/cognee-hackathon-feedback/SKILL.md`):

- Whenever cognee errors, is slow, behaves unexpectedly, or I seem confused or
  annoyed about it, add an entry to `./cognee-feedback.md`.
- About every 10 minutes a hook ends your turn with a "cognee-feedback
  checkpoint" message: update the file as it says, briefly, then stop.
- When I say I'm done, submitting, or out of time — or run
  `/cognee-hackathon-feedback` — run the skill's wrap-up.
- The organizers announce where the finished file goes.
- Never commit or send that file yourself.
<!-- /cognee-hackathon-feedback -->

<!-- memoff-memory-report -->
## memoff report (hackathon)

This project takes part in "Mem Off (date TBD)" as team "<team-slug>". Follow the `memoff-memory-report`
skill (`.claude/skills/memoff-memory-report/SKILL.md`):

- About every 15 minutes a hook ends your turn with a "memoff-report checkpoint"
  message: update `./memoff-report.md` and `./memoff-report.json` from tool output
  (harness run folders, the cognee-report scorecard, recall receipts), briefly, then stop.
- Record numbers from tools, never impressions; no quotes, keys, data or names.
- When I say I'm done or submitting — or run `/memoff-memory-report` — run the skill's wrap-up and
  copy both files into `submissions/<team-slug>/report/`. They are submitted with the
  action results.
<!-- /memoff-memory-report -->
