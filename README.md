# y

Like yq (and jq) but without their feature of cleaning up your yaml.

# features

- Preserves preserve, comments, block style, flow style, key ordering, and anchor names and others. See
  also [Ruamel YAML docs](https://yaml.readthedocs.io/).
- An expression language (a subset similar to yq and jq).

Note that this does not preserve indentation, instead indentation can be configured through options.

# installation

?

## requirements

- Python 3

```bash
pip install -r requirements.txt
```
