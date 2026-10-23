---
name: cpp-standard-library
description: "C++ standard library choices: containers, string versus string_view and span, std::format and std::print, std::unreachable, std::to_underlying, flat_map, new dependencies. Read when you pick a container or text type, format output, or add a dependency."
disable-model-invocation: true
---

# Standard library


- `std::array` / `std::vector` over C arrays. `std::vector` is the default
  container.
- `std::string` owns text; `std::string_view` and `std::span` only look at
  it. Never keep a view after the thing it points into is gone.
- `std::format` / `std::print` instead of `<<` chains and `printf`.
- `std::unreachable()` for a branch that truly can't happen, after a
  `switch` that covers every enumerator. `-Wswitch` then reports a newly
  added enumerator that the `switch` doesn't handle.
- `std::to_underlying(e)` instead of
  `static_cast<std::underlying_type_t<E>>(e)`.
- `std::flat_map` / `std::flat_set` when lookups and iteration far
  outnumber insertions.
- No new third-party dependencies without a good reason. SQLite is the
  only one today.
