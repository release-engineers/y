# y

A tool like yq (and jq) but without their feature of completely cleaning up your YAML documents. yq and jq are great tools especially for making
changes to documents that are not intended to be human-readable. However, when you want to make changes programmatically to documents and still be
able to read them afterwards, they're probably not the best tools for the job.

**y** aims to be a tool familiar for users of yq and jq while preserving your YAML's comments, block & flow style, key ordering, anchor names & more.

<img src="./docs/cinema.svg">

Install the `y` CLI utility and Python package with;

```bash
pip install re-y
```

## Usage

**y** comes with an expression language similar to yq which can be used to select and edit parts of a YAML document. Here's examples for a
YAML document 'sample.yml';

```yaml
---
a:
  b:
    # comments and whitespace are preserved
    # unless the object owning them is removed or replaced
    c:
      - d: 1
      # replacing the array element `d: 1` above would remove this comment (and any potential whitespace around it)
      - e: 2
      - f: 3
```

```bash
#!/usr/bin/env bash
# modify a file in-place
y --inplace --file sample.yml -- '.a.b.c[0] = 123'
```

```bash
#!/usr/bin/env bash
# write to stdout
y --file sample.yml -- '.a.b.c[0] = 123'
```

### Expressions

| Selectors | Description                                  | Example                           |
|-----------|----------------------------------------------|-----------------------------------|
| `.`       | Select the root of the expression context    | `y --file sample.yml '.'`         |
| `.key`    | Select field `key` within the context        | `y --file sample.yml '.a.b.c'`    |
| `[index]` | Select element at `index` within the context | `y --file sample.yml '.a.b.c[0]'` |
| `$`       | Select the root of the program context.      | `y --file sample.yml '$'`         |

| Operators                                 | Description                                                                                          | Example                            |
|-------------------------------------------|------------------------------------------------------------------------------------------------------|------------------------------------|
| `expression = expression`                 | Assign a value a given reference                                                                     | `y --file sample.yml '.a = .a.b'`  |
| `expression + expression`                 | Mathematical operators `+`, `-`, `/`, `*`, `%` and `^`                                               | `y '.1 + 2 * 4'`                   |
| <code>expression &#124; expression</code> | Pipe operator; pass the output of the left-hand expression as context for the right-hand expression. | <code>y -- '2 &#124; . * 2'</code> |
| `(expression)`                            | Precedence operator; evaluate the expression within parentheses first.                               | <code>y '(2 &#124; . * 2)'</code>  |

:information_source: Regarding mathematical operators; `^` is evaluated first, then `*`, `/` and `%` are evaluated left-to-right, and finally `+`
and `-` are evaluated left-to-right.

:warning: Assigning precedence to mathematical operators with parentheses is not supported.

:information_source: The pipe operator `|` modifies the expression context (`.`) of the right-hand expression to the output of the left-hand
expression, hence the availability of the `$` operator to select the root of the program context.

| Constants | Description                       | Example     |
|-----------|-----------------------------------|-------------|
| `true`    | Boolean values `true` and `false` | `y 'true'`  |
| `null`    | Null value                        | `y 'null'`  |
| `123`     | Numbers                           | `y '123'`   |
| `"abc"`   | Strings                           | `y '"abc"'` |

## Contributing

### Requirements & Installation

**y** is being developed on Python 3.9 & Poetry.

Build with Poetry:

```bash
poetry build
```

Install with Poetry:

```bash
poetry install
```

Run with your favorite shell:

```bash
./bin/y
```
