---
name: perf-io
description: "Measure and reduce I/O costs: count system calls, find blocked time, then avoid the I/O, batch it, reduce it, make it asynchronous, avoid copies, or move it to user space. Covers network (batching, Nagle, io_uring, zero-copy, busy polling, kernel bypass) and disk (page cache, fsync batching, direct I/O, preallocation). Read when a profile shows high system time, many system calls, or threads blocked on I/O."
disable-model-invocation: true
---

# I/O: avoid, batch, reduce, move to user space

Each system call costs from about 100 ns to several µs, and it can block. Each
device operation (a packet, a disk write, an `fsync`) costs much more. The
number of calls and device operations usually matters more than the bytes.

## 1. Measure

| Question | Unprivileged | Root |
| --- | --- | --- |
| Is the cost in the kernel? | `thread_cpu.sh <pid>` (system %) in `perf-profiling` | `perf record -a -g` with kernel stacks |
| Which system calls, how many, how long? | `strace -c -f <cmd>`; `strace -f -T -e trace=<calls> -o trace.txt <cmd>` | `perf trace -s -p <pid>`; `syscount.bt` |
| Bytes and calls per process | `/proc/<pid>/io` (`rchar`, `wchar`, `syscr`, `syscw`, `read_bytes`, `write_bytes`) | `pidstat -d 1` (sysstat) |
| Disk latency and queue | `vmstat 1` (`wa`, `bi`, `bo`) | `biolatency.bt`, `biosnoop.bt`, `iostat -x 1` |
| Socket queues, retransmits, window | `ss -tmi`, `nstat` | `tcpretrans.bt`, `tcplife.bt` |
| Where a thread blocks | `thread_cpu.sh` (voluntary switches), `/proc/<pid>/task/<tid>/wchan` | `perf sched timehist`, off-CPU stacks (`perf-profiling`, section 7) |

Notes:

- `strace` slows every system call a lot. Use it to count and to see the
  pattern, not to time the program. At `ptrace_scope` 1 it can trace only a
  process that it starts.
- The key ratio is **system calls per item**. If `strace -c` shows one
  `write` for each message, the batch is missing.
- `strace -c` on `known_problems_demo.cpp` (`perf-profiling`) must show
  about 200,000 `write` calls. Use it to check the tool.

## 2. Reduce I/O, in this order

1. **Avoid it.** Ask `perf-remove-work`: is the read or write needed? Cache
   the data in memory, keep the connection open, keep the file open, do not
   log on the hot path.
2. **Batch it.** One call for many items:
   - Collect output in a buffer and send it once per loop pass, not once per
     message.
   - `writev` / `readv` for several buffers; `sendmmsg` / `recvmmsg` for
     several UDP datagrams.
   - io_uring: put many operations in the submission queue, then submit once.
   - Disk: group commit. Write many records, then `fsync` once
     (`fdatasync` if the metadata does not change).
3. **Reduce it.** Send fewer, smaller messages: binary instead of text, only
   the changed fields, conflated updates.
4. **Make it asynchronous.** Do not block the hot thread on I/O. Use
   non-blocking sockets with `epoll` or io_uring, or give the I/O to another
   thread through a queue.
5. **Avoid copies.** `sendfile` or `splice` between descriptors; `mmap` for
   large read-mostly files; `MSG_ZEROCOPY` for large sends (see section 3).
6. **Move it to user space.** Busy polling, then kernel bypass (section 3).
   Each step costs dedicated cores and complexity. Go there only when the
   measurement shows that the kernel path is the bottleneck.

## 3. Network

- **Latency and Nagle.** For request-reply traffic with small messages, set
  `TCP_NODELAY` and do your own batching (step 2). To send one batch made of
  several writes as one segment, use `MSG_MORE` on all but the last send, or
  set and clear `TCP_CORK`.
- **Many small segments.** Many small sends cost one system call and often one
  packet each. Measure the system calls per message, and batch.
- **io_uring** (from the
  [liburing networking notes](https://github.com/axboe/liburing/wiki/io_uring-and-networking-in-2023)
  and [a 2025 study](https://arxiv.org/abs/2512.04859)):
  - One `io_uring_submit` for many prepared operations replaces many calls.
  - `IORING_SETUP_SINGLE_ISSUER` with `IORING_SETUP_DEFER_TASKRUN` (Linux
    6.1+) runs completion work when the thread asks for it, with less locking
    and fewer interruptions.
  - Multishot receive (6.0+) with provided buffer rings (5.19+): one
    submission receives many times; the kernel picks a buffer for each.
  - Registered buffers and files remove the cost of mapping and looking them
    up on each operation. They help most for many small operations that reuse
    the same buffers.
  - `IORING_SETUP_SQPOLL` uses a kernel thread that polls the queue, so the
    application makes no submit calls. It uses a core all the time.
  - Measure each option. The study found that the best choice changes with
    message size and kernel settings.
- **Zero-copy sends.** `MSG_ZEROCOPY` is usually worth it only for writes
  larger than about 10 KB, and loopback traffic still gets copied
  ([kernel documentation](https://docs.kernel.org/networking/msg_zerocopy.html)).
  A loopback benchmark cannot show its gain.
- **Busy polling.** `SO_BUSY_POLL`, the `net.core.busy_poll` sysctls, or
  io_uring NAPI busy polling trade CPU for lower latency: the thread polls the
  device queue instead of waiting for an interrupt
  ([kernel NAPI documentation](https://docs.kernel.org/networking/napi.html)).
- **Kernel bypass.** AF_XDP keeps the device shared with the normal kernel
  stack and needs driver support. DPDK takes the whole device and needs its
  own stack. Use them only when the kernel network stack is the measured
  bottleneck and dedicated cores are acceptable.
- **Loopback tests** hide network costs and add others: the client and the
  server share the CPU and the kernel. Write down that a result came from
  loopback.

## 4. Disk

- **Use the page cache** for data that is read again. Measure cold reads
  separately (after `echo 3 > /proc/sys/vm/drop_caches`, root) from warm
  reads.
- **Batch durability.** `fsync` costs a device flush: often from 50 µs to
  many ms. Group many records into one `fsync`. Keep the batch window inside
  the latency goal.
- **Sequential beats random.** Append to a log, and compact later.
- **Preallocate** files with `fallocate`, so that appends do not change the
  file size and metadata each time.
- **Direct I/O** (`O_DIRECT`, aligned buffers) skips the page cache. Use it
  only when the program does its own caching. It needs aligned sizes and
  offsets.
- **io_uring** also batches disk operations and can register files and
  buffers, as for the network.

## 5. Prove it

- `strace -c` again: fewer calls per item.
- `thread_cpu.sh`: lower system % for the same throughput.
- The benchmark (`perf-benchmarks`): latency percentiles and throughput,
  A/B as in `perf-profiling`, section 9.
- Add a guard: a test that counts the system calls or the sends per item
  (`perf-benchmarks`, section 5).
