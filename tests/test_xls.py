from io import BytesIO
from pathlib import Path

import anyio
import pytest
from fastapi import UploadFile

from asynctor.xls import df_to_datas, load_xls, read_excel


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
