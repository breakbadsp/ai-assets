---
name: cpp-hot-path
description: "C++ hot-path performance: measure first, no allocation per datagram, limits on loops and caches, batching, contiguous data, no virtual dispatch or RTTI, likely and unlikely. Read when you change code that runs for every datagram or sample, or make a performance change."
disable-model-invocation: true
---

# The hot path


The hot path is the code that runs for every datagram or every sample:
the sampler's `/proc` reads, packet encode and decode, and the collector's
per-thread state updates. `docs/collector-comparison.md` shows why this
code is in C++. These rules keep it fast.

- **Measure first** (Per.1, Per.2, Per.6). Do a quick estimate of network,
  disk, memory and CPU while designing. After that, change hot code only
  with a measurement, and report the before and after numbers.
- **Don't allocate on every datagram.** Reuse buffers. Set bounds once at
  startup. Keep maps keyed by thread so they don't rebuild on each tick.
  Allocation at startup, and when a new thread first appears, is fine.
- **Put a limit on everything.** Each loop over external data has a maximum
  (threads per packet, bytes per datagram, entries in a cache). Hitting a
  limit is an operating error: count it, log it once, and carry on. The
  collector does not grow without bound because a sampler misbehaves.
- **Batch.** Write rollups to SQLite in transactions, not row by row. Let
  the program run at its own pace instead of doing I/O as a direct reaction
  to each event.
- **Keep data contiguous.** Prefer `std::vector<Record>` to
  `std::vector<std::unique_ptr<Record>>` for anything walked in a loop.
- **No virtual dispatch or RTTI** (`dynamic_cast`, `typeid`) in per-datagram
  code. Use templates or `if constexpr` there.
- **`[[likely]]` / `[[unlikely]]`** only on a branch that a profile showed
  to matter.
