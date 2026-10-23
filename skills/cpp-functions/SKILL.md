---
name: cpp-functions
description: "C++ function design: one operation, short functions, constexpr, pure functions, parameter passing (value, const&, sink), return values instead of out parameters, parameter count, references versus pointers, branching, recursion. Read when you write or change a function."
disable-model-invocation: true
---

# Functions


| Rule | Summary |
|------|---------|
| **F.2** | One function, one logical operation |
| **F.3** | Keep functions short. Aim for under 70 lines (TigerStyle). Splitting a long function usually reveals the pieces it was made of |
| **F.4** | If it can run at compile time, make it `constexpr` |
| **F.8** | Prefer pure functions; keep leaf functions pure |
| **F.16** | Pass cheap-to-copy types by value, larger types by `const&`. Pass by value when the function keeps its own copy (a sink) |
| **F.20 / F.21** | Return values, not output parameters. Return a struct for several values |
| **F.43** | Never return a pointer or reference to a local |
| **I.23** | Few parameters. Two neighboring parameters of the same type are easy to swap at the call site; use a struct or a distinct type |

- **References by default.** A reference is never null. Use a raw pointer
  only when null is a valid state, and then it never owns anything.
- **Push `if`s up and `for`s down.** Keep the branching in the parent
  function and move the straight-line work into helpers.
- **Split compound conditions** into nested `if`s when that makes it
  clearer which cases are handled. State conditions positively: prefer
  `index < count` to `!(index >= count)`.
- **Pass options to library calls explicitly** at the call site (flags,
  timeouts, `O_CLOEXEC`), instead of relying on defaults that could change.

```cpp
struct RateWindow
{
  double start_s_{};
  double end_s_{};
};

// Cheap types by value. The two doubles travel together in a struct, so
// a caller can't swap start and end.
[[nodiscard]] double Rate(std::uint64_t p_delta, RateWindow p_window);

// Large and read-only: const reference.
[[nodiscard]] Json Snapshot(const Engine& p_engine);

// A sink: by value, then moved into place.
void SetName(std::string p_name);
```

Avoid these:

- returning `T&&` or `const T` by value (a `const` return value can't be
  moved from);
- C-style variadics (`va_arg`). Use `std::format` or a variadic template;
- a lambda that captures by reference and is handed to another thread;
- recursion over data that comes from outside the process, because its
  depth has no bound. Use a loop with an explicit limit. A recursive parser
  must carry a depth limit.
