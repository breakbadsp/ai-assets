---
name: perf-false-sharing
description: "Find and fix false sharing between CPU cores with perf c2c: calibrate on a known case, record HITM samples, read the Shared Data Cache Line Table and the Pareto table, map offsets to fields with pahole, change the layout, and prove the fix. Read when threads write shared data, when a multithreaded hot path scales badly, or before you add cache-line padding."
disable-model-invocation: true
---

# Find false sharing

CPU caches keep data coherent one cache line at a time. A line is 64 bytes
on x86-64 and most Arm cores. When one core writes a line, the other cores
lose their copies. When a core then reads that line, the load gets the line
from the core that modified it. That event is a **HITM** (hit modified).

- **False sharing:** threads write *different* variables that are on the
  same line. The line moves between the cores at each write, but the threads
  share no data. A different layout removes the cost.
- **True sharing:** threads use the *same* variable, for example the head
  index of a queue. A different layout does not help. Change the protocol:
  batch the writes, keep a local copy of the remote value, or give each
  thread its own copy and combine them later.

Do the steps in `perf-profiling` first: build, workload, pinning, and
permissions. The threads under test must run on different cores at the same
time. If they do not, no HITM occurs.

## 1. Calibrate the tool

A clean report proves nothing until the tool has found a known case on this
machine. Build and record the demo in this skill's directory:

```bash
g++ -O2 -g -pthread false_sharing_demo.cpp -o fs_shared
g++ -O2 -g -pthread -DPAD=1 false_sharing_demo.cpp -o fs_padded
```

Record each binary as in step 3. Expect these results:

- `fs_shared`: one hot line. One thread writes offset `0x30` and the other
  writes `0x38` (the offsets change with the address of the global).
- `fs_padded`: zero `Load Local HITM`.
- `fs_shared` is several times slower than `fs_padded`. On an Intel
  i5-9500, the times were 6.4 s and 0.85 s.

## 2. Count HITM events (optional and quick)

```bash
perf list 2>/dev/null | grep -i hitm
perf stat -e mem_load_l3_hit_retired.xsnp_hitm:u -- <cmd>
```

The event name changes with the CPU model. On the i5-9500 (Skylake family),
the demo gave 158,141,825 for `fs_shared` and 1 for `fs_padded`. A count
that is near zero for the real workload shows that no cache-line contention
occurs. If the count is high, step 3 tells you which line causes it.

## 3. Record

With `sudo`, or with `perf_event_paranoid` at 1 or lower, use `perf c2c`.
It selects the events for the CPU: PEBS on Intel, IBS on AMD, SPE on Arm.

```bash
perf c2c record -F 20000 --call-graph dwarf -o c2c.data -p <pid> -- sleep 10
```

At `perf_event_paranoid` 2 on Intel, `perf c2c record` fails. Record the
same events in user space with `perf record`:

```bash
perf record -W -d --sample-cpu \
  -e cpu/mem-loads,ldlat=30/Pu -e cpu/mem-stores/Pu \
  -o c2c.data -p <pid> -- sleep 10
```

`perf c2c report` reads both files. On AMD, IBS usually needs root.

## 4. Read the report

```bash
perf c2c report -i c2c.data -NN -c tid,iaddr --stdio > c2c.txt
```

Read these three sections, in this order.

1. **Trace Event Information.** Find `Load Local HITM` (and
   `Load Remote HITM` on a machine with more than one socket). If both are
   near zero and step 1 passed, this workload has no false sharing. Stop.
2. **Shared Data Cache Line Table.** There is one row for each cache line,
   sorted by HITM. `Tot Hitm` is the share of all HITM samples that this
   line has. Examine the lines with the largest share first. Lines with a
   small share are not worth a layout change.
3. **Shared Cache Line Distribution Pareto.** For each hot line, there is
   one row for each offset, thread, and code address. `Offset` is the byte
   in the line. `Tid` is the thread. `Symbol` and `Source:Line` give the
   code (they need `-g`). Classify the line:
   - Different threads write different offsets: **false sharing**.
   - All threads use the same offset: **true sharing**.
   - One thread writes one offset and other threads read other offsets:
     **false sharing**. The reads get HITM.

   The `lcl hitm` cycles column shows the mean load latency for each HITM.
   It tells you how much each transfer costs.

## 5. Map offsets to fields

```bash
pahole -C 'Type' <binary>
pahole -C 'ns::Queue<ns::Item>' <binary>
```

`pahole` prints the offset of each field and the
`--- cacheline N boundary ---` lines. You can ignore its warnings about
template parameters.

The report offset is relative to the line, not to the object. If an object
does not start on a line boundary, the two offsets are different. Use
`Source:Line` to find the field. If you have the object address, use this
equation: field offset = line address + report offset - object address.

Two objects can share a line at their boundary. This occurs when one thread
allocates objects one after the other, and different threads use them later.
`pahole` cannot show this. The report shows it as one line with symbols from
two different objects.

## 6. Change the layout

Group the fields by the thread that writes them:

- Put the fields that each thread writes on a cache line of that thread.
- Put read-mostly fields together, away from written fields.
- For per-thread counters, give each counter its own line, or keep the
  counts thread-local and add them at the end.
- Pad only the lines that the report shows. Padding makes the data larger
  and uses more cache.
- Lock the layout with a compile-time check (for example, a `static_assert`
  on the alignment or the field offset), so that a later edit cannot undo
  the fix.

For C++, `cpp-concurrency` has the layout rules.

## 7. Prove the fix

Record the same workload again, with the same commands.

- The line is no longer in the Shared Data Cache Line Table, or its HITM
  count is much smaller.
- The HITM counter from step 2 is lower.
- The user-visible metric is better, measured as in `perf-profiling`,
  section 9.
