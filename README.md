# y

A tool like yq (and jq) but without their feature of completely cleaning up your YAML documents. yq and jq are great tools especially for making
changes to documents that are not intended to be human-readable. However, when you want to make changes programmatically to documents and still be
able to read them afterwards, they're probably not the best tools for the job.

**y** aims to be a tool familiar for users of yq and jq while preserving your YAML's comments, block & flow style, key ordering, anchor names & more.

## Usage

**y** comes with an expression language similar to yq which can be used to select and edit parts of a YAML document. Here's examples for a
YAML document 'sample.yml';

```yaml
---
a:
  b:
    c:
      # comments and whitespace are preserved

      # unless the object owning them is removed or replaced
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

## Installation

Presently this project is not published to any package registry. Install from project directory like so;

```bash
poetry build
pip install ./y/dist/*.whl
```

This will make the `y` command available in to your PATH.

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

