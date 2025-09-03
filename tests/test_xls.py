from __future__ import annotations

from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any

import anyio
import pandas as pd
import pytest

from asynctor.xls import Excel, df_to_datas, load_xls, read_excel

try:
    from fastapi import UploadFile
except ImportError:

    class UploadFile:  # type:ignore[no-redef]
        def __init__(self, file):
            self.file = file

        async def read(self) -> bytes:
            return self.file.read()


@pytest.mark.anyio
async def test_read():
    demo = Path(__file__).parent / "demo.xlsx"
    content = demo.read_bytes()
    df = await read_excel(demo)
    df2 = await read_excel(content)
    df3 = await read_excel(anyio.Path(demo))
    df4 = await read_excel(BytesIO(content))
    df5 = await read_excel(UploadFile(BytesIO(content)))
    assert df2.compare(df).empty and df3.compare(df).empty
    assert df4.compare(df).empty and df5.compare(df).empty
    data = df_to_datas(df)
    assert data == [
        {"Column1": "row1-\\t%c", "Column2\nMultiLines": 0, "Column 3": 1, 4: ""},
        {"Column1": "r2c1\n00", "Column2\nMultiLines": "r2 c2", "Column 3": 2, 4: ""},
    ]
    assert data == (await load_xls(demo))

    assert (await load_xls(demo, True)) == [
        {"Column1": "row1-\\t%c", "Column2\nMultiLines": "0", "Column 3": "1", 4: ""},
        {"Column1": "r2c1\n00", "Column2\nMultiLines": "r2 c2", "Column 3": "2", 4: ""},
    ]


def test_init_excel():
    filename = "a.xlsx"
    assert Excel(filename)._path == Excel(Path(filename))._path


@pytest.mark.usefixtures("tmp_work_dir")
class TestExcel:
    file = Path("a.xlsx")
    df_data: dict[str, list[Any]] = {
        "产品": ["苹果", "香蕉", "橙子"],
        "销量": [100, 150, 120],
        "单价": [5.5, 3.2, 4.8],
    }

    @cached_property
    def klass(self) -> Excel:
        return Excel(self.file)

    @cached_property
    def data(self) -> list[dict[str, Any]]:
        columns = list(self.df_data)
        length = len(self.df_data[columns[0]])
        lines: list[dict[str, Any]] = [dict.fromkeys(columns) for _ in range(length)]
        for key, value in self.df_data.items():
            for i, v in enumerate(value):
                lines[i][key] = v
        return lines

    def test_write(self):
        assert not self.klass._path.exists()
        self.klass.write(self.data)
        assert self.data == self.klass.read().to_dict(orient="records")
        assert self.klass._path.exists()
        self.klass._path.unlink()
        self.klass.write(pd.DataFrame(self.df_data))
        assert self.data == self.klass.read().to_dict(orient="records")

    @pytest.mark.anyio
    async def test_awrite(self):
        assert not self.klass._path.exists()
        await self.klass.awrite(self.data)
        assert self.data == (await self.klass.aread()).to_dict(orient="records")
        assert self.klass._path.exists()
        self.klass._path.unlink()
        await self.klass.awrite(pd.DataFrame(self.df_data))
        assert self.data == (await self.klass.aread()).to_dict(orient="records")
