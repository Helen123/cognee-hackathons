# Known gaps — open to Track 2 proposals

The eight issues deliberately leave these xitkit findings out. Each was excluded because it
is large, breaking, hard to grade independently, or likely to break an all-pass run. A
proposal that makes one of them **gradable without a human** and **small enough to pass** is
exactly what Track 2 is for.

| Gap | Why it was left out | What a proposal has to solve |
|---|---|---|
| Stable task IDs (today `file:line`) | touches most commands; could dominate the result | a bounded slice with an exact grader |
| `rm` help text vs behaviour mismatch | small and cosmetic alone | pair it with something memory-relevant |
| Repeated section-title parsing | performance-only, hard to assert cheaply | a deterministic call-count grader like issue 5's |
| Line-preserving writes to Markdown and malformed `.xit` | large: replaces the parser with a line-based editor | a strictly scoped subset |
| Broad dead-code cleanup | target list was not precise enough to grade fairly | an explicit, enumerated list |

Other directions the organisers would like to see proposed:

- **Cross-session preference**: a convention the user states in an early issue (naming,
  test layout, error-message style) that a later issue must honour unprompted.
- **Superseded decision**: an instruction given in issue n that issue n+k reverses; memory
  must not keep applying the old one.
- **Stale index**: a change that moves a symbol the memory indexed earlier; does recall point
  at the old location?
