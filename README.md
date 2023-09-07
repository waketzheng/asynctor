# asyncur
Some async functions that using anyio

## Requirements

Python 3.11+

## Installation

<div class="termy">

```console
$ pip install "asyncur"
---> 100%
Successfully installed asyncur
```

## Usage

- Read Excel File
```py
>>> from asycur.xls import load_xls
>>> await load_xls('tests/demo.xlsx')
[{'Column1': 'row1-\\t%c', 'Column2\nMultiLines': 0, 'Column 3': 1, 4: ''}, {'Column1': 'r2c1\n00', 'Column2\nMultiLines': 'r2 c2', 'Column 3': 2, 4: ''}]
```
