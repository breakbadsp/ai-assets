---
name: cpp-assertions
description: "C++ assertions: assert and static_assert for programmer errors, split compound assertions, never assert on external input. Read when you check invariants, preconditions, or build-time facts."
disable-model-invocation: true
---

# Assertions


Assertions catch programmer errors (TigerStyle). Our Makefile doesn't
define `NDEBUG`, so `assert` stays enabled in the shipped binaries.

- Assert preconditions, postconditions and invariants that a bug could
  break. Examples: an index you're about to use is in range, a state
  machine is in an allowed state, a count stays under its limit.
- Assert both sides of a boundary. Assert what you expect to hold, and
  also what must not happen.
- Split compound assertions: write `assert(a); assert(b);`, not
  `assert(a && b);`. When one fails, the message shows which condition was
  false.
- Use `static_assert` for facts about the build: a wire-struct size, a
  limit that relates to another limit, `std::is_trivially_copyable_v`.
- **Never assert on input from outside the process**: datagrams, files,
  `/proc`, HTTP requests, config. Those are operating errors and get a
  `std::expected`. A sampler on another host must never be able to crash
  the collector.
- An assertion must have no side effects.

```cpp
static_assert(sizeof(WireHeader) == 24, "the wire format is fixed");
static_assert(kMaxThreads <= std::numeric_limits<std::uint16_t>::max());

void ThreadTable::Erase(std::size_t p_slot)
{
  assert(p_slot < slots_.size());
  assert(slots_[p_slot].live_);
  // ...
}
```

C++26 contracts (`pre`, `post`, `contract_assert`) would replace some of
this, but only GCC implements them so far. We'll keep using `assert` until
both of our compilers support contracts.
