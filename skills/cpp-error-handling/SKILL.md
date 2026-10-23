---
name: cpp-error-handling
description: "C++ error handling: operating versus programmer errors, std::expected and std::optional, choosing the error type, fallible constructors (static Create), when exceptions are allowed, noexcept. Read when a function can fail, or when you write throw, try, catch, or noexcept."
disable-model-invocation: true
---

# Error handling


## Two kinds of failure

TigerStyle separates two things, and this document follows it:

- **Operating errors** are expected: a malformed datagram, a missing file,
  a busy SQLite database, a port already in use, a thread that exited
  between two `/proc` reads. Handle them. Return them as values.
- **Programmer errors** are bugs: an index past the end, a broken
  invariant, a state that "can't happen". Don't return these. Check them
  with an assertion (see the `cpp-assertions` skill), which crashes the program. A crash
  turns a silent correctness bug into a visible one.

## Return values, not exceptions

- A function that can fail returns `std::expected<T, E>`. If it has no
  value to return, use `std::expected<void, E>`.
- A value that may legitimately be missing, where missing is not an error,
  is a `std::optional<T>`. Don't use sentinels (`-1`, `""`, `nullptr`).
- Every function that returns `std::expected` or `std::optional` is
  `[[nodiscard]]`. Our build uses `-Werror`, so ignoring the result is a
  compile error.
- Choose the error type `E` by how hot the path is:
  - Per-datagram or per-sample paths: an `enum class` or a
    `std::string_view` that points at a string literal. Building an error
    never allocates. (`collector/protocol.hpp` `Decode` does this.)
  - System calls: `std::error_code{errno, std::generic_category()}`.
    Capture `errno` right away, before another call can overwrite it.
  - Startup and configuration: `std::string`, so the message can name the
    file, key or value (as `collector/config.hpp` does).
- Use an early `return` for each error, so the main path stays flat. Use
  `and_then` / `transform` / `or_else` only when the chain is clearer than
  the `if` statements it replaces.
- Don't call `.value()` on a `std::expected` or `std::optional`. It throws
  when the object is empty. Check first and then use `*result` or
  `result->`, or use `value_or`.

```cpp
enum class DecodeError
{
  ShortHeader = 0,
  BadVersion,
  BadLength,
};

[[nodiscard]] std::expected<Header, DecodeError> DecodeHeader(
    std::span<const std::byte> p_bytes)
{
  if (p_bytes.size() < kHeaderBytes)
  {
    return std::unexpected(DecodeError::ShortHeader);
  }
  const auto version = ReadLittleEndian<std::uint16_t>(p_bytes, 0);
  if (version != kProtocolVersion)
  {
    return std::unexpected(DecodeError::BadVersion);
  }
  // ...
  return header;
}
```

```cpp
// A system call. Capture errno before anything else can change it.
[[nodiscard]] std::expected<std::uint64_t, std::error_code> MonotonicNs()
{
  timespec now{};
  if (::clock_gettime(CLOCK_MONOTONIC, &now) != 0)
  {
    return std::unexpected(std::error_code{errno, std::generic_category()});
  }
  return static_cast<std::uint64_t>(now.tv_sec) * 1'000'000'000U +
         static_cast<std::uint64_t>(now.tv_nsec);
}
```

## A constructor that can fail

Don't throw from a constructor. Make the constructor private and add a
static `Create` that returns `std::expected`. The constructor then only
stores a resource that has already been acquired, so it can't fail.

```cpp
class File final
{
public:
  [[nodiscard]] static std::expected<File, std::error_code> Create(
      const std::filesystem::path& p_path)
  {
    const int fd = ::open(p_path.c_str(), O_RDONLY | O_CLOEXEC);
    if (fd < 0)
    {
      return std::unexpected(std::error_code{errno, std::generic_category()});
    }
    return File{fd};
  }

  ~File()
  {
    if (fd_ >= 0)
    {
      ::close(fd_);
    }
  }

  File(const File&) = delete;
  File& operator=(const File&) = delete;

  File(File&& p_other) noexcept : fd_(std::exchange(p_other.fd_, -1))
  {
  }

  File& operator=(File&& p_other) noexcept
  {
    if (this != &p_other)
    {
      if (fd_ >= 0)
      {
        ::close(fd_);
      }
      fd_ = std::exchange(p_other.fd_, -1);
    }
    return *this;
  }

  [[nodiscard]] int Fd() const noexcept
  {
    return fd_;
  }

private:
  explicit File(int p_fd) noexcept : fd_(p_fd)
  {
  }

  int fd_;
};
```

If the only resource is a pointer or a descriptor with a simple close
function, a `std::unique_ptr` with a custom deleter is shorter. The SQLite
handles in `collector/storage.hpp` work this way.

## When an exception is allowed

Exceptions are not banned, but each one has to be justified. One is
allowed only in these places:

1. **Code we don't own that throws**: `std::thread`'s constructor,
   `std::filesystem` calls that have no `std::error_code` overload,
   allocation, and so on. Use the non-throwing overload when one exists.
   Otherwise catch at the narrowest boundary and convert to
   `std::expected`. Let `std::bad_alloc` terminate the program.
2. **The last-resort handler in `main`.** One `catch (const std::exception&)`
   logs the error and returns a non-zero exit code. It catches bugs. It is
   not the error-handling design.
3. **Test helpers.** In `tests/*.cpp` a failed check may throw to abort the
   current test case.

Exceptions are never used:

- on the per-datagram or per-sample path;
- for operating errors (a bad packet, a missing day file, a busy database);
- as control flow, such as `try { ... } catch (...) { continue; }` in a
  loop;
- to cross a module boundary. A function that a caller can call returns
  `std::expected`.

We don't build with `-fno-exceptions`. The standard library still throws
(allocation, `std::thread`, some `std::filesystem` calls), and the cases
above need the mechanism.

Some existing code predates this rule: the `SqliteError` and
`std::system_error` throws in `collector/storage.hpp`,
`collector/http.hpp`, `sampler/io.hpp` and `sampler/main.cpp`. When you
change one of these functions, convert it to `std::expected` in the same
change. Don't mix the conversion with unrelated edits.

## `noexcept`

Mark a function `noexcept` when it really can't throw: moves, swaps,
destructors, accessors, and pure arithmetic on trivial types. Don't add it
to a function that allocates or calls something that might throw. With
exceptions enabled, a wrong `noexcept` turns an exception into
`std::terminate`.
