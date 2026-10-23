---
name: cpp-expressions-and-statements
description: "C++ expressions and statements: scope, initialization, {} versus (), magic numbers, narrowing, nullptr, casts, signed and unsigned comparison, index, count, and size. Read when you declare variables, convert types, or do integer arithmetic."
disable-model-invocation: true
---

# Expressions and statements


| Rule | Summary |
|------|---------|
| **ES.5** | Keep scopes small; declare a variable where it is first needed |
| **ES.20** | Always initialize |
| **ES.23** | Prefer `{}` initialization (but see below) |
| **ES.25** | `const` / `constexpr` unless the value changes |
| **ES.45** | No magic numbers; use named constants |
| **ES.46** | No narrowing. The build uses `-Wconversion` |
| **ES.47** | `nullptr`, never `0` or `NULL` |
| **ES.48 / ES.50** | No C-style casts; use the named casts or `std::bit_cast`. Never cast away `const` |

`{}` and `()` differ for containers: `std::vector<int>{3}` holds one
element, the value 3, while `std::vector<int>(3)` holds three zeros. Use `()`
when you mean the size.

Mixing signed and unsigned values is a common bug. Use `std::cmp_less` and
the other comparison helpers from `<utility>`, or make the conversion
explicit with a `static_cast` and a reason.

**Index, count and size are different things** (TigerStyle). An index is
0-based and a count is 1-based, so going from one to the other needs a `+
1`. A size is a count times a unit. Name the variables so the difference
shows (`slot_index`, `slot_count`, `buffer_bytes`). When integer division
rounds, make it visible which way and why.
