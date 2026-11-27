---
name: perf-benchmarks
description: "Design tests that detect and measure performance problems: pick the level (micro, component, end to end), make the workload realistic, check what saturates, get stable numbers, and guard results with deterministic regression tests (allocation, system call, and instruction counts). Read before you write or change a benchmark or a performance test, or when a benchmark result looks wrong."
disable-model-invocation: true
---

# Performance tests and benchmarks

A benchmark is a measuring instrument. Before you trust it, prove that it
measures the code under test, that its numbers repeat, and that it can detect
a known regression.

## 1. Choose the level

| Level | Measures | Good for | Risk |
| --- | --- | --- | --- |
| Micro | One function or data structure in a loop | Comparing two implementations | The compiler removes the work; caches are warmer than in production. |
| Component | One thread or subsystem with its real inputs (for example, one engine fed from a queue) | Cost per event of a real path | Misses the cost of the other threads. |
| End to end | The whole system with load generators | Throughput and latency that users see | The load generator, the network, or the host can saturate first. |

Use more than one level. An end-to-end test shows whether a change matters to
users. A component test shows the cost of the code, even when the end-to-end
test is limited by something else.

## 2. Check what saturates

For each end-to-end benchmark, measure the CPU use of every process and
thread (`thread_cpu.sh` in `perf-profiling`, section 5). If a load generator or the host
saturates first, the result measures the harness. Then:

- Give the load generators more cores, or make them cheaper.
- Or add a component benchmark that drives the code under test directly.

Real case: an exchange test with 4 load generators on 3 cores showed the same
throughput before and after a change that halved the engine cost. A component
benchmark of the engine showed 206 ns against 107 ns for each command.

## 3. Make the workload realistic

- Use the production mix of operations, sizes, and key patterns. Reuse the
  generator of the load tool if one exists, so both tests use the same mix.
- Use production sizes for tables and pools. A table that fits in L2 cache
  hides the cache misses of a production-size table. Run at both sizes when
  the size can matter.
- Reach the steady state before you time it: fill pools and queues to their
  normal level, and warm the caches.
- Include the optional features that production turns on (for example, a
  market data feed), as separate rows.

## 4. Get stable numbers

- Build with the release flags. Pin the process to one core (`taskset -c N`).
  Keep the machine quiet.
- Take the median of 5 or more runs. Report the spread (minimum and maximum,
  or the `perf stat -r` `+-` value).
- For latency, record each sample in a preallocated array or an HDR
  histogram, and report the percentiles (p50, p99, p99.9, max). Do not report
  only the mean. The clock read costs about 20 ns; for very short
  operations, time a batch and divide.
- **Avoid coordinated omission.** A closed-loop load generator that waits for
  each reply sends less during a stall, so it records few slow samples and
  hides the stall. For latency, use an open loop: send on a fixed schedule,
  and measure from the scheduled send time, not the actual send time
  ([Gil Tene](https://groups.google.com/g/mechanical-sympathy/c/icNZJejUHfE)).
  Use a closed loop to measure capacity, not latency.
- Stop the compiler from removing the work: use the results (sum them, print
  them), or use `benchmark::DoNotOptimize` and `benchmark::ClobberMemory`
  from [Google Benchmark](https://github.com/google/benchmark). A library
  such as Google Benchmark or [nanobench](https://github.com/martinus/nanobench)
  also handles iteration counts and warm-up.
- Interleave A and B runs. Do not run all A runs, then all B runs: the host
  state drifts.

## 5. Guard results with deterministic tests

Timing tests are noisy in CI. Guard the cause of a gain with a count that does
not depend on the machine. The test fails when a change brings the cost back.

| Guard | How | Catches |
| --- | --- | --- |
| Allocation count | Replace `operator new` in the test binary and count calls during the steady state. Expect 0. | An allocation on the hot path |
| System call count | `strace -c -f <cmd>` in a test, or count the calls in a wrapper | A lost batch (one call per item) |
| Instruction count | `valgrind --tool=cachegrind` (Ir), or `perf stat -e instructions:u` | Extra work, with less noise than time |
| Work count | A counter in the code (publishes, copies, lookups for each event) | Work that comes back, for example one publish per event |
| Smoke run | Run each benchmark with a small count in the normal test suite | A benchmark that no longer builds or runs |

Check that each guard can fail. Break the code on purpose once (remove the
batch, add an allocation), and see the guard fail for the intended reason.

Instruction counts vary by well under 1% between runs, even on a busy CI
host, while wall time can vary by much more
([Rust compiler performance discussion](https://internals.rust-lang.org/t/what-is-perf-rust-lang-org-measuring-and-why-is-instructions-u-the-default/9815)).
They do not see cache misses, branch mispredictions, or slow instructions,
so a change can add time without adding instructions. Use them as a gate
next to the other guards, not alone.

Keep CI gates coarse: gate on a few end-to-end or component counts. Gating
on every microbenchmark gives so many false alarms that people stop reading
them. Use the microbenchmarks to find the cause of a regression.

## 6. Calibrate

Before you trust a "no difference" result, show that the benchmark detects a
difference of the size that you care about. Add a known cost (for example, an
extra copy or a sleep of known length) and check that the numbers move by
that amount.

## 7. Keep it

- Keep the benchmark in the repository, built by the normal build, with a
  smoke run in the test suite.
- Write the result next to it: the date, the machine, the build flags, the
  command, and the numbers.
