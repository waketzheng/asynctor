from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

import anyio
import pandas as pd

if TYPE_CHECKING:
    from fastapi import UploadFile


FilePathType: TypeAlias = str | Path | anyio.Path


async def read_excel(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str: bool = False, **kw
) -> pd.DataFrame:
    """Read excel from local file or bytes

    :param as_str: whether to read as dtype=str
    :param kw: other kwargs that will pass to the `pd.read_excel` function
    """
    if isinstance(file, (str, Path, BytesIO, bytes)):
        await anyio.lowlevel.checkpoint()
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
    return [dict(zip(cols, v, strict=False)) for v in df.values.tolist()]


async def load_xlsx(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str=False, **kw
) -> list[dict]:
    """Read excel file or content to be list of dict"""
    return df_to_datas(await read_excel(file, as_str, **kw))


class Excel:
    def __init__(self, filename: str | Path) -> None:
        self._path = Path(filename)

    @staticmethod
    def to_df(data: list[dict[str, Any]]) -> pd.DataFrame:
        columns = list(data[0].keys())
        df_data: dict[str, list[Any]] = {c: [] for c in columns}
        for d in data:
            for k, v in d.items():
                df_data[k].append(v)
        return pd.DataFrame(df_data)

    @classmethod
    def write_buffer(cls, data: list[dict[str, Any]] | pd.DataFrame) -> BytesIO:
        if not isinstance(data, pd.DataFrame):
            data = cls.to_df(data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            data.to_excel(writer, index=False)
        buffer.seek(0)
        return buffer

    def write(self, data: list[dict[str, Any]] | pd.DataFrame) -> None:
        df = data if isinstance(data, pd.DataFrame) else self.to_df(data)
        return df.to_excel(self._path, index=False)

    async def awrite(self, data: list[dict[str, Any]] | pd.DataFrame) -> None:
        bio = self.write_buffer(data)
        await anyio.Path(self._path).write_bytes(bio.getvalue())

    def read(self, as_str: bool = False, **kw) -> pd.DataFrame:
        return pd_read_excel(self._path, as_str, **kw)

    async def aread(self, as_str: bool = False, **kw) -> pd.DataFrame:
        return await read_excel(anyio.Path(self._path), as_str, **kw)
