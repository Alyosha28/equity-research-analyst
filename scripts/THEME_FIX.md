# Theme Merge Order Bug Fix

## Bug Summary

The `load_theme()` function in `theme.py` had a critical merge-order bug where parent themes overrode child themes, breaking theme inheritance.

## Root Cause

The function built an inheritance chain from leaf (child) to root (parent):

```
chain = [goldman, default]   # goldman extends default
```

Then it merged by iterating the chain in traversal order:

```python
# BROKEN — parent (default) merges last, overriding child (goldman)
for theme_name in chain:
    resolved = _deep_merge(resolved, themes[theme_name])
```

Because `chain[0]` (child) was merged first and `chain[-1]` (parent) was merged last, the parent's values always won. The leaf theme's overrides were silently discarded.

## Fix

Reverse the chain before merging so the root (most generic) merges first and the leaf (most specific) merges last:

```python
# CORRECT — root merges first, leaf merges last and wins
for theme_name in reversed(chain):
    resolved = _deep_merge(resolved, themes[theme_name])
```

## Test Case

- **default theme**: `accent = "#002D72"` (deep navy)
- **goldman theme**: extends default, `accent = "#003A70"` (Goldman Sachs blue)
- **Expected resolution**: `accent` must be `"#003A70"` (child override wins)
- **Before fix**: `accent` was `"#002D72"` (parent silently won)
- **After fix**: `accent` is `"#003A70"` (child correctly overrides)

## Corrected `merge_theme_chain` Pseudocode

```python
def merge_theme_chain(chain: list[str], themes: dict) -> dict:
    """
    Merge themes from most generic to most specific.

    chain is [child, ..., parent] from leaf to root.
    Reverse so parent merges first (base), child merges last (override winner).
    """
    resolved = {}
    for theme_name in reversed(chain):
        resolved = _deep_merge(resolved, themes[theme_name])
    return resolved
```

## Status

- [x] Bug identified: 2026-06-28
- [x] Fix applied in `theme.py` at line 72 (`reversed(chain)`)
- [ ] Add unit test for nested override with 2+ levels of inheritance
