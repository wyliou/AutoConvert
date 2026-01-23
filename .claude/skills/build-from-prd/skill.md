---
name: build-from-prd
description: Implement a PRD with sequential subagent delegation
---

# Build from PRD 

## Quick Reference
   
**Output:** Terse. Use "✓ Step N complete" format.

**Role:** Tech Lead coordinating subagents. You plan, delegate, integrate — you don't implement subsystems.

| Action | Main | Sub |
|--------|:----:|:---:|
| Read PRD/architecture docs | ✓ | ✗ |
| Scaffold (dirs, init files, manifest) | ✓ | ✗ |
| Write subsystem code | ✗ | ✓ |
| Write tests | ✗ | ✓ |
| Write pipeline/entry point | ✓ | ✗ |
| Run commands (test, lint) | ✓ | ✓ |

**Enforcement:** Do not directly edit subsystem implementation files. Only edit: init/index files, entry points (main.py, index.ts, main.go), and pipeline orchestration. Delegate all other source file changes via Task tool.

**Test Gate:** Every subsystem delegation MUST return `tests: N passing` where N > 0. Reject and re-delegate if missing.

---

## Workflow

### 1. Pre-flight & Plan

**Verify docs exist:**
```
ls docs/PRD.md docs/architecture.md
```
If missing → STOP, notify user.

**Read and extract (for each subsystem):**
- From PRD.md:
  - FRs: full text including tables, formats, codes
  - NFRs: performance, validation requirements
  - Error cases: what edge cases must be handled
  - Examples: sample inputs/outputs if provided
  - **MUST/CRITICAL statements:** Extract statements with "MUST", "CRITICAL", "REQUIRED" - these are non-negotiable
  - **Numeric constraints:** Extract numbers with units (e.g., "13 columns", "13 fields", "rows 7-30") - flag ambiguous ones
- From architecture.md:
  - Tech stack, dependencies, data models
  - Input/Output types per subsystem
  - Architecture pattern excerpt

**Create PRD Checklist (before delegation):**
```
MUST/CRITICAL statements:
- [ ] "MUST..." / "CRITICAL..." - line NNN

Numeric constraints:
- [ ] counts, limits, ranges - line NNN

Input→Output examples:
- [ ] every "X" → Y example - line NNN

Scattered requirements (group by topic):
- [ ] topic: lines NNN, MMM, PPP → single subsystem
```
**GATE:** Every input→output example requires a test. Related requirements across sections must be grouped before delegation.

**Define interfaces (before any delegation):**
Design API contracts between subsystems based on architecture.md. This ensures:
- Subsystems can be developed independently in parallel
- Each subagent knows exact inputs/outputs for their module
- Integration works because all subsystems agree on signatures upfront
```
<subsystem> interfaces:
- func(param: type) -> type: "purpose"
  Example: func(x) → y
```

**Map FRs → subsystems:** Each FR maps to one primary subsystem.
**Map NFRs → subsystems:** Assign relevant NFRs to affected subsystems.

**FR Coverage Matrix (CRITICAL - verify BEFORE implementation):**
```
| FR | Subsystem | Acceptance Criteria (from PRD) |
|----|-----------|--------------------------------|
| FR-XX | parser | Valid files return DataFrame with expected columns |
| FR-YY | validator | Invalid rows flagged with error messages |
```
**GATE:** Every FR must have: subsystem assignment + acceptance criteria. Stop if any FR unmapped.

**File discovery:**
```
ls -la
```
Check for existing: src/, tests/, manifest (pyproject.toml, package.json, go.mod, etc.)

**GATE:** Stop if FR unmappable, docs incomplete, or dependency cycle detected.

**Output to TodoWrite:**
```
1. Scaffold (if needed)
2. Implement <subsystem_1>
3. Implement <subsystem_2>
... (per dependency order)
N. Integration (includes FR verification)
N+1. Real Data Validation
N+2. Code simplification
N+3. Build & docs
N+4. Commit
```

Brief: "Found X FRs, Y subsystems"

### 2. Scaffold (if needed)

**Skip if ALL exist:** manifest, subsystem dirs, init files.

**Otherwise create:**
- Directory structure per architecture.md
- pyproject.toml / package.json
- `__init__.py` / index.ts files
- Run `uv sync` / `npm install`

**Output:** "✓ Scaffold complete" or "✓ Scaffold skipped"

### 3. Implement & Test (delegate each subsystem)

Execute in dependency order, ONE subsystem at a time. Sequential execution avoids subtle integration issues from parallel development (data format assumptions, interface drift, semantic dependencies).

For each subsystem, delegate via Task tool (subagent_type="general-purpose"). See **Appendix A** for template.

**After each return:**
- Questions? → Answer, re-delegate (max 1 round)
- Blocker? → Resolve, re-delegate
- Success? → Verify compliance for this subsystem:

**Per-subsystem compliance check (do NOT proceed until pass):**
1. **Acceptance criteria met?** Check each FR assigned to this subsystem against its acceptance criteria in the coverage matrix
2. **MUST statements verified?** For any MUST/CRITICAL statements related to this subsystem, trace code path to confirm
3. **Numeric constraints correct?** Verify any numbers/limits for this subsystem match PRD intent
4. **Tests pass?** All tests for this subsystem must pass
5. **Output format verified?** If PRD provides example outputs (logs, reports, files), compare actual output character-by-character against examples
6. **Data model edge cases?** Verify data structures capture all fields needed for reporting across ALL status outcomes (success, warning, error, edge cases)
7. **Requirement applied to all code paths?** If a requirement affects multiple code paths (e.g., encoding for console, file, diagnostic output), verify ALL paths implement it

**If any check fails:** Fix directly or re-delegate with specific feedback. Max 2 re-delegation rounds per subsystem.

**Output:** "✓ <subsystem>: N tests passing, acceptance criteria verified for FR-X, FR-Y"

### 4. Integration (main agent writes directly)

**Pre-gate:**
1. Verify test files exist for each subsystem
2. Run test discovery to confirm tests are found
3. If tests missing → delegate test creation first

**Write entry point:**
- Create main entry point per architecture.md (e.g., `main.py`, `index.ts`, `main.go`)
- Import public APIs from all subsystems
- Wire together per the data flow defined in architecture.md
- Handle CLI args if specified in PRD

**FR-tagged export verification (CRITICAL):**
- Review exports from each subsystem, especially those tagged with FRs
- For each FR-tagged export: verify it is imported AND called in the pipeline
- If a simpler variant exists (e.g., `map_columns` vs `map_columns_with_subheader`), use the FR-tagged one
- Example: FR9 requires multi-row headers → must use `map_columns_with_subheader`, not `map_columns`

**For complex entry points:** If entry point requires >100 lines or has its own FRs (e.g., FR66: CLI handling), delegate via Task tool instead of writing directly.

**Verify (use stack-appropriate tools from architecture.md):**
1. Tests pass (e.g., `pytest`, `npm test`, `go test`)
2. Type check passes (e.g., `pyright`, `tsc`, `mypy`)
3. Lint passes (e.g., `ruff`, `eslint`, `golint`)
4. All FR-tagged exports are actually called in the pipeline
5. All FRs accounted for? Scan coverage matrix - every FR should be checked off
6. Cross-subsystem MUST statements? Verify any that span multiple subsystems

**Output:** "✓ Integration: N tests, N/N FRs, checks pass"

**If gaps found:** Return to Step 3 for the affected subsystem.

### 5. Real Data Validation (delegate)

**Skip if:** Pure library with no entry point AND no test data files exist.

**Pre-check:** Look for inputs in data/, samples/, test_data/, fixtures/

**Delegate via Task tool (subagent_type="general-purpose").**
See **Appendix B** for template. Fill in:
- Entry point and input path
- Expected behavior (what the tool does with inputs)
- **Include PRD examples** that mention specific files or data patterns

**Output:** "✓ Validation: N/M passed (X input_issues)"

**If fixes applied:** Re-run tests to verify no regressions.

**IMPORTANT:** If validation reveals missing functionality that PRD specified, return to Step 3 and fix.

### 6. Code Simplification (delegate) - Skip at this moment

**Delegate via Task tool (subagent_type="general-purpose"):**

```
Simplify: <src_path>

Rules:
- Remove dead code (unused imports, unreachable branches)
- Flatten nested logic >3 levels
- Extract functions >20 lines
- Run tests after changes

Return: {files_modified: N, tests_pass: bool}
```

**Output:** "✓ Simplified: N files, tests pass"

### 7. Build & Docs - Skip at this moment

**Build (if specified in architecture.md):**
- Look for "Build" or "Distribution" section
- Run build command, validate output

**Documentation:**
- Update README.md (setup, test, structure)
- Write docs/user_guide.md (non-technical perspective)

**Output:** "✓ Build: [path]" / "✓ Docs updated"

### 8. Commit - Skip at this moment
i 
Use project convention if specified, else: `feat: implement [PRD name]`

### 9. Summary

```
## Complete
Subsystems: N (each verified in Step 3)
FRs: N/N covered | Tests: N passing
Validation: N/M | Build: [status]
```

**If any gaps found:** This indicates Step 3 gates were not enforced - each subsystem should have been verified before proceeding.

---

## Appendix A: Subsystem Delegation Template

```
Implement & test: <subsystem_name>
Module: <path> | Tests: <test_path>

Dependencies (ONLY import from these, no peer subsystems):
- <module>: <exports>

Stack: <language version | test framework | linter> (from architecture.md)

Style:
- Type annotations on all functions (per language idioms)
- Docstrings/comments per project style guide
- Max 500 lines/file

Architecture:
<relevant pattern excerpt from architecture.md>

Data Models:
Input: <type definitions this subsystem receives>
Output: <type definitions this subsystem produces>
Internal: <any internal types if needed>

Interfaces (implement these exact signatures):
- func(param: type) -> type: "purpose"
  Example: func(x) → y

Error Handling:
- <what errors to raise, edge cases to handle per PRD>

FRs (implement EXACTLY as specified):
- FR-XXX: <full requirement text>
- Include ALL input→output examples from PRD for this FR

NFRs (if applicable):
- <performance, validation, or other non-functional requirements>

Tasks:
1. If requirements unclear → return {questions: [...]} and STOP
2. Write tests covering FRs, interfaces, edge cases, and every PRD example
3. Implement to pass tests (TDD)
4. Add PRD line references in code comments for non-obvious logic
5. Type check → lint → fix all issues (use tools from Stack)
6. Verify data models capture fields needed for ALL outcomes (success/warning/error)
7. If requirement affects multiple code paths → verify ALL paths implement it

Gates: tests pass, lint clean, types clean, interfaces match, all PRD examples tested, all code paths covered, PRD traceability in comments

Return: {
  tests: N passing,
  exports: [
    {func: "func_name", fr: "FR-XX"},  // FR-specific function
    {func: "helper_func", fr: null}     // General helper, no specific FR
  ],
  blockers: [...]
}

Note: Tag exports with the FR they implement. This ensures integration uses the correct function for each requirement.
```

## Appendix B: Data Validation Template

```
Validate: <entry_point>
Inputs: <data_path>
PRD: docs/PRD.md

Expected behavior:
<brief description of what the tool should do with inputs>

Classification rules:
- code_bug: PRD says this case SHOULD be handled, but code fails
- input_issue: genuinely malformed data AND PRD is silent on handling it

Tasks:
1. Run against ALL test inputs, capture results
2. For each failure:
   - Inspect the input file
   - Trace code path
   - Check PRD: does it require handling this case?
   - Classify as code_bug or input_issue
3. Fix code_bugs (only modify src/, not config)
4. Re-run tests after each fix
5. Max 3 fix iterations

Constraints:
- Do NOT modify config files
- Default to code_bug if unsure

Return: {passed: N, bugs_fixed: N, input_issues: N, fixes: ["summary1", ...]}
```
