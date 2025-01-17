from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

import anyio
import pandas as pd

FilePathType = Union[str, Path, anyio.Path]


async def read_excel(file: FilePathType | bytes, as_str=False, **kw) -> pd.DataFrame:
    """Read excel from local file or bytes

    :param as_str: whether to read as dtype=str
    :param kw: other kwargs that will pass to the `pd.read_excel` function
    """
    if isinstance(file, anyio.Path):
        file = await file.read_bytes()
    if as_str and "dtype" not in kw:
        kw.setdefault("dtype", str)
    kw.setdefault("keep_default_na", False)
    if isinstance(file, bytes):
        return pd.read_excel(BytesIO(file), **kw)
    else:
        return pd.read_excel(file, **kw)


def df_to_datas(df: pd.DataFrame) -> list[dict]:
    """Convert dataframe to list of dict"""
    cols = list(df.columns)
    return [dict(zip(cols, v)) for v in df.values.tolist()]


async def load_xls(file: FilePathType | bytes, as_str=False, **kw) -> list[dict]:
    """Read excel file or content to be list of dict"""
    return df_to_datas(await read_excel(file, as_str, **kw))
