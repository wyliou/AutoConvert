---
name: quick-build
description: Implement from PRD + architecture quickly
---

# Quick Build

## Process

1. **Plan** - Read docs/PRD.md and docs/architecture.md, then write implementation plan to TodoWrite
2. **Implement** - Build it. Use your judgment on structure, testing, and order
3. **Validate** - Run data-driven validation if test data exists
4. **Commit** - When complete

## Data-Driven Validation (Delegate to subagent)

If test data exists (data/, samples/, fixtures/):

1. Run against all test inputs
2. Group ALL non-success results by error/warning type (not just failures - include warnings, attention, partial success, etc.)
3. For each non-success result, ask: "Is this bad input, or is my code wrong?"
   - Examine the actual input data
   - Trace through the code path
   - Default assumption: code bug (not input issue)
4. Fix code bugs, re-run (max 3 rounds)