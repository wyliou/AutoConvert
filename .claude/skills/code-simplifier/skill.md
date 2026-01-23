---
name: code-simplifier
description: Simplify and clean up source code files
---

# Code Simplifier

Analyze and simplify source code while preserving functionality.

## Usage

Run on a single file:
```
/code-simplifier path/to/file.py
```

Run on a directory:
```
/code-simplifier src/
```

## Simplification Rules

### 1. Remove Dead Code
- Unused imports
- Unused variables
- Unreachable code blocks
- Commented-out code (unless marked `# TODO` or `# FIXME`)

### 2. Reduce Complexity
- Flatten nested conditionals where possible
- Replace complex boolean expressions with named variables
- Extract repeated logic into helper functions (3+ occurrences)
- Simplify redundant type conversions

### 3. Improve Readability
- Replace magic numbers with named constants
- Simplify overly verbose expressions
- Remove redundant else after return/raise/continue/break

### 4. Consolidate Duplicates
- Merge similar functions with minor differences
- Extract common patterns into utilities
- Remove duplicate validation logic

## Constraints

- **DO NOT** change public API signatures
- **DO NOT** remove code marked with `# KEEP` or `# REQUIRED`
- **DO NOT** simplify test files (files matching `*_test.py`, `test_*.py`, `**/tests/**`)
- **DO NOT** modify configuration files
- **PRESERVE** all existing functionality - simplification must be behavior-preserving

## Process

1. Read the target file(s)
2. Identify simplification opportunities
3. Apply changes incrementally
4. Run linter to verify no errors introduced
5. Report changes made

## Output Format

```
✓ <filename>: <N> simplifications
  - Removed N unused imports
  - Flattened N nested conditionals
  - Extracted N helper functions
  - [other changes]
```

Or if no changes needed:
```
✓ <filename>: already clean
```
