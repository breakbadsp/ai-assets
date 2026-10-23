---
name: cpp-classes-and-composition
description: "C++ class design: class versus struct, Rule of Zero and Rule of Five, explicit constructors, final, virtual destructors, overrides, composition over inheritance, no const or reference members. Read when you define or change a class or struct."
disable-model-invocation: true
---

# Classes and composition


| Rule | Summary |
|------|---------|
| **C.2** | `class` if there is an invariant; `struct` if the members vary independently |
| **C.9** | Expose as little as possible |
| **C.20** | Rule of Zero: don't write special members if you don't need them |
| **C.21** | Rule of Five: if you write or delete one, handle all five |
| **C.35** | A base destructor is public virtual or protected non-virtual |
| **C.41** | A constructor produces a fully initialized object |
| **C.46** | Single-argument constructors are `explicit` |
| **C.128** | An override uses exactly one of `virtual`, `override`, `final` |
| — | Mark a class `final` unless it is meant to be a base |
| — | Inheritance is always `public`. If you want private inheritance, use a member |

```cpp
// Avoid: inheriting only to reuse FormatLine(). A logger is not a formatter.
class Logger : public Formatter
{
};

// Prefer: the logger has a formatter.
class Logger final
{
public:
  void Write(std::string_view p_text)
  {
    std::println(stderr, "{}", formatter_.FormatLine(p_text));
  }

private:
  Formatter formatter_;
};
```

- **Data members are not `const` and not references.** Either one makes the
  class impossible to assign, and a `const` member can't be moved from.
  Make the member private with no setter.
- Don't call virtual functions from a constructor or destructor.
- Don't `memset` / `memcpy` a type that isn't trivially copyable.
