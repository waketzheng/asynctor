from pathlib import Path

import anyio
import pytest

from asynctor.xls import df_to_datas, load_xls, read_excel


@pytest.mark.anyio
async def test_read():
    demo = Path(__file__).parent / "demo.xlsx"
    df = await read_excel(demo)
    df2 = await read_excel(demo.read_bytes())
    df3 = await read_excel(anyio.Path(demo))
    assert df2.compare(df).empty and df3.compare(df).empty
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
