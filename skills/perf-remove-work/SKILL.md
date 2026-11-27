---
name: perf-remove-work
description: "The first fix for a bottleneck: decide whether the work is needed at all, and remove, skip, cache, precompute, conflate, batch, or move it before you make it faster. Lists the common kinds of unnecessary work and how to prove that a removal is safe. Read after the bottleneck report and before any micro-optimization."
disable-model-invocation: true
---

# Remove unnecessary work

The fastest code is code that does not run. Before you make a bottleneck
faster, ask whether it must run at all, as often, or at this place. A removal
is usually simpler than an optimization, and it often removes allocations,
system calls, and cache misses at the same time.

## 1. Ask these questions, in this order

For each bottleneck in the report (`perf-optimization`, step 3):

1. **Who uses the result?** Find every reader. If nobody reads it, delete it.
2. **How often does the reader need it?** If the writer produces a result for
   each event and the reader samples it every 20 ms, almost all results are
   thrown away. Produce it at the rate of the reader.
3. **Is it already known?** The value can be computed once at startup, kept
   from the last time, or derived from data that the code already has.
4. **Is the full result needed?** Maybe only the top N, only the changed part,
   only a count, or only a yes or no.
5. **Must it happen now, on this thread?** Maybe it can happen later, in a
   batch, on another thread, at build time, or offline.
6. **Is there a simpler way?** A different algorithm, a library call, or a
   change to the requirement can remove the work.

Stop at the first answer that removes the work. Only if all six answers are
"yes, it is needed here and now", go to `perf-memory`, `perf-io`, `perf-cpu`,
or `perf-data-oriented-design`.

## 2. Common kinds of unnecessary work

| Kind | Sign in a profile | Fix |
| --- | --- | --- |
| Work for each event that a slow reader samples | A publish, snapshot, or copy for each event; the reader polls on a timer | Mark it dirty; publish when idle or after N events (conflation) |
| The same computation again | The same function with the same input in many samples | Compute once; cache with a bounded size; precompute at startup |
| Copies | `memcpy`, copy constructors, `std::string` construction in the profile | Pass by reference or `std::span` / `std::string_view`; move; build in place |
| Formatting and logging on the hot path | `std::format`, `snprintf`, stream operators, log calls | Log binary values or counters; format on another thread; log less |
| Checks done twice | The same validation in the caller and the callee | Validate once at the boundary; trust the type after that |
| One system call for each item | `strace -c` count equal to the item count | Batch (`perf-io`) |
| Polling for work that rarely comes | A loop that checks an empty source | Wait on an event, or poll less often when idle |
| Zeroing or initializing memory that is overwritten | `memset` in the profile | Initialize only what is read; reuse buffers |
| Conversions back and forth | Parse, then format, then parse again | Keep one representation |
| Sorting or searching data that is already ordered | Sort calls on data from an ordered source | Keep the order; merge instead of sort |
| Work for a feature that is off | Code paths that run with an option disabled | Check the option once, outside the loop |
| Debug or statistics code in release builds | Counters, asserts, or timers in hot loops | Keep the cheap ones; remove or sample the rest |

## 3. Ways to remove or move work

- **Delete:** the result has no reader.
- **Skip:** check a cheap condition first (a dirty flag, a size, a version
  number) and do nothing when nothing changed.
- **Cache:** keep the last result with its input. Give the cache a size limit
  and a clear rule for when it becomes invalid.
- **Precompute:** do the work at startup, at configuration load, or at build
  time (`constexpr`, generated tables).
- **Conflate:** many updates to the same thing, one publish. Keep a dirty
  list with fixed capacity, publish when the input queue is empty, and also
  after at most N events so that a busy system still publishes.
- **Batch:** handle N items with one fixed cost (one system call, one lock,
  one cache warm-up).
- **Defer:** do it after the latency-critical reply, or when idle.
- **Move:** to another thread, process, or machine that has spare capacity.
  The handoff costs something; measure that it is less than the work.
- **Change the requirement:** ask whether the result must be exact, complete,
  or this fresh. A depth view that is 5 µs old is as good as a new one for a
  screen that redraws every 20 ms.

## 4. Prove that the removal is safe

A removal changes behavior when someone used the result. Before you remove:

- Find the readers: search for the function, the field, and the output.
- Write a test for the behavior that must stay, for example "the reader sees
  the final state after a burst".
- Write a test for the limit that you introduce, for example "a view is at
  most N events old". Check that the test fails when you break the limit.
- Measure the gain with the benchmark (`perf-benchmarks`) and the A/B rules
  (`perf-profiling`, section 9).

Real case: an exchange engine published a 20-level market depth after every
order. The feed thread read it every 20 ms. Publishing once per batch (when
the queue was empty, or after 64 commands) cut the engine cost from 206 to
107 ns per command. Two tests guard it: one for the final state after a
burst, and one for the 64-command limit.

## Related skills

- `principle-subtract-before-you-add`: the same rule for any change.
- `no-parts-is-best-parts`: does this part need to exist?
