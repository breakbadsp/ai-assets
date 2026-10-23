---
name: cpp-concurrency
description: "C++ concurrency: data races, RAII locks, named lock guards, publishing immutable snapshots, jthread, no detach, false sharing. Read when you add or change threads, locks, atomics, or shared data."
disable-model-invocation: true
---

# Concurrency


The collector's main loop runs on one thread. The HTTP server runs on its
own thread and reads a published snapshot (`collector/http.hpp`). Keep it
that way. Per `AGENTS.md`, a slow helper must never delay the main loop.

| Rule | Summary |
|------|---------|
| **CP.2 / CP.3** | No data races; share as little writable data as possible |
| **CP.8** | Never use `volatile` for synchronization |
| **CP.20** | RAII locks only (`std::scoped_lock`, `std::unique_lock`) |
| **CP.22** | Never call unknown code while holding a lock |
| **CP.44** | Always name a lock guard. An unnamed one is destroyed at once, and the lock is never held |

- Publish immutable data across threads (for example a
  `std::shared_ptr<const T>` swapped under a short lock) instead of sharing
  mutable state.
- Prefer `std::jthread` to `std::thread`: its destructor joins, so a thread
  can't be left running by mistake. Never `detach`.
- Avoid false sharing. If two threads each write their own variable often,
  keep those variables on separate cache lines (`alignas(64)`).

```cpp
class Snapshot final
{
public:
  void Publish(std::shared_ptr<const std::string> p_body)
  {
    const std::scoped_lock lock{mutex_};
    body_ = std::move(p_body);
  }

  [[nodiscard]] std::shared_ptr<const std::string> Live()
  {
    const std::scoped_lock lock{mutex_};
    return body_;
  }

private:
  std::mutex mutex_;
  std::shared_ptr<const std::string> body_;
};
```
