import pytest
import sys
import os
import csv
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.execution_logger import ExecutionLogger


@pytest.fixture
def tmp_logger(tmp_path):
    return ExecutionLogger(log_path=tmp_path / "test_log.jsonl")


class TestExecutionLogger:
    def test_log_creates_file(self, tmp_logger, tmp_path):
        tmp_logger.log(
            natural_language="列出文件",
            command="ls -la",
            risk_level="low",
            returncode=0,
            elapsed_sec=0.01,
            session_id="sess-1",
        )
        log_file = tmp_path / "test_log.jsonl"
        assert log_file.exists()

    def test_log_record_fields(self, tmp_logger, tmp_path):
        import json
        tmp_logger.log(
            natural_language="删除临时文件",
            command="rm -rf /tmp/test",
            risk_level="high",
            returncode=0,
            elapsed_sec=0.05,
            session_id="sess-abc",
        )
        log_file = tmp_path / "test_log.jsonl"
        record = json.loads(log_file.read_text(encoding="utf-8").strip())

        assert record["natural_language"] == "删除临时文件"
        assert record["command"] == "rm -rf /tmp/test"
        assert record["risk_level"] == "high"
        assert record["returncode"] == 0
        assert record["success"] is True
        assert record["elapsed_sec"] == 0.05
        assert record["session_id"] == "sess-abc"
        assert "timestamp" in record

    def test_log_appends_multiple_records(self, tmp_logger, tmp_path):
        for i in range(3):
            tmp_logger.log(
                natural_language=f"命令 {i}",
                command=f"echo {i}",
                risk_level="low",
                returncode=0,
                elapsed_sec=0.01,
            )
        log_file = tmp_path / "test_log.jsonl"
        lines = [l for l in log_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 3

    def test_log_failed_command_success_false(self, tmp_logger):
        tmp_logger.log(
            natural_language="失败命令",
            command="ls /nonexistent",
            risk_level="low",
            returncode=1,
            elapsed_sec=0.02,
        )
        records = tmp_logger._load_all()
        assert records[-1]["success"] is False

    def test_log_none_returncode(self, tmp_logger):
        tmp_logger.log(
            natural_language="无返回码",
            command="some_cmd",
            risk_level="medium",
            returncode=None,
            elapsed_sec=0.0,
        )
        records = tmp_logger._load_all()
        assert records[-1]["returncode"] is None
        assert records[-1]["success"] is None

    def test_export_csv_creates_file(self, tmp_logger, tmp_path):
        tmp_logger.log(
            natural_language="查看文件",
            command="cat file.txt",
            risk_level="low",
            returncode=0,
            elapsed_sec=0.01,
        )
        csv_path = tmp_path / "export.csv"
        count = tmp_logger.export_csv(csv_path)
        assert count == 1
        assert csv_path.exists()

    def test_export_csv_columns(self, tmp_logger, tmp_path):
        tmp_logger.log(
            natural_language="查看端口",
            command="ss -tlnp",
            risk_level="low",
            returncode=0,
            elapsed_sec=0.03,
            session_id="s1",
        )
        csv_path = tmp_path / "export.csv"
        tmp_logger.export_csv(csv_path)

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["natural_language"] == "查看端口"
        assert row["command"] == "ss -tlnp"
        assert row["risk_level"] == "low"
        assert row["returncode"] == "0"
        assert row["success"] == "True"
        assert row["session_id"] == "s1"

    def test_export_csv_empty_log(self, tmp_logger, tmp_path):
        csv_path = tmp_path / "empty.csv"
        count = tmp_logger.export_csv(csv_path)
        assert count == 0
        assert csv_path.exists()

    def test_export_csv_multiple_records(self, tmp_logger, tmp_path):
        for i in range(5):
            tmp_logger.log(
                natural_language=f"操作 {i}",
                command=f"echo {i}",
                risk_level="low",
                returncode=0,
                elapsed_sec=0.01,
            )
        csv_path = tmp_path / "multi.csv"
        count = tmp_logger.export_csv(csv_path)
        assert count == 5
