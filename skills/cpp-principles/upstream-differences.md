# Differences from the modern_exchng_cpp documents


The upstream guide was written for a single-threaded matching engine. These
are the changes, and why:

- **Exceptions.** Upstream bans `throw`/`try`/`catch` outright and asks for
  `-fno-exceptions`. Here `std::expected` is the rule, but exceptions are
  allowed in three narrow places. The standard library throws, and
  triangulator has a second thread and filesystem code. We don't use
  `-fno-exceptions`. Added: the operating-error versus programmer-error split
  from TigerStyle, a guide to choosing the error type, and "never call
  `.value()`".
- **Bugs in the upstream examples, fixed here** (and upstream in
  [modern_exchng_cpp#3](https://github.com/breakbadsp/modern_exchng_cpp/pull/3)):
  - The Enumerations section and `ParseError` used `kRed` / `kEmptyInput`.
    That breaks upstream's own rule of PascalCase enumerators, no `k`, and
    an explicit first initializer.
  - The examples used 4-space indentation, parameters without `p_`, and
    struct members without the trailing `_`, all against upstream's own
    naming rules.
  - The `FileHandle::Create` example always returned `no_such_file_or_directory`,
    whatever the real `errno` was (a permission error, for example). The
    example here reports `errno`.
  - The `Sensor` example had a `const std::string id_` member, while the
    same document lists `const` data members as an anti-pattern. They
    break assignment and moves. This document keeps the anti-pattern rule.
  - `Boil(const Temperature&)` passed a one-`double` struct by reference,
    against upstream's own F.16 rule (cheap types by value).
  - The `[[nodiscard]]` example claimed that ignoring a result "won't
    compile". On its own it is a warning. Here it fails the build only
    because we use `-Werror`.
  - A line in the checklist was garbled ("ends with `_` plain snake_case").
- **Not carried over:** the C++26 contracts section (GCC-only, and the
  Makefile uses `-std=c++23`), the "no heap allocation once running" rule
  (narrowed to "no allocation per datagram"), the references to the order
  book, and these TigerStyle rules: 4-space indentation, `snake_case`
  functions, static allocation for everything, and in-place initialization
  through out pointers. Each of those conflicts with the naming above or
  with F.20.
- **Formatting:** upstream's `.clang-format` is LLVM-based with a 100-column
  limit. Triangulator keeps its Google-based 80-column file. Both use
  Allman braces, 2-space indentation and inserted braces, so the visible
  style is the same, and switching would only reformat every file.
- **Added from TigerStyle:** assertions (with a carve-out for external
  input), limits on everything, functions under about 70 lines, "push `if`s
  up and `for`s down", units at the end of names, index/count/size
  discipline, explicit options at call sites, and always saying why.
