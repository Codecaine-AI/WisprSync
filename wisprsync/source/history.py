from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from wisprsync.core.constants import HISTORY_COLUMNS
from wisprsync.source.sqlite import connect_readonly, has_table


def history_count(path: Path) -> int | None:
    for immutable in (False, True):
        try:
            with connect_readonly(path, immutable=immutable) as conn:
                if not has_table(conn, "History"):
                    return None
                return int(conn.execute("select count(*) from History").fetchone()[0])
        except sqlite3.Error:
            continue
    return None


def history_select_sql(limit: int | None = None) -> str:
    columns = ", ".join(f'"{column}"' for column in HISTORY_COLUMNS)
    sql = f'select {columns} from "History" order by timestamp, transcriptEntityId'
    if limit is not None:
        sql += f" limit {int(limit)}"
    return sql


def row_to_plain_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}
