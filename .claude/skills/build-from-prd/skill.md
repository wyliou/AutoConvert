---
name: build-from-prd
description: Implement a PRD with subagent delegation
---

# Build from PRD

## Role & Output Style

**You are a Tech Lead.** You plan, delegate, and integrate. You do NOT implement subsystems.

**Output:** Terse. Use "Step N complete" format. Minimize verbose explanations.

## What You Do vs Delegate

| Action | You | Subagent |
|--------|:---:|:--------:|
| Read PRD/architecture docs | Y | - |
| Create task list (TaskCreate) | Y | - |
| Scaffold (dirs, init files, manifest) | Y | - |
| Write subsystem code | - | Y |
| Write tests | - | Y |
| Write entry point / pipeline | Y | - |
| Run commands (test, lint) | Y | Y |

**Enforcement:** Do NOT edit `src/**/*.py` files except: `__init__.py`, `main.py`, `__main__.py`, pipeline/orchestration files. All other source files must be delegated via Task tool.

---

## Workflow

### 1. Pre-flight & Plan

**1.1 Verify docs exist:**
```
ls docs/PRD.md docs/architecture.md
```
If missing: STOP, notify user.

**1.2 Read and extract:**

From PRD.md (for each subsystem):
- FRs: full text including tables, formats, codes
- NFRs: performance, validation requirements
- Error cases and edge cases
- Input/output examples
- MUST/CRITICAL statements (non-negotiable requirements)
- Numeric constraints with units

From architecture.md:
- Tech stack, dependencies
- Data models per subsystem
- Interface signatures
- **Subsystem dependency graph**

**1.3 Define interfaces (BEFORE delegation):**
```
<subsystem> interfaces:
- func(param: type) -> type: "purpose"
```

**1.4 Map FRs to subsystems:**

| FR | Subsystem | Acceptance Criteria |
|----|-----------|---------------------|
| FR-XX | parser | Valid files return DataFrame |

**GATE:** Every FR must have subsystem + acceptance criteria. Stop if any unmapped.

**1.5 Build dependency table:**

| Subsystem | Dependencies | Batch |
|-----------|--------------|-------|
| config | (none) | 1 |
| parser | config | 2 |
| validator | config | 2 |
| transformer | parser, validator | 3 |

Rules for batching:
- Batch 1: subsystems with no dependencies
- Batch N: subsystems whose ALL dependencies are in batches < N
- Max 3 subsystems per batch (parallel limit)

**1.6 Check existing structure:**
```
ls -la
```

**1.7 Create task list via TaskCreate:**
```
1. Scaffold (if needed)
2. Batch 1: <subsystem_a>
3. Batch 2: <subsystem_b>, <subsystem_c>  [parallel]
4. Batch 3: <subsystem_d>
...
N. Integration
N+1. Real data validation
N+2. Final verification
```

**Output:** "Plan complete: X FRs, Y subsystems, Z batches"

---

### 2. Scaffold (if needed)

**Skip if ALL exist:** manifest, subsystem dirs, init files.

**Otherwise create:**
- Directory structure per architecture.md
- pyproject.toml / package.json / go.mod
- `__init__.py` / index files
- Run dependency install (`uv sync`, `npm install`, etc.)

**Output:** "Scaffold complete" or "Scaffold skipped"

---

### 3. Implement & Test (delegate by batch)

Process batches in order. Within each batch, delegate in parallel.

#### Parallel Execution Rules

| Rule | Description |
|------|-------------|
| Max concurrency | 3 subagents per batch |
| Dependency respect | Never start subsystem before its dependencies complete |
| No file conflicts | Verify no two subsystems in same batch write to same file |
| Batch completion | Wait for ALL subagents in batch before starting next |

#### Pre-batch: Update Dependency Status

Before each batch, update the table:

| Subsystem | Dependencies | Status |
|-----------|--------------|--------|
| config | (none) | done |
| parser | config | ready |
| validator | config | ready |
| transformer | parser, validator | blocked |

Status: `done` = complete, `ready` = deps satisfied, `blocked` = deps pending

#### Delegation Template

For each subsystem, delegate via Task tool (subagent_type="general-purpose"):

```
Implement & test: <subsystem_name>
Module: <path> | Tests: <test_path>

Dependencies (import ONLY from these):
- <module>: <exports>

Stack: <language | test framework | linter>

Interfaces (implement these exact signatures):
- func(param: type) -> type: "purpose"

Data Models:
- Input: <type>
- Output: <type>

FRs (implement EXACTLY as specified):
- FR-XXX: <full requirement text with examples>

Error Handling:
- <what errors to raise, edge cases per PRD>

Tasks:
1. If unclear: return {questions: [...]} and STOP
2. Write tests covering FRs, interfaces, edge cases
3. Implement to pass tests (TDD)
4. Type check -> lint -> fix all issues
5. Verify output format matches PRD examples exactly

Gates: tests pass, lint clean, types clean, interfaces match

Return: {
  tests: N passing,
  exports: [{func: "name", fr: "FR-XX"}],
  blockers: [...]
}
```

#### Parallel Batch Execution

**For each batch with multiple ready subsystems:**

1. **Conflict check:** Verify no file write conflicts between subsystems
2. **Launch parallel:** Send ALL Task tool calls in a single message
   ```
   [Task: subsystem_a] [Task: subsystem_b] [Task: subsystem_c]
   ```
3. **Wait for all:** Collect all results before proceeding
4. **Process results:** Handle each result (see below)

#### Result Handling

| Result | Action |
|--------|--------|
| Questions | Queue for answer, re-delegate after batch |
| Blocker | Queue for resolution, re-delegate after batch |
| Success | Verify, update export registry |

#### Batch Failure Handling

| Scenario | Action |
|----------|--------|
| 1 agent fails | Continue others, retry failed one in next round |
| 2+ agents fail | Pause, ask user whether to continue or debug |
| Max retries (2) | Escalate to user |

#### Per-subsystem Verification (3 checks)

1. Tests pass for this subsystem
2. Acceptance criteria met for assigned FRs
3. Output format matches PRD examples (if applicable)

**If any check fails:** Queue for re-delegation in next round. Max 2 rounds per subsystem.

#### Export Registry

Track FR-tagged exports from each completed subsystem:

```
Export Registry:
- config: [{func: "load_config", fr: "FR-1"}]
- parser: [{func: "parse_file", fr: "FR-5"}, {func: "parse_header", fr: "FR-6"}]
```

Use this registry in Step 4 to verify all FR functions are called.

**Output per batch:** "Batch N: <sub1> (X tests), <sub2> (Y tests)"

**Output when all batches complete:** "Implementation: N subsystems, M total tests"

---

### 4. Integration

**Pre-gate:**
1. Verify test files exist per stack convention
2. Run test discovery per stack (e.g., `pytest --collect-only`, `npm test --listTests`, `go test -list .`)
3. If tests missing: delegate test creation first

**Write entry point (you write this directly):**
- Create entry point per architecture.md (e.g., `main.py`, `index.ts`, `cmd/main.go`)
- Import public APIs from all subsystems
- Wire together per data flow in architecture.md
- Handle CLI args if specified

**FR-tagged export verification (use Export Registry):**
- For each FR-tagged export: verify it's imported AND called
- If simpler variant exists alongside FR-tagged one: use the FR-tagged function
- Check: `All exports with fr != null must be called`

**Verify (use commands from architecture.md tech stack):**
1. Test command - all tests pass
2. Type check command - passes (if applicable)
3. Lint command - passes
4. All FRs accounted for in coverage matrix

**Output:** "Integration: N tests, N/N FRs, checks pass"

**If gaps found:** Return to Step 3 for affected subsystem.

---

### 5. Real Data Validation

**Skip ONLY if:** Pure library with no entry point AND no test data exists.

**Check for inputs:** `ls data/ samples/ test_data/ fixtures/`

**Delegate validation:**

```
Validate: <entry_point>
Inputs: <data_path>

Expected behavior: <what the tool does>

Classification:
- code_bug: PRD says handle this case, code fails
- input_issue: genuinely malformed AND PRD silent on it

Tasks:
1. Run against ALL test inputs
2. For each failure: inspect input, trace code, check PRD
3. Classify as code_bug or input_issue
4. Fix code_bugs (src/ only, not config)
5. Re-run tests after each fix
6. Max 3 fix iterations

Return: {passed: N, bugs_fixed: N, input_issues: N}
```

**Output:** "Validation: N/M passed (X input_issues)"

**If bugs fixed:** Re-run tests to verify no regressions.

---

### 6. Final Verification

**PRD compliance spot-check:**
1. Pick 2-3 high-risk FRs (complex logic, multiple conditions)
2. Trace code path for each
3. Verify output matches PRD specification exactly

**If issues found:** Fix directly or re-delegate, then re-validate.

**Output:** "Verified: N FRs spot-checked"

---

### 7. Summary

```
## Complete
Subsystems: N (in B batches) | FRs: N/N covered
Tests: N passing | Validation: N/M inputs
```

---

## Recovery Procedures

**Subagent returns questions:**
1. Answer based on PRD/architecture
2. If PRD unclear: ask user via AskUserQuestion
3. Re-delegate with clarified requirements

**Subagent blocked:**
1. Check if dependency issue (wrong batch order)
2. Check if missing context (add to prompt)
3. If infrastructure issue: resolve directly, then re-delegate

**Parallel batch partial failure:**
1. Let successful agents complete
2. Collect failures and analyze common cause
3. If related failures: fix root cause, re-delegate all
4. If unrelated: re-delegate individually in next round

**Tests failing after integration:**
1. Identify which subsystem's tests fail
2. Check if integration broke existing functionality
3. Fix integration code OR re-delegate subsystem fix

**Validation finds bugs:**
1. Classify: is it subsystem logic or integration wiring?
2. Subsystem logic: re-delegate to that subsystem
3. Integration wiring: fix directly

---

## Gates Summary

| Gate | Location | Fail Action |
|------|----------|-------------|
| Docs exist | Step 1.1 | STOP, notify user |
| All FRs mapped | Step 1.4 | STOP, resolve mapping |
| No batch conflicts | Step 3 pre-batch | Run conflicting subsystems sequentially |
| Tests exist per subsystem | Step 3 post-delegation | Reject, re-delegate |
| Verification pass | Step 3 post-delegation | Re-delegate (max 2x) |
| Test files exist | Step 4 pre-gate | Delegate test creation |
| All FR exports called | Step 4 verify | Add missing calls |
| All checks pass | Step 4 verify | Fix or return to Step 3 |
| Validation pass | Step 5 | Fix bugs, re-validate |

---

## Quick Reference: Parallel vs Sequential

**Use parallel (default):** When dependency graph allows independent subsystems

**Force sequential:** When:
- Subsystems have subtle data format dependencies not in architecture.md
- Shared test fixtures that could conflict
- User explicitly requests sequential

**Batch size guidance:**
- 2-3 subsystems: parallelize all independent ones
- 4-6 subsystems: 2-3 batches typical
- 7+ subsystems: consider if architecture needs simplification
