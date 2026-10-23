---
name: cpp-checklist
description: "C++ completion checklist across all C++ standards skills. Read before you declare C++ work done, and when you review C++ code."
disable-model-invocation: true
---

# Checklist


Before you call C++ work done:

- [ ] `make format-check` and `make check` pass, with `-Werror`
- [ ] Fallible functions return `std::expected`; missing values are
      `std::optional`; both are `[[nodiscard]]`
- [ ] No new `throw` / `try` / `catch` outside the three allowed places
- [ ] No `.value()` on `std::expected` / `std::optional`
- [ ] Assertions for programmer errors; never assertions on external input
- [ ] Every loop, queue and cache over external data has a limit
- [ ] No allocation per datagram on the hot path
- [ ] RAII for every handle; no naked `new` / `delete`
- [ ] Rule of Zero or all five special members
- [ ] Single-argument constructors are `explicit`; leaf classes are `final`
- [ ] Every variable initialized; `const` by default; no magic numbers
- [ ] No narrowing, no C-style casts, `nullptr`
- [ ] Locks are RAII and named; no `detach`
- [ ] PascalCase functions, `p_` parameters, members with a trailing `_`,
      `k` constants, PascalCase enumerators with the first initialized
- [ ] Allman braces, braces on every branch, 2-space indent
