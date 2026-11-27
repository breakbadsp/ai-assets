---
name: perf-cpu
description: "Reduce CPU-bound work: classify the stall with top-down metrics, then remove, reduce, batch, fix branches, vectorize (auto-vectorization, std::simd, intrinsics), parallelize with threads (Amdahl and USL, sharding, pipelines), and use compiler options (-march, LTO, PGO, BOLT). Read when a thread is busy doing real work and the profile points at computation, not waits."
disable-model-invocation: true
---

# CPU-bound work

Make sure the work is needed first (`perf-remove-work`). Then make the needed
work cheaper, in the order of section 2. Each later step costs more code
complexity than the one before it.

## 1. Measure and classify

```bash
perf stat -r 5 -e task-clock,cycles:u,instructions:u,branches:u,branch-misses:u -- <cmd>
perf stat -M TopdownL1 -- <cmd>
perf record -e cycles:u -g --user-callchains -F 999 -o cpu.data -- <cmd>
perf annotate -i cpu.data --stdio -s <hot function>
```

Read the top-down level 1 classes, then act on the largest:

| Class | Meaning | Look at | Typical fixes |
| --- | --- | --- | --- |
| Retiring high, IPC high | The CPU does the instructions fast | Instruction count | Fewer instructions: remove work, better algorithm, SIMD |
| Bad speculation | Branch mispredictions throw work away | `branch-misses`; `perf record -e branch-misses:u` | Predictable branches, branchless code, sorted data (section 4) |
| Frontend bound | The CPU cannot fetch or decode code fast enough | Code size, i-cache misses | PGO, BOLT, less inlining in cold code, hot/cold splitting (section 7) |
| Backend bound, memory | Waiting for data | Cache and TLB misses | `perf-data-oriented-design`, `perf-memory` |
| Backend bound, core | Execution units or dependency chains | Divisions, long dependency chains | Break dependency chains, avoid division, SIMD |

For levels 2 and deeper on Intel CPUs, use `toplev` from
[pmu-tools](https://github.com/andikleen/pmu-tools).

Other instruments:

- `valgrind --tool=cachegrind` counts instructions (Ir) per source line, with
  no noise. Good for comparing two versions of a function.
- `llvm-mca` estimates the throughput of a short loop from its assembly:
  `g++ -O3 -march=native -S -o - f.cpp | llvm-mca -mcpu=<cpu>`. Read
  `Block RThroughput` (cycles per iteration) and the bottleneck resource.
- [Compiler Explorer](https://godbolt.org) shows the generated code for a
  small function.

## 2. Reduce the work, in this order

1. **Remove it** (`perf-remove-work`).
2. **Use a better algorithm or data structure.** A linear search in a hot
   loop, a `std::map` where a sorted vector or a flat hash table fits, a
   repeated sort. Complexity wins beat all micro-optimizations.
3. **Batch and amortize.** Handle N items per call: one dispatch, one lock,
   one bounds check, one cache warm-up for many items. Hoist checks and
   lookups that do not change out of the loop.
4. **Help the compiler** (section 7): release flags, `-march`, LTO, PGO.
5. **Fix branches** (section 4).
6. **Vectorize** (section 5).
7. **Parallelize** with threads (section 6).

## 3. Small fixes that often matter

- **Break dependency chains.** A sum in one variable waits for each add. Use
  2–4 accumulators, then add them at the end.
- **Avoid division and modulo** by a variable in hot loops. Use a power of
  two with a mask, or a multiply by a precomputed reciprocal.
- **Avoid virtual calls and `std::function` in per-event code.** Use
  templates or a `switch` on a type tag (`cpp-hot-path`).
- **Avoid hidden work:** exceptions on normal paths, `std::shared_ptr`
  copies (atomic counts), locale-aware formatting, `std::endl` (it flushes).

## 4. Branches

- Find mispredicted branches with `perf record -e branch-misses:u` and
  `perf annotate`.
- Make the common case predictable: sort or partition the data so that the
  same branch is taken many times in a row.
- Replace an unpredictable branch with arithmetic or a conditional move: a
  `?:` on two simple values, or a lookup table.
- Use `[[likely]]` / `[[unlikely]]` only where a profile shows that the
  layout matters. PGO does this better (section 7).

## 5. SIMD

1. **Auto-vectorization first.** Ask GCC what it did:

   ```bash
   g++ -O3 -march=native -fopt-info-vec-optimized -fopt-info-vec-missed -c f.cpp
   ```

   A loop vectorizes when the data is contiguous (struct of arrays,
   `perf-data-oriented-design`), the trip count is known at loop start, the
   body has no calls that are not inlined, and the pointers cannot alias (use
   `__restrict` or local copies).

   "loop vectorized" in the report is not enough proof. For a floating-point
   sum, GCC 16 reports "loop vectorized using 32 byte vectors" but still adds
   one value at a time (`vaddss`), because IEEE rules fix the order of the
   additions. Packed adds (`vaddps` on `ymm`) need permission to reorder:
   `-fassociative-math -fno-signed-zeros -fno-trapping-math` (alone,
   `-fassociative-math` is disabled with a warning), or `-ffast-math`. Both
   change the result in the last bits. Without those flags, write the sum
   with several accumulators or with `std::simd`. Always check the
   instructions (below).
2. **`std::simd`** (C++26). GCC 16 ships it as experimental support:
   `#include <simd>`, then `std::simd::vec<float>` (8 lanes with AVX2).
   Portable and type-safe. Check the generated code.
3. **Libraries:** [Highway](https://github.com/google/highway),
   [xsimd](https://github.com/xtensor-stack/xsimd), Eigen for linear
   algebra.
4. **Intrinsics** (`<immintrin.h>`) last: fastest to write wrong, hardest to
   maintain, and tied to one instruction set.

Check that vector instructions run where the time goes: `perf annotate`
shows `ymm` (AVX2) or `zmm` (AVX-512) registers in the hot loop. Build for
the CPUs that production uses: `-march=native` builds for this machine only.

## 6. Threads

- **Estimate the gain first.** With serial fraction s, Amdahl's law limits the
  speedup on N cores to 1 / (s + (1 − s) / N). Shared data that cores must
  keep coherent makes throughput fall again after some N (the Universal
  Scalability Law). Measure throughput at 1, 2, 4, … threads and plot it.
- **Share nothing on the hot path.** Partition the data by key (one engine
  per symbol, one shard per thread). Each thread owns its data; no locks.
- **Pipeline with queues.** Stages connected by single-producer,
  single-consumer queues. Pass items in batches to amortize the handoff.
- **Pin threads** to cores, and do not run more busy threads than cores.
  `thread_cpu.sh` (`perf-profiling`, section 5) shows the run-queue wait.
- **Find contention:** many voluntary context switches in `thread_cpu.sh`
  mean blocking. With root, use `perf lock` or off-CPU stacks. Atomic writes
  to shared cache lines show as HITM in `perf c2c` (`perf-false-sharing`).
- **Spinning versus blocking.** A spinning thread has the lowest wake-up
  latency but uses a whole core. Use spinning only on dedicated cores.

## 7. Compiler and linker

- **Release flags:** `-O2` or `-O3`; compare both. `-march=<production
  CPU>` enables newer instructions.
- **LTO** (`-flto`): inlining across source files. Small calls to other
  files (for example, accessors in a `.cpp`) become free.
- **PGO** (GCC):

  ```bash
  g++ -O2 -fprofile-generate -fprofile-update=atomic f.cpp -o prog   # atomic: for threads
  ./prog <representative workload>                                   # writes .gcda files
  g++ -O2 -fprofile-use -Werror=missing-profile f.cpp -o prog
  ```

  Use the same output name (`-o prog`) in both builds: GCC finds the profile
  by that name. A different name builds without the profile, with only a
  warning; `-Werror=missing-profile` makes that an error. Train with the real
  workload: a wrong profile makes the code slower.
- **BOLT** (`llvm-bolt`) reorders the code of the linked binary with a
  `perf` profile. Meta reports 2–15% less CPU time on large services, on top
  of PGO and LTO. With GCC, build with `-fno-reorder-blocks-and-partition`
  and link with `-Wl,--emit-relocs`. See the
  [BOLT documentation](https://github.com/llvm/llvm-project/tree/main/bolt).
- Measure each option alone. Keep it only if the benchmark shows a gain.

## 8. Prove it

- The benchmark shows the gain (`perf-benchmarks`), A/B as in
  `perf-profiling`, section 9.
- The counter that explains it moved: instructions, branch misses, IPC, or
  the top-down class.
- A guard keeps it, for example an instruction-count test or a check that the
  loop still vectorizes.
