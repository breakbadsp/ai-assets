---
name: perf-profiling
description: "Profile a program on Linux and read the report: state one question, build with symbols, run a pinned and representative workload, choose the tool (perf stat, perf record, perf c2c, perf trace), read its output, and prove a change with an A/B run. Read before you profile, read a profile, or claim a performance result."
disable-model-invocation: true
---

# Profile a program and read the report

A profile answers one question about one workload. Write the question
first. A profile without a question gives a long report and no decision.

## 1. Choose the tool from the question

| Question | Tool | Section or skill |
| --- | --- | --- |
| Is version B faster than version A? | The program's own metric (throughput, latency percentiles, wall time), repeated | 6 |
| What kind of stall limits the CPU? | `perf stat`, top-down metrics | 4 |
| Which functions use the CPU time? | `perf record` and `perf report` | 5 |
| Do threads fight over cache lines? | `perf c2c` | `perf-false-sharing` |
| Where does a thread wait (system calls, locks, sleep)? | `perf trace -s`, `perf sched`, off-CPU profiles | Tool manual |

Start with the cheapest tool that answers the question. `perf stat` costs
almost nothing and tells you where to look with `perf record`.

## 2. Prepare the build

- Use the release optimization level and flags. Do not profile a Debug or
  sanitizer build: its hot spots are different.
- Add debug information and frame pointers: `-g -fno-omit-frame-pointer`
  (for CMake, `RelWithDebInfo` and these flags).
- Do not strip the binary. `perf report` reads symbols from the same binary
  that ran. Do not rebuild between the record and the report.

## 3. Prepare the workload

- Use a representative load: the real request mix, sizes, and number of
  clients. A toy load profiles the toy.
- Measure the steady state. Skip startup and warm-up, or attach with
  `-p <pid>` after warm-up.
- Run long enough: at least 10 seconds or 10,000 samples.
- Pin each thread under test to its own core (`taskset`, or the program's
  own setting). Put load generators on other cores.
- Keep the machine quiet. Stop builds and other heavy jobs. If you can, set
  a fixed CPU frequency (`cpupower frequency-set -g performance`). Write down
  what you could not control.

## 4. Permissions

Read `/proc/sys/kernel/perf_event_paranoid` first.

- At `2` (a common default), you can profile only user space:
  - Add `:u` to events (`cycles:u`).
  - With `-g`, also add `--user-callchains`. Without it, `perf record -g`
    fails with "Failure to open event".
  - `perf c2c record` fails. `perf-false-sharing` gives the unprivileged
    command.
- At `1` or lower, or with `sudo`, kernel samples and system-wide (`-a`)
  recording work.
- Do not change the sysctl or use `sudo` without the user's consent.

## 5. Record and read

Profiler output is large. Write it to a file. Then read only the sections
that you need with `--percent-limit`, `head`, or `sed -n`. Do not paste
`perf script` output into the context.

### `perf stat`: counts and stall classes

```bash
perf stat -r 5 -e task-clock,cycles:u,instructions:u,cache-misses:u,branch-misses:u -- <cmd>
perf stat -M TopdownL1 -- <cmd>
```

- **IPC** (instructions divided by cycles): a modern x86 core can retire 4
  or more instructions for each cycle. An IPC below 1 shows stalls.
- **`+-` column** with `-r`: this is the spread over the runs. If it is more
  than a few percent, the workload is noisy. Fix the noise before you
  compare.
- **Last column below 100%**: the kernel multiplexed the counters, so the
  counts are estimates. Measure fewer events in one run.
- **Top-down level 1** divides the pipeline slots into retiring, frontend
  bound, backend bound, and bad speculation. If backend bound is high, the
  cause is memory or execution units. Then use `TopdownL2`, or `perf c2c` if
  more than one thread writes shared data.

### `perf record` and `perf report`: where the time goes

```bash
perf record -e cycles:u -g --user-callchains -F 999 -o cpu.data -- <cmd>
perf record -e cycles:u -g --user-callchains -F 999 -o cpu.data -p <pid> -- sleep 10
perf report -i cpu.data --stdio --no-children --percent-limit 2 > report.txt
```

- **Overhead** with `--no-children` is the self time: samples in the
  function body. Start at the top entries.
- **The call graph** under each entry shows the callers. It tells you which
  path to make cheaper.
- **`(inlined)` frames** come from the debug information. The cost belongs
  to the caller that contains the inlined code.
- **`[unknown]` frames** mean that frame pointers or symbols are missing.
  Rebuild with frame pointers, or record with `--call-graph dwarf`.
- **To find the slow instruction**, use `perf annotate -i cpu.data --stdio -s <symbol>`.
  Samples often land on the instruction after the slow one (skid). Examine
  the instructions just before a hot instruction.

## 6. Prove a change

- Change one thing at a time.
- Use the same machine, build flags, workload, and pinning for A and B.
- Interleave the runs (A, B, A, B), at least 5 of each. Report the median
  and the spread.
- Show two numbers: a user-visible metric (throughput, latency, or time), and
  the counter that explains it (for example, HITM samples or IPC). A result
  without its mechanism can be noise. A mechanism without a user-visible
  change is not worth its cost.

## 7. Write the report

Write: the question, the setup (commit, build flags, CPU model, workload,
pinning, `perf_event_paranoid`), the commands, the numbers before and after,
and the explanation. Keep raw profiles out of the repository unless the
project keeps them in a profiling directory.
