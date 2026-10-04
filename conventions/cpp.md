# C++ naming and style conventions

Apply these conventions globally to new and edited C++ code, including
headers, source files, tests, templates, and lambdas. Do not apply them to
other programming languages or rename unrelated existing code.

Use the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
as the baseline for naming not covered here. These are the user's explicit
conventions. They take precedence over Google C++ Style defaults, including the parameter prefix, struct member
suffix, enumerator naming, and Allman brace placement.

## Naming

- **Functions and methods:** PascalCase (`SubmitLimitOrder`, `CancelOrder`).
- **Every named function parameter:** `p_` + snake_case (`p_order_id`,
  `p_price_level`), including free functions, methods, and lambdas.
- **Local variables:** snake_case (`order_id`, `price_level`); no `p_` prefix.
- **Classes, structs, types, and template parameters:** PascalCase
  (`OrderNode`, `PriceLevel`, `Book`, `TNode`).
- **Class and struct data members:** snake_case with a mandatory trailing
  underscore (`order_id_`), including members of nested helper classes
  and test fixtures. Structs remain passive aggregates; use a class for
  types that need to protect invariants.
- **Constants / `constexpr`:** `k` + PascalCase (`kMaxOrders`, `kInvalid`).
- **Enumerators:** PascalCase without a `k` prefix (`Side::Buy`). The first
  enumerator in every `enum class` must have an explicit initializer,
  usually `= 0`.
- **Namespaces:** lowercase with underscores for multiple words (`order_book`).
- **Macros:** avoid where possible; otherwise `ALL_CAPS_WITH_UNDERSCORES`.
- **Files:** lowercase with underscores or dashes. Preserve the project's
  existing header/source extensions (for example, `.hpp` / `.cpp` in
  `modern_exchng_cpp`, or `.h` / `.cc` elsewhere).

## Layout and design

- **Braces:** Allman style, with opening and closing braces on their own
  lines for every block.
- **Control flow:** braces are mandatory for every `if`, `else`, `while`,
  and `for`, including single-statement bodies.
- **Indentation:** 2 spaces per level; never tabs. Use the project's formatter
  and keep its configuration consistent with these conventions.
- **Design:** prefer composition over inheritance wherever a choice exists.
