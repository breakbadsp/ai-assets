---
name: perf-data-oriented-design
description: "Fix cache and TLB misses with data-oriented design: measure misses per source line and per data structure (perf stat, perf mem, cachegrind, pahole), then lay out data for the hot loops: struct of arrays, hot/cold splitting, smaller types, indices instead of pointers, contiguous containers, grouping by state, sorting by access, prefetching, huge pages. Read when a profile shows memory-bound stalls or high miss rates."
disable-model-invocation: true
---

# Data-oriented design for cache misses

A cache miss to DRAM costs about 80–100 ns: hundreds of instructions. The CPU
fetches whole 64-byte lines. If a loop uses 8 bytes of each line, it wastes 7/8
of the memory bandwidth and cache. Data-oriented design lays out data for the
way the hot code reads it, not for how the domain names it.

## 1. Measure

| Question | Command |
| --- | --- |
| How many loads miss? | `perf stat -e L1-dcache-loads:u,L1-dcache-load-misses:u,LLC-load-misses:u,dTLB-loads:u,dTLB-load-misses:u -- <cmd>` |
| Which source line misses? | `valgrind --tool=cachegrind --cache-sim=yes --cachegrind-out-file=cg.out <cmd>`, then `cg_annotate --show=Dr,D1mr,DLmr cg.out` |
| Which function's loads come from DRAM? | Record load samples (below), then `perf mem report -i mem.data --stdio --sort mem,sym` |
| How is a type laid out? | `pahole -C '<Type>' <binary>` (holes, padding, cache-line boundaries) |
| Do threads share lines? | `perf c2c` (`perf-false-sharing`) |

Record load samples on Intel without root:

```bash
perf record -W -d --sample-cpu -e cpu/mem-loads,ldlat=30/Pu -e cpu/mem-stores/Pu -o mem.data -- <cmd>
```

How to read the numbers:

- **L1 miss ratio** = `L1-dcache-load-misses` / `L1-dcache-loads`. A
  streaming loop over dense data is near 1/8 for 8-byte values (one miss per
  64-byte line). Much higher means each load touches a new line.
- **LLC misses** go to DRAM. These are the expensive ones.
- **dTLB misses** mean that the data spans many pages: random access over a
  large table. Huge pages can help (section 3).
- In `perf mem report`, sort by `mem,sym`: the rows with `RAM hit` or
  `L3 hit` name the functions that wait for memory.
- `cachegrind` simulates the caches, so its counts repeat exactly. It runs
  about 50 times slower; use a short run.

Calibrate: on `known_problems_demo.cpp` (`perf-profiling`, section 8), cachegrind must
put 99.9% of the D1 misses on the line marked "problem 1".

## 2. Know the access pattern first

For each hot loop, write down:

- Which fields it reads and writes.
- In which order it visits the items: sequential, strided, or random.
- How many items it visits each time, and how many exist.

Then compare **bytes used** with **bytes fetched** (lines touched × 64). The
layout changes in section 3 make these two numbers closer.

## 3. Layout techniques

| Technique | When | How |
| --- | --- | --- |
| Struct of arrays (SoA) | A loop reads a few fields of many items | One array per field (`std::vector<long> qty_`); the loop streams only what it reads. SoA loops also vectorize: GCC 16 vectorized an SoA sum of `long` values with 32-byte vectors and did not vectorize the array-of-structs version. (A floating-point sum needs more; see `perf-cpu`, section 5.) |
| Hot/cold splitting | Some fields are used on every event, others rarely | Keep the hot fields in a small struct; move the cold fields to a parallel array or a side table, indexed the same way. |
| Smaller types | Fields wider than their range | 32-bit indices and counts, `std::uint8_t` enums, bit fields or flags packed together. Order fields from large to small to remove padding; check with `pahole`. |
| Indices instead of pointers | Linked structures, references between objects | A 32-bit index into an array is half the size of a pointer, stays valid when the array is copied or saved, and keeps the data in one block. |
| Contiguous containers | Node-based containers on the hot path | `std::vector`, `std::flat_map` (in GCC 16), open-addressing hash tables, B-trees instead of `std::list`, `std::map`, `std::unordered_map`. |
| Group by state | A loop checks a flag on each item and skips most | Keep items of each state in their own array (for example, active and idle), so that the loop visits only the items that need work, with no branch. |
| Sort by access | Items visited in an order unrelated to memory order | Sort or partition the data in the order the loop visits it, or visit it in memory order. |
| Batch the processing | One item handled at a time through many layers | Handle arrays of items in each stage, so that each stage's code and data stay in cache. |
| Software prefetch | Random lookups that you know in advance (a batch of keys) | `__builtin_prefetch(&table[next_key])` some items ahead. The hardware already prefetches sequential and strided access, so this helps only for random access. Measure; it often does nothing. |
| Huge pages | High `dTLB-load-misses` on large tables | `madvise(MADV_HUGEPAGE)` on the region; see `perf-memory`, section 4. |
| Cache-line alignment | Data that two threads write | `alignas(64)` on the data each thread writes; see `perf-false-sharing`. Do not pad everything: padding makes data larger. |

Hash tables need a note. A good hash spreads keys at random, so each new key
touches a new cache line even when the keys are sequential. If a profile
shows the first probe as a DRAM miss and the table is large, the options are a
smaller table, a layout that keeps nearby keys in nearby lines, or a
different index. Each option has a cost in clustering or in protection
against bad keys; measure before you change it.

## 4. C++ notes

- The standard library has no struct-of-arrays container. Write a struct of
  vectors with one size, or a small class that keeps the arrays in step.
- `std::vector<std::unique_ptr<T>>` puts each object in its own allocation.
  Use `std::vector<T>` for data that a loop walks (`cpp-hot-path`).
- `std::unordered_map` allocates one node per entry. For hot lookups, use a
  flat open-addressing table with a fixed capacity.
- `std::hardware_destructive_interference_size` can differ between
  translation units in GCC (`-Winterference-size`). Many projects use the
  constant 64 on x86-64.

## 5. Prove it

- The miss counts fall: `perf stat` ratios and `cg_annotate` per line.
- The functions leave the `RAM hit` rows of `perf mem report`.
- The benchmark shows the time per item fall (`perf-benchmarks`), with the
  production data size: a small table fits in cache and hides the problem.

## Further reading

- Andrew Kelley, "Practical Data-Oriented Design" (talk): struct of arrays,
  indices instead of pointers, flags stored out of line.
- Mike Acton, "Data-Oriented Design and C++" (CppCon 2014).
- Richard Fabian, *Data-Oriented Design* (book, free online).
