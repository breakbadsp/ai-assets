---
name: cpp-source-files
description: "C++ source files: #pragma once, self-contained headers, no using namespace in headers, inline functions in headers, the project namespace. Read when you add or change a header or source file, or its includes."
disable-model-invocation: true
---

# Source files


| Rule | Summary |
|------|---------|
| **SF.7** | No `using namespace` at global scope in a header |
| **SF.8** | `#pragma once` on every header |
| **SF.11** | Headers are self-contained: each includes what it uses |

Most of this code is header-only, with one `main.cpp` per binary. Free
functions defined in a header are `inline`. Put everything in
`namespace triangulator`.
