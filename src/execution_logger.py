"""
执行日志模块

记录所有命令的执行历史，支持导出为 CSV。
日志文件：data/execution_log.jsonl（每行一条 JSON）
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Optional


_DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "execution_log.jsonl"


class ExecutionLogger:
    """结构化执行日志，写入 JSONL，支持 CSV 导出。"""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        natural_language: str,
        command: str,
        risk_level: str,
        returncode: Optional[int],
        elapsed_sec: float,
        session_id: str = "",
    ) -> None:
        """追加写入一条执行记录。"""
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id": session_id,
            "natural_language": natural_language,
            "command": command,
            "risk_level": risk_level,
            "returncode": returncode,
            "success": returncode == 0 if returncode is not None else None,
            "elapsed_sec": round(elapsed_sec, 4),
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def export_csv(self, output_path: Path) -> int:
        """
        将全部日志导出为 CSV。
        返回导出的记录条数。
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "timestamp", "session_id", "natural_language",
            "command", "risk_level", "returncode", "success", "elapsed_sec",
        ]

        records = self._load_all()
        with output_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)

        return len(records)

    def _load_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        records = []
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records
