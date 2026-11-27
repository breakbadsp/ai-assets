---
name: perf-profiling
description: "Profile a program on Linux in all ways and read the reports: the USE method for each resource, a catalog of CPU, memory, I/O, off-CPU, and cache tools, build and workload setup, permissions, the per-thread CPU split, perf stat and perf record, calibration on known problems, and the A/B proof. Read before you profile, read a profile, or claim a performance result."
disable-model-invocation: true
---

# Profile a program and read the reports

A profile answers one question about one workload. Write the question first.
Then profile in all the ways below that can answer it. One tool sees only one
kind of cost: a CPU profile cannot show time that a thread spends blocked.

## 1. The catalog: what to measure and with which tool

Use the [USE method](https://www.brendangregg.com/usemethod.html) first: for
each resource, check **utilization** (busy time), **saturation** (queued
work), and **errors**. The first resource that saturates is the bottleneck.

| Resource or question | Unprivileged tools | Root only | Details |
| --- | --- | --- | --- |
| Which thread or process is busy, and is it user or kernel time? | `thread_cpu.sh <pid>`, `top -H -p <pid>` | | Section 5 |
| CPU: where does the time go? | `perf record -g --user-callchains`, `perf report` | Kernel stacks: `perf record -a -g` | Section 6, `perf-cpu` |
| CPU: what kind of stall? | `perf stat`, `perf stat -M TopdownL1` | `toplev` (pmu-tools) for deeper levels | Section 6, `perf-cpu` |
| Waits: blocked, sleeping, or in a run queue | `thread_cpu.sh` (wait %, context switches) | `perf sched timehist`, `runqlat.bt`, off-CPU flame graphs | Section 7 |
| Locks and contention | Context switches in `thread_cpu.sh` | `perf lock`, `perf sched` | `perf-cpu` |
| Memory: allocations | `heaptrack`, `valgrind --tool=dhat`, an `operator new` counter | | `perf-memory` |
| Memory: footprint and page faults | `perf stat -e page-faults,minor-faults,major-faults`, `/proc/<pid>/status` (VmRSS, VmHWM), `valgrind --tool=massif` | | `perf-memory` |
| Cache and TLB misses | `perf stat -e L1-dcache-load-misses,LLC-load-misses,dTLB-load-misses`, `perf mem`, `valgrind --tool=cachegrind` | | `perf-data-oriented-design` |
| Cache lines shared between cores | `perf record` with PEBS load and store events, `perf c2c report` | `perf c2c record` | `perf-false-sharing` |
| System calls: which and how many | `strace -c -f <cmd>` (only a child process when `ptrace_scope` is 1) | `perf trace -s`, `syscount.bt` | `perf-io` |
| Disk I/O | `/proc/<pid>/io`, `vmstat 1` | `biolatency.bt`, `biosnoop.bt`, `iostat -x` (sysstat) | `perf-io` |
| Network | `ss -tmi`, `/proc/net/snmp`, `nstat` | `tcpretrans.bt`, `tcplife.bt` | `perf-io` |
| Compiler output | `-fopt-info-vec-missed`, `llvm-mca`, `perf annotate` | | `perf-cpu` |

The `.bt` tools come with `bpftrace` (on Arch, in `/usr/share/bpftrace/tools/`).
The bcc versions have names such as `offcputime-bpfcc`.

Start with the cheapest tools: `thread_cpu.sh` and `perf stat` cost almost
nothing, and they tell you which detailed tool to run next.

## 2. Prepare the build

- Use the release optimization level and flags. Do not profile a Debug or
  sanitizer build: its hot spots are different.
- Add debug information and frame pointers: `-g -fno-omit-frame-pointer`
  (for CMake, `RelWithDebInfo` and these flags).
- Do not strip the binary. `perf report` reads symbols from the same binary
  that ran. Do not rebuild between the record and the report.

## 3. Prepare the workload

- Use the workload from `perf-benchmarks`: the real mix, sizes, and number of
  clients. A toy load profiles the toy.
- Measure the steady state. Skip startup and warm-up, or attach with
  `-p <pid>` after warm-up.
- Run long enough: at least 10 seconds or 10,000 samples.
- Pin each thread under test to its own core (`taskset`, or the program's
  own setting). Put load generators on other cores.
- Keep the machine quiet. Stop builds and other heavy jobs. If you can, set
  a fixed CPU frequency (`cpupower frequency-set -g performance`). Write down
  what you could not control.
- Results can change with things that look unrelated, such as the size of the
  environment variables or the link order ([Mytkowicz et al.,
  2009](https://dl.acm.org/doi/10.1145/1508284.1508275)). Keep them the same
  for A and B. Treat a gain of 1–2% as uncertain until it repeats in another
  build.

## 4. Permissions

Read `/proc/sys/kernel/perf_event_paranoid` and
`/proc/sys/kernel/yama/ptrace_scope` first.

- At `perf_event_paranoid` 2 (a common default), you can profile only user
  space:
  - Add `:u` to events (`cycles:u`).
  - With `-g`, also add `--user-callchains`. Without it, `perf record -g`
    fails with "Failure to open event".
  - `perf c2c record`, `perf trace`, and `perf sched` fail.
    `perf-false-sharing` gives an unprivileged command for `perf c2c`.
- At `perf_event_paranoid` 1 or lower, or with `sudo`, kernel samples and
  system-wide (`-a`) recording work.
- At `ptrace_scope` 1, `strace -p` and `gdb -p` cannot attach to a process
  that is not their child. Start the process under the tool instead.
- `bpftrace` always needs root. It cannot even check a script's syntax without
  root.
- Do not change a sysctl or use `sudo` without the user's consent.

## 5. Find what saturates

Before you look at functions, find which thread or process limits the goal.

```bash
thread_cpu.sh <pid> 3     # in this skill's directory
```

For each thread, the script prints user %, system %, run-queue wait %, and
voluntary and involuntary context switches per second. It needs no root.

- **A thread near 100% (user + system)** is saturated, unless it spins on
  purpose. A spinning thread is always at 100%; measure its real work with a
  component benchmark (`perf-benchmarks`).
- **High system %** means the cost is in the kernel: system calls, page
  faults, network stack. Go to `perf-io` or `perf-memory`.
- **High wait %** means the thread is ready but has no CPU: too many threads
  for the cores, or another process on its core.
- **Many voluntary switches** mean that the thread blocks: on locks, I/O, or
  sleeps. Profile off-CPU time (section 7).
- **Check the load generators too.** If they saturate first, the test measures
  them, not the code.

## 6. CPU profiles

Profiler output is large. Write it to a file. Then read only the sections
that you need with `--percent-limit`, `head`, or `sed -n`. Do not paste
`perf script` output into the context.

### `perf stat`: counts and stall classes

```bash
perf stat -r 5 -e task-clock,cycles:u,instructions:u,cache-misses:u,branch-misses:u -- <cmd>
perf stat -M TopdownL1 -- <cmd>
perf stat --per-thread -e cycles:u,instructions:u -p <pid> -- sleep 5
```

- **IPC** (instructions divided by cycles): a modern x86 core can retire 4
  or more instructions for each cycle. An IPC below 1 shows stalls.
- **`+-` column** with `-r`: this is the spread over the runs. If it is more
  than a few percent, the workload is noisy. Fix the noise before you
  compare.
- **Last column below 100%**: the kernel multiplexed the counters, so the
  counts are estimates. Measure fewer events in one run.
- **Top-down level 1** divides the pipeline slots into retiring, frontend
  bound, backend bound, and bad speculation. `perf-cpu` tells what to do for
  each class. On Intel hybrid CPUs, measure on one core type
  (`taskset`), or the metric groups can mix the two core types.

### `perf record` and `perf report`: where the time goes

```bash
perf record -e cycles:u -g --user-callchains -F 999 -o cpu.data -- <cmd>
perf record -e cycles:u -g --user-callchains -F 999 -o cpu.data -p <pid> -- sleep 10
perf report -i cpu.data --stdio --no-children --percent-limit 2 > report.txt
perf report -i cpu.data --stdio --no-children --comm <thread name> --percentage relative
```

- **Overhead** with `--no-children` is the self time: samples in the
  function body. Start at the top entries.
- **Use `--comm` and `--percentage relative`** to see one thread's profile
  as a share of that thread. Percentages of the whole process mislead when
  some threads spin.
- **The call graph** under each entry shows the callers. It tells you which
  path to make cheaper.
- **`(inlined)` frames** come from the debug information. The cost belongs
  to the caller that contains the inlined code.
- **`[unknown]` frames** mean that frame pointers or symbols are missing.
  Rebuild with frame pointers, or record with `--call-graph dwarf`.
- **To find the slow instruction**, use `perf annotate -i cpu.data --stdio -s <symbol>`.
  Samples often land on the instruction after the slow one (skid). Examine
  the instructions just before a hot instruction.

## 7. Off-CPU time: where threads wait

A CPU profile shows only running time. To account for all the time of a
thread, also measure the time it is blocked or waiting
([off-CPU analysis](https://www.brendangregg.com/offcpuanalysis.html)).

- Without root: `thread_cpu.sh` gives the wait % and the context switches.
  `/proc/<pid>/task/<tid>/wchan` names the kernel function where a blocked
  thread sleeps.
- With root:

  ```bash
  sudo perf sched record -- sleep 5 && sudo perf sched timehist -s   # run and wait time per thread
  sudo bpftrace /usr/share/bpftrace/tools/runqlat.bt                  # run-queue latency
  sudo offcputime-bpfcc -df -p <pid> 10 > offcpu.folded               # off-CPU stacks (bcc)
  ```

  Make a flame graph from the folded stacks with `flamegraph.pl` from
  [FlameGraph](https://github.com/brendangregg/FlameGraph).

## 8. Calibrate the tools

A tool that finds nothing proves nothing, until it has found a known problem
on this machine. `known_problems_demo.cpp` in this skill's directory plants
three problems. Build it and check each tool:

```bash
g++ -std=c++26 -O2 -g -fno-omit-frame-pointer known_problems_demo.cpp -o demo
strace -c -f ./demo > /dev/null                 # expect about 200,000 write calls
heaptrack -o demo-heap ./demo > /dev/null        # then: heaptrack_print -f demo-heap.zst
valgrind --tool=cachegrind --cache-sim=yes --cachegrind-out-file=cg.out ./demo > /dev/null
cg_annotate --show=D1mr cg.out                   # expect 99.9% of D1 misses on "problem 1"
```

`heaptrack_print` must report 200,000 temporary allocations from `MakeLine`.
For `perf c2c`, use the demo in `perf-false-sharing`.

## 9. Prove a change

- Change one thing at a time.
- Use the same machine, build flags, workload, and pinning for A and B.
- Interleave the runs (A, B, A, B), at least 5 of each. Report the median
  and the spread.
- Show two numbers: a user-visible metric (throughput, latency, or time), and
  the counter that explains it (for example, HITM samples or IPC). A result
  without its mechanism can be noise. A mechanism without a user-visible
  change is not worth its cost.

## 10. Write the report

Write the bottleneck report from `perf-optimization`, step 3. Include the
setup (commit, build flags, CPU model, workload, pinning,
`perf_event_paranoid`) and the commands, so that someone else can repeat the
measurement. Keep raw profiles out of the repository unless the project keeps
them in a profiling directory.
