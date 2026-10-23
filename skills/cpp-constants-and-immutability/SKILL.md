---
name: cpp-constants-and-immutability
description: "C++ const and constexpr: const by default, const member functions, k constants, immutable members without const. Read when you decide whether a value or member can change."
disable-model-invocation: true
---

# Constants and immutability


- Objects are `const` by default (Con.1). Member functions are `const`
  unless they change the object (Con.2).
- Use `constexpr` for anything that can be computed at compile time
  (Con.5), with a `k` prefix: `constexpr std::size_t kMaxDatagramBytes =
  65'507;`.
- A member that must not change after construction: make it private with
  no setter, rather than a `const` member (see the `cpp-classes-and-composition` skill).
