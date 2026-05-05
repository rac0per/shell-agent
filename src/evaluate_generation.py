"""生成质量评估脚本（自动化版本）。

针对20条代表性查询，调用运行中的模型服务器并评估：
1) 命令语法正确率（validate_syntax）
2) 语义匹配分数（字符级F1，作为 ChrF 近似）
3) 安全沙箱 dry-run 成功率（simulate_command）
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.command_safety import classify_command, simulate_command, validate_syntax

_QUERY_FILE = Path(__file__).resolve().parent.parent / "data" / "eval" / "generation_eval_queries.json"
_DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "eval" / "generation_eval_results.csv"
_DEFAULT_SUMMARY = Path(__file__).resolve().parent.parent / "data" / "eval" / "generation_eval_summary.json"
_DEFAULT_SERVER = os.getenv("SHELL_AGENT_SERVER_URL", "http://127.0.0.1:8000")


def _call_generate(server: str, query: str, session_id: str) -> str:
    resp = requests.post(
        f"{server}/generate",
        json={"input": query, "session_id": session_id, "target_shell": "bash"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def _extract_first_json_object(text: str) -> Dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def _extract_command(raw_response: str) -> str:
    """从模型响应中提取命令字段（容错解析）。"""
    obj = _extract_first_json_object(raw_response)
    if obj is not None:
        cmd = str(obj.get("command", "")).strip()
        if cmd:
            return cmd

    # 当 JSON 不完整时，回退到字段级提取
    m = re.search(r'"command"\s*:\s*"((?:\\.|[^"\\])*)"', raw_response, re.DOTALL)
    if m:
        raw = m.group(1)
        try:
            return json.loads(f'"{raw}"').strip()
        except Exception:
            return raw.replace('\\"', '"').replace('\\\\', '\\').strip()

    # 标签格式
    m = re.search(
        r'(?:^|\n)\s*(?:命令|command)\s*[：:]\s*(.+?)(?=\n\s*(?:说明|explanation|警告|warning)\s*[：:]|\Z)',
        raw_response,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()

    return ""


def _char_f1(reference: str, predicted: str) -> float:
    """字符级F1，作为 ChrF 的轻量近似。"""
    ref = [ch for ch in reference if not ch.isspace()]
    pred = [ch for ch in predicted if not ch.isspace()]
    if not ref and not pred:
        return 1.0
    if not ref or not pred:
        return 0.0

    from collections import Counter

    c_ref = Counter(ref)
    c_pred = Counter(pred)
    overlap = sum(min(c_ref[ch], c_pred[ch]) for ch in c_ref)
    precision = overlap / len(pred)
    recall = overlap / len(ref)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _syntax_status(command: str) -> str:
    if not command:
        return "fail"
    ok, _ = validate_syntax(command, shell="bash")
    return "pass" if ok else "fail"


def _sandbox_status(command: str) -> str:
    """仅执行安全模块 dry-run，不执行真实写操作。"""
    if not command:
        return "fail"

    safety = classify_command(command, shell="bash")
    if not safety.allowed:
        return "blocked"

    try:
        preview = simulate_command(command, shell="bash")
        return "pass" if isinstance(preview, str) else "fail"
    except Exception:
        return "fail"


def _semantic_status(chrf1: float) -> str:
    if chrf1 >= 0.80:
        return "high"
    if chrf1 >= 0.50:
        return "medium"
    return "low"


def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    syntax_pass = sum(1 for r in results if r["syntax_check"] == "pass")
    sandbox_pass = sum(1 for r in results if r["sandbox_check"] == "pass")
    sandbox_blocked = sum(1 for r in results if r["sandbox_check"] == "blocked")
    semantic_high = sum(1 for r in results if r["semantic_level"] == "high")
    semantic_medium = sum(1 for r in results if r["semantic_level"] == "medium")
    chrf1_avg = sum(float(r["semantic_chrf1"]) for r in results) / total if total else 0.0

    return {
        "total": total,
        "syntax_pass": syntax_pass,
        "syntax_pass_rate": round(syntax_pass / total, 4) if total else 0.0,
        "semantic_chrf1_avg": round(chrf1_avg, 4),
        "semantic_high": semantic_high,
        "semantic_medium": semantic_medium,
        "semantic_high_or_medium_rate": round((semantic_high + semantic_medium) / total, 4) if total else 0.0,
        "sandbox_pass": sandbox_pass,
        "sandbox_blocked": sandbox_blocked,
        "sandbox_pass_rate": round(sandbox_pass / total, 4) if total else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成质量离线评估脚本")
    parser.add_argument("--server", default=_DEFAULT_SERVER)
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT))
    parser.add_argument("--summary", default=str(_DEFAULT_SUMMARY))
    args = parser.parse_args()

    queries = json.loads(_QUERY_FILE.read_text(encoding="utf-8"))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id", "category", "query", "reference_command",
        "generated_raw", "extracted_command",
        "syntax_check",
        "semantic_chrf1",
        "semantic_level",
        "sandbox_check",
        "notes",
    ]

    results = []
    total = len(queries)
    for i, item in enumerate(queries, 1):
        qid = item["id"]
        category = item["category"]
        query = item["query"]
        ref = item["reference_command"]

        print(f"[{i}/{total}] id={qid} category={category}: {query[:40]}…", flush=True)

        session_id = f"gen_eval_{qid}"
        try:
            raw = _call_generate(args.server, query, session_id)
        except requests.RequestException as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            raw = ""

        extracted = _extract_command(raw)
        syntax = _syntax_status(extracted)
        semantic = _char_f1(ref, extracted)
        sandbox = _sandbox_status(extracted)

        results.append({
            "id": qid,
            "category": category,
            "query": query,
            "reference_command": ref,
            "generated_raw": raw.replace("\n", " | "),
            "extracted_command": extracted,
            "syntax_check": syntax,
            "semantic_chrf1": f"{semantic:.4f}",
            "semantic_level": _semantic_status(semantic),
            "sandbox_check": sandbox,
            "notes": "",
        })
        time.sleep(0.5)  # avoid session ID collision

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    summary = _summarize(results)
    summary_path = Path(args.summary)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n完成。共 {total} 条查询。")
    print(f"语法正确率: {summary['syntax_pass']}/{summary['total']} ({summary['syntax_pass_rate']*100:.1f}%)")
    print(f"语义匹配(ChrF1近似)均值: {summary['semantic_chrf1_avg']:.4f}")
    print(f"语义高/中匹配占比: {(summary['semantic_high_or_medium_rate']*100):.1f}%")
    print(f"沙箱 dry-run 成功率: {summary['sandbox_pass']}/{summary['total']} ({summary['sandbox_pass_rate']*100:.1f}%)")
    print(f"沙箱拦截率: {summary['sandbox_blocked']}/{summary['total']}")
    print(f"结果保存至: {output_path}")
    print(f"汇总保存至: {summary_path}")


if __name__ == "__main__":
    main()
