---
name: cpp-principles
description: "C++ core principles and the base of the C++ standards (C++ Core Guidelines, TigerStyle, deliberate differences). Read at the start of any C++ writing, editing, or review."
disable-model-invocation: true
---

# C++ coding standards

How C++ is written in this repository: the sampler (`sampler/`), the core
collector (`collector/`) and the C++ tests (`tests/*.cpp`).

The base is the [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines),
with ideas from [TigerStyle](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md).
This document differs from both on purpose in four places, and says so each
time:

1. **Errors are values.** Fallible functions return `std::expected` or
   `std::optional`. Exceptions are kept only in the few places listed in the
   `cpp-error-handling` skill.
2. **Our own naming** (PascalCase functions, `p_` parameters), not the
   Guidelines' `snake_case`.
3. **Allman braces and 2-space indentation**, enforced by `.clang-format`.
4. **A hot-path section** for the code that handles every datagram.

Adapted from `docs/cpp-coding-standards.md`, `docs/naming-conventions.md`
and `prep/TIGER_STYLE.md` in
[modern_exchng_cpp](https://github.com/breakbadsp/modern_exchng_cpp).
`upstream-differences.md` lists what changed and why.

## Principles


1. **Simple first.** Simple code is easier to get right, and easier to make
   fast after that. Pick the obvious solution unless a measurement says
   otherwise.
2. **RAII for every resource.** Every file descriptor, socket, SQLite handle,
   thread and lock belongs to an object that releases it.
3. **Errors are values.** See the `cpp-error-handling` skill.
4. **Composition before inheritance.** Inherit only for a real "is-a"
   interface with runtime polymorphism.
5. **Immutable by default.** Start with `const` / `constexpr` and make
   something mutable only when it has to change.
6. **Let the type system catch mistakes.** Prefer compile-time checks to
   runtime checks.
7. **Put a limit on everything.** Every loop, queue, buffer and cache has
   an upper bound (TigerStyle).
8. **Always say why.** A comment explains why the code is written this way,
   not what it does.
