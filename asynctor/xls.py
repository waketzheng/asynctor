from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Union

import anyio
import pandas as pd

if TYPE_CHECKING:
    from fastapi import UploadFile

    from ._types import TypeAlias

FilePathType: TypeAlias = Union[str, Path, anyio.Path]


async def read_excel(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str: bool = False, **kw
) -> pd.DataFrame:
    """Read excel from local file or bytes

    :param as_str: whether to read as dtype=str
    :param kw: other kwargs that will pass to the `pd.read_excel` function
    """
    if isinstance(file, (str, Path, BytesIO, bytes)):
        return pd_read_excel(file, as_str, **kw)
    if isinstance(file, anyio.Path):
        content = await file.read_bytes()
    else:  # UploadFile
        content = await file.read()
    return pd_read_excel(content, as_str, **kw)


def pd_read_excel(
    file: str | Path | BytesIO | bytes, as_str: bool = False, *, keep_default_na: bool = False, **kw
) -> pd.DataFrame:
    if as_str and "dtype" not in kw:
        kw.setdefault("dtype", str)
    kw.update(keep_default_na=keep_default_na)
    return pd.read_excel(BytesIO(file) if isinstance(file, bytes) else file, **kw)


def df_to_datas(df: pd.DataFrame) -> list[dict]:
    """Convert dataframe to list of dict"""
    cols = list(df.columns)
    return [dict(zip(cols, v)) for v in df.values.tolist()]


async def load_xls(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str=False, **kw
) -> list[dict]:
    """Read excel file or content to be list of dict"""
    return df_to_datas(await read_excel(file, as_str, **kw))
