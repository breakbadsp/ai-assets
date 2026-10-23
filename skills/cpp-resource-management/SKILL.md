---
name: cpp-resource-management
description: "C++ resource ownership: RAII, unique_ptr and shared_ptr, no naked new/delete or malloc/free, raw pointers do not own, wrapping C handles. Read when you acquire a file descriptor, socket, database handle, memory, or other resource."
disable-model-invocation: true
---

# Resource management


| Rule | Summary |
|------|---------|
| **R.1** | RAII for every resource |
| **R.3** | A raw `T*` doesn't own, and is used only when null is valid |
| **R.5** | Prefer scoped objects; don't use the heap without a reason |
| **R.10 / R.11** | No `malloc`/`free`, no naked `new`/`delete` |
| **R.20 / R.21** | `std::unique_ptr` for ownership; `std::shared_ptr` only when ownership really is shared |

RAII doesn't depend on exceptions. A destructor runs on every way out of a
scope, including an early `return` of an error. `std::expected` changes how
a failure is reported, not how resources are cleaned up. Destructors,
deallocation and swap must never fail.

C APIs (`open`, `socket`, `sqlite3_open_v2`): wrap the handle in its owner
right after you acquire it, before the next line that can return early.
