from io import BytesIO
from pathlib import Path

import anyio
import pandas as pd

FileLike = str | Path | anyio.Path | bytes


async def read_excel(file: FileLike, as_str=False, **kw) -> pd.DataFrame:
    """Read excel from local file or bytes

    :param as_str: whether to read as dtype=str
    """
    if isinstance(file, str | Path | anyio.Path):
        file = await anyio.Path(file).read_bytes()
    if as_str:
        kw.setdefault("dtype", str)
    return pd.read_excel(BytesIO(file), keep_default_na=False, **kw)


def df_to_datas(df: pd.DataFrame) -> list[dict]:
    """Convert dataframe to list of dict"""
    cols = list(df.columns)
    values: list[list] = df.values.tolist()
    return [dict(zip(cols, v)) for v in values]


async def load_xls(file: FileLike, as_str=False, **kw) -> list[dict]:
    """Read excel file or content to be list of dict"""
    return df_to_datas(await read_excel(file, as_str, **kw))
