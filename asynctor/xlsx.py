"""Helpers for reading and writing Excel files with pandas.

The async helpers accept FastAPI ``UploadFile`` objects and ``anyio.Path`` in
addition to regular local paths and in-memory content. DataFrame conversion is
kept intentionally small so callers can still use pandas directly when they
need advanced Excel options.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

import anyio
import pandas as pd
from anyio.lowlevel import checkpoint

if TYPE_CHECKING:
    from fastapi import UploadFile


FilePathType: TypeAlias = str | Path | anyio.Path


async def read_excel(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str: bool = False, **kw
) -> pd.DataFrame:
    """Read an Excel file into a pandas DataFrame.

    ``file`` may be a local path, an ``anyio.Path``, raw bytes, ``BytesIO``, or
    a FastAPI ``UploadFile``. Keyword arguments are forwarded to
    ``pandas.read_excel``.

    :param file: Excel source to read.
    :param as_str: if True, default ``dtype`` to ``str`` unless explicitly provided.
    :param kw: additional keyword arguments for ``pandas.read_excel``.
    :return: parsed Excel content as a DataFrame.
    """
    if isinstance(file, (str, Path, BytesIO, bytes)):
        # Give async callers a scheduling point before the synchronous pandas read.
        await checkpoint()
        return pd_read_excel(file, as_str, **kw)
    if isinstance(file, anyio.Path):
        content = await file.read_bytes()
    else:  # UploadFile
        content = await file.read()
    return pd_read_excel(content, as_str, **kw)


def pd_read_excel(
    file: str | Path | BytesIO | bytes, as_str: bool = False, *, keep_default_na: bool = False, **kw
) -> pd.DataFrame:
    """Read Excel content using pandas with asynctor defaults.

    By default, empty cells are preserved as empty strings instead of pandas
    converting them to ``NaN``. Pass ``keep_default_na=True`` to restore pandas'
    default missing-value handling.

    :param file: local path, ``BytesIO``, or raw Excel bytes.
    :param as_str: if True, default ``dtype`` to ``str`` unless explicitly provided.
    :param keep_default_na: forwarded to ``pandas.read_excel``.
    :param kw: additional keyword arguments for ``pandas.read_excel``.
    :return: parsed Excel content as a DataFrame.
    """
    if as_str and "dtype" not in kw:
        kw.setdefault("dtype", str)
    kw.update(keep_default_na=keep_default_na)
    # pandas.read_excel needs a file-like wrapper for raw bytes.
    return pd.read_excel(BytesIO(file) if isinstance(file, bytes) else file, **kw)


def df_to_datas(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to row-oriented dictionaries.

    Column names are used as dictionary keys and each DataFrame row becomes one
    dictionary in the returned list.

    :param df: DataFrame to convert.
    :return: list of row dictionaries.
    """
    cols = list(df.columns)
    return [dict(zip(cols, v, strict=False)) for v in df.values.tolist()]


async def load_xlsx(
    file: UploadFile | FilePathType | BytesIO | bytes, as_str=False, **kw
) -> list[dict]:
    """Read Excel content and return row-oriented dictionaries.

    This is a convenience wrapper around ``read_excel`` and ``df_to_datas`` for
    API handlers that want JSON-ready data instead of a DataFrame.

    :param file: Excel source accepted by ``read_excel``.
    :param as_str: if True, default ``dtype`` to ``str`` unless explicitly provided.
    :param kw: additional keyword arguments for ``pandas.read_excel``.
    :return: list of row dictionaries.
    """
    return df_to_datas(await read_excel(file, as_str, **kw))


class Excel:
    """Small convenience wrapper for reading and writing one Excel file.

    ``Excel`` stores the target path once and exposes synchronous and async
    helpers for common DataFrame/list-of-dict workflows.

    Usage::
        >>> filename = 'my.xlsx'
        >>> df: pd.DataFrame = await Excel(filename).aread()
        >>> new_file = 'your.xlsx'
        >>> await Excel(new_file).awrite(df)
        >>> Path(filename).read_bytes() == Path(new_file).read_bytes()
        True
    """

    def __init__(self, filename: str | Path) -> None:
        """Create an Excel helper bound to ``filename``.

        :param filename: target Excel file path.
        """
        self._path = Path(filename)

    @staticmethod
    def to_df(data: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert a non-empty list of dictionaries to a DataFrame.

        The first row defines the output columns. Later rows should use the same
        keys for predictable output.

        :param data: non-empty list of row dictionaries.
        :return: DataFrame built from the supplied rows.
        """
        columns = list(data[0].keys())
        df_data: dict[str, list[Any]] = {c: [] for c in columns}
        for d in data:
            for k, v in d.items():
                df_data[k].append(v)
        return pd.DataFrame(df_data)

    @classmethod
    def write_buffer(cls, data: list[dict[str, Any]] | pd.DataFrame) -> BytesIO:
        """Write Excel content to an in-memory buffer.

        :param data: DataFrame or list of row dictionaries to serialize.
        :return: ``BytesIO`` positioned at the beginning of the generated file.
        """
        if not isinstance(data, pd.DataFrame):
            data = cls.to_df(data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            data.to_excel(writer, index=False)
        buffer.seek(0)
        return buffer

    def write(self, data: list[dict[str, Any]] | pd.DataFrame) -> None:
        """Write rows or a DataFrame to the configured Excel path.

        :param data: DataFrame or list of row dictionaries to write.
        """
        df = data if isinstance(data, pd.DataFrame) else self.to_df(data)
        return df.to_excel(self._path, index=False)

    async def awrite(self, data: list[dict[str, Any]] | pd.DataFrame) -> None:
        """Asynchronously write rows or a DataFrame to the configured path.

        The Excel file is rendered in memory first, then written with
        ``anyio.Path.write_bytes``.

        :param data: DataFrame or list of row dictionaries to write.
        """
        bio = self.write_buffer(data)
        await anyio.Path(self._path).write_bytes(bio.getvalue())

    def read(self, as_str: bool = False, **kw) -> pd.DataFrame:
        """Synchronously read the configured Excel path.

        :param as_str: if True, default ``dtype`` to ``str`` unless explicitly provided.
        :param kw: additional keyword arguments for ``pandas.read_excel``.
        :return: parsed Excel content as a DataFrame.
        """
        return pd_read_excel(self._path, as_str, **kw)

    async def aread(self, as_str: bool = False, **kw) -> pd.DataFrame:
        """Asynchronously read the configured Excel path.

        :param as_str: if True, default ``dtype`` to ``str`` unless explicitly provided.
        :param kw: additional keyword arguments for ``pandas.read_excel``.
        :return: parsed Excel content as a DataFrame.
        """
        return await read_excel(anyio.Path(self._path), as_str, **kw)
