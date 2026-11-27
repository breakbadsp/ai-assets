---
name: perf-memory
description: "Find and remove memory costs: count and locate allocations (heaptrack, DHAT, massif, an operator new counter), then remove them in order: avoid the copy, allocate once at startup, reuse, use stack or inline storage, use an arena or monotonic buffer, change the allocator. Also page faults, huge pages, and NUMA. Read when a profile shows malloc, free, operator new, page faults, or a large or growing footprint."
disable-model-invocation: true
---

# Memory: allocations, footprint, page faults

A heap allocation costs tens to hundreds of nanoseconds, can take a lock, and
scatters data over memory, which causes cache misses later. A page fault costs
microseconds. On a hot path, the goal is zero allocations and zero page faults
in the steady state. The C++ rules for this are in `cpp-hot-path` and
`cpp-resource-management`; this skill tells how to find the costs and which
pattern removes each one.

## 1. Measure

| Question | Tool | Command |
| --- | --- | --- |
| Where are the allocations, how many, and which are temporary? | heaptrack | `heaptrack -o heap ./prog`, then `heaptrack_print -f heap.zst` |
| Which blocks are short-lived, never read, or too large? | DHAT | `valgrind --tool=dhat ./prog`, then open `dh_view.html` (in `/usr/lib/valgrind/` on Arch) and load `dhat.out.<pid>` |
| How does the heap grow over time? | massif | `valgrind --tool=massif ./prog`, then `ms_print massif.out.<pid>` |
| Does the steady state allocate at all? | An `operator new` counter in a test | See section 3 |
| How much CPU does the allocator use? | perf | `perf report --comm <thread> --percentage relative`; look for `malloc`, `free`, `_int_malloc` |
| Footprint and faults | `/proc`, perf | `grep -E 'VmRSS|VmHWM' /proc/<pid>/status`; `perf stat -e page-faults,minor-faults,major-faults` |

How to read the heaptrack report:

- **MOST CALLS TO ALLOCATION FUNCTIONS**: the call sites that allocate most
  often. This is the list for the hot path.
- **MOST TEMPORARY ALLOCATIONS**: allocations freed right after they were
  made. These are almost always unnecessary: a buffer or a string that could
  be reused or put on the stack.
- **PEAK MEMORY CONSUMERS**: what sets the footprint.

heaptrack slows the program a few times; DHAT and massif run it under
Valgrind, which is much slower. Use them on a short run of the workload.

Calibrate first: `known_problems_demo.cpp` (`perf-profiling`, section 8) must show
200,000 temporary allocations.

## 2. Remove allocations, in this order

1. **Do not allocate.** Remove the copy: pass `std::span` or
   `std::string_view`, move instead of copy, build the object in place. Ask
   `perf-remove-work` whether the object is needed at all.
2. **Allocate once, at startup.** Size containers from the configuration
   limits: `reserve`, fixed-capacity arrays, pools sized to the maximum. A
   full container is an error that the code returns, not a reason to grow.
3. **Reuse.** Keep the buffer and `clear()` it; `clear()` keeps the capacity.
   Keep free lists of fixed-size objects (an object pool), so that a freed
   object serves the next request.
4. **Use stack or inline storage** for small, bounded sizes: `std::array`,
   `std::inplace_vector<T, N>` (C++26; in GCC 16), or a type with small
   buffer optimization. Keep large arrays off the stack: the default thread
   stack is 8 MiB or less.
5. **Use an arena (monotonic buffer)** when many objects live and die
   together, for example for one request, one message, or one frame. Each
   allocation only moves a pointer; everything is freed at once.
6. **Change the allocator** only after steps 1–5, and only with a measurement.
   Test jemalloc, mimalloc, or tcmalloc with `LD_PRELOAD=<library> ./prog`
   before you link one.

### Arena with `std::pmr`

```cpp
alignas(std::max_align_t) std::array<std::byte, 64 * 1024> buffer; // sized from limits
std::pmr::monotonic_buffer_resource arena{buffer.data(), buffer.size(),
                                          std::pmr::null_memory_resource()};
for (const Request &request : requests)
{
  {
    std::pmr::vector<Item> items{&arena}; // allocations move a pointer in buffer
    Handle(request, items);
  } // destroy every container that uses the arena first
  arena.release(); // then free everything at once; the next request reuses buffer
}
```

Rules and traps (verified with GCC 16):

- With `null_memory_resource()` as the upstream, an arena that is too small
  throws `std::bad_alloc` instead of quietly using the heap. Size the buffer
  from the limits, and test the largest request. In a project without
  exceptions, check the size before you allocate.
- A monotonic buffer never frees one object. Memory grows until `release()`.
  Do not use one for long-lived data that changes.
- Destroy all containers that use the arena before `release()`. A container
  that lives longer points into memory that the next request overwrites.
- `std::pmr::unsynchronized_pool_resource` is for one thread only;
  `synchronized_pool_resource` takes a lock.
- `std::pmr` containers are different types from the `std` ones, and each
  allocation is a virtual call. On the hottest paths, a plain fixed-capacity
  array can be faster. Measure.

## 3. Guard it with a test

Replace the global `operator new` in a test binary, count the calls during the
steady state, and expect 0:

```cpp
std::atomic<bool> g_counting{false};
std::atomic<std::uint64_t> g_news{0};
// noinline: when GCC inlines these at -O2, -Wmismatched-new-delete fires.
[[gnu::noinline]] void *operator new(std::size_t p_size)
{
  if (g_counting.load(std::memory_order_relaxed))
  {
    g_news.fetch_add(1, std::memory_order_relaxed);
  }
  void *const block = std::malloc(p_size == 0 ? 1 : p_size);
  if (block == nullptr)
  {
    std::abort(); // the test cannot continue without memory
  }
  return block;
}
[[gnu::noinline]] void operator delete(void *p_block) noexcept { std::free(p_block); }
[[gnu::noinline]] void operator delete(void *p_block, std::size_t) noexcept { std::free(p_block); }
```

This builds without warnings at `-O0`, `-O2`, and `-O3` with `-Werror` (GCC
16). Also replace the array, `nothrow`, and aligned forms if the code uses
them. Warm up first,
then set `g_counting`, run the workload, and check the count. Enable every
optional feature in the test (for example, a market data feed), because each
can add its own allocation. Check that the test fails when you add an
allocation on purpose.

## 4. Page faults, huge pages, NUMA

- **Pre-fault at startup.** Touch every page of the large buffers once at
  startup (write one byte per 4 KiB page), or map them with `MAP_POPULATE`.
  For hard latency limits, also `mlock` or `mlockall(MCL_CURRENT | MCL_FUTURE)`
  so that the kernel cannot page them out.
- **Huge pages** reduce TLB misses for large tables (see
  `perf-data-oriented-design` for `dTLB-load-misses`). Check
  `/sys/kernel/mm/transparent_hugepage/enabled`. With the setting `madvise`,
  call `madvise(MADV_HUGEPAGE)` on the large regions. Traps: a huge page can
  waste memory for sparse data, and compaction can stall an allocation
  ([kernel documentation](https://docs.kernel.org/admin-guide/mm/transhuge.html)).
  Pre-fault huge-page regions at startup too.
- **NUMA** (machines with more than one socket): memory is placed on the node
  of the thread that first writes it. Allocate and first touch the data on
  the thread that uses it, or bind with `numactl --cpunodebind=N --membind=N`.
  Check with `numastat -p <pid>`.

## 5. Prove it

- heaptrack again: the hot call sites are gone from the lists.
- The allocation test passes, and fails without the change.
- The benchmark (`perf-benchmarks`) shows the gain in time per operation.
