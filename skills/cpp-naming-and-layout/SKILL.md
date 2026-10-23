---
name: cpp-naming-and-layout
description: "C++ naming and layout: functions, p_ parameters, locals, types, trailing _ members, k constants, enumerators, namespaces, macros, files, Allman braces, indentation, units in names, abbreviations. Read when you name or format anything in C++."
disable-model-invocation: true
---

# Naming and layout


These match `$HOME/ai/conventions/cpp.md`, and they take precedence over
Google style.

| Kind | Convention | Example |
|------|------------|---------|
| Functions and methods | PascalCase | `DecodePacket`, `WriteRollup` |
| Function parameters | `p_` + snake_case, every named parameter (free functions, methods, lambdas) | `p_packet`, `p_day` |
| Local variables | snake_case | `thread_count` |
| Classes, structs, aliases, template parameters | PascalCase | `Engine`, `Record`, `TNumber` |
| Class and struct data members | snake_case + trailing `_` | `tid_`, `last_seen_` |
| Constants and `constexpr` | `k` + PascalCase | `kMaxDatagramBytes` |
| Enumerators | PascalCase, no `k`; the first one has an explicit initializer | `LogLevel::Info`, `Debug = 0` |
| Namespaces | lowercase, underscores between words | `triangulator` |
| Macros | avoid; if needed, `ALL_CAPS` | `TRIANGULATOR_VERSION` |
| Files | lowercase, underscores; `.hpp` / `.cpp` | `storage.hpp` |

- **Braces:** Allman. Every `{` and `}` sits on its own line.
- **Braces are mandatory** on every `if` / `else` / `for` / `while`, even
  when the body is one statement.
- **Indentation:** 2 spaces, never tabs. Run `make format`. `make
  format-check` fails if the code has drifted from `.clang-format`.
- **Units go last in a name** (TigerStyle): `interval_ms`, `latency_ms_max`
  and `latency_ms_min`. Related names then line up and sort together.
- **No abbreviations** unless they're standard in the domain (`tid`, `pid`,
  `fd`, `io`).
- **Structs are passive aggregates.** If a type has an invariant to
  protect, make it a `class`. The trailing `_` on struct members keeps them
  consistent with class members. It doesn't mean the struct hides anything.
