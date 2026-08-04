# Duration parser

Write a module `duration.py` in the project root containing one public
function:

```python
def parse_duration(text: str) -> int:
    ...
```

It returns the total number of seconds a duration string represents.

## Contract

| input | result |
|---|---|
| `"30s"` | `30` |
| `"5m"` | `300` |
| `"1h"` | `3600` |
| `"1h30m"` | `5400` |
| `"2h15m30s"` | `8130` |
| anything it cannot parse | raises `ValueError` |

Units are hours (`h`), minutes (`m`), and seconds (`s`). When several
appear they are written largest-first and their values add together.

## Environment

- The Python standard library only. Do not import third-party packages
  and do not install anything.
- The file must be named `duration.py` and must sit in the project root.
- Run tests with `python -m pytest` from the project root.
