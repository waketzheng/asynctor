from __future__ import annotations

from .xlsx import Excel, df_to_datas, pd_read_excel, read_excel
from .xlsx import load_xlsx as load_xls

# Leave it here for compatibility
__all__ = ("Excel", "df_to_datas", "load_xls", "pd_read_excel", "read_excel")
