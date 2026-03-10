#!/usr/bin/env python3
"""
简单测试 parse_response 方法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 直接导入需要的类，避免复杂的模块导入
from memory.sqlite_memory import SQLiteMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path
import json
import re

class MockShellAgentCLI:
    """模拟的CLI类，只包含parse_response方法"""

    def parse_response(self, response: str) -> dict:
        """解析LLM响应，提取命令和说明"""
        import re

        # 清理响应文本
        response = response.strip()

        # 方法1: 尝试提取JSON格式（更灵活）
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "command": parsed.get("command", "").strip(),
                    "explanation": parsed.get("explanation", "").strip(),
                    "warning": parsed.get("warning", "").strip()
                }
            except json.JSONDecodeError:
                pass  # 继续其他方法

        # 方法2: 提取代码块（```bash 或 ```shell 或 ```）
        code_block_match = re.search(r'```(?:bash|shell|sh)?\n?(.*?)\n?```', response, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            command = code_block_match.group(1).strip()
            # 移除代码块后的文本作为说明
            explanation = response.replace(code_block_match.group(0), '').strip()
            return {
                "command": command,
                "explanation": explanation,
                "warning": ""
            }

        # 方法3: 提取$开头的单行命令
        dollar_match = re.search(r'^\$ (.+)$', response, re.MULTILINE)
        if dollar_match:
            command = dollar_match.group(1).strip()
            # 移除命令行后的文本作为说明
            explanation = response.replace(dollar_match.group(0), '').strip()
            return {
                "command": command,
                "explanation": explanation,
                "warning": ""
            }

        # 方法4: 查找可能的命令关键词（ls, cd, mkdir等）
        command_keywords = ['ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep', 'find', 'chmod', 'ps', 'kill', 'top', 'df', 'du', 'tar', 'gzip', 'ssh', 'scp']
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(line.startswith(kw + ' ') or line == kw for kw in command_keywords):
                command = line
                explanation = response.replace(line, '').strip()
                return {
                    "command": command,
                    "explanation": explanation,
                    "warning": ""
                }

        # 方法5: 默认返回整个响应作为说明，无命令
        return {
            "command": "",
            "explanation": response,
            "warning": "无法提取有效命令，请检查响应格式"
        }

def main():
    cli = MockShellAgentCLI()

    # 测试 JSON 格式
    test_input = '{"command": "ls -la", "explanation": "列出详细文件列表", "warning": ""}'
    result = cli.parse_response(test_input)
    print("JSON 测试:")
    print(f"  输入: {test_input}")
    print(f"  命令: {result['command']}")
    print(f"  说明: {result['explanation']}")
    print(f"  警告: {result['warning']}")
    print()

    # 测试代码块格式
    test_input2 = """使用以下命令：

```bash
find . -name "*.txt"
```

查找所有 txt 文件。"""
    result2 = cli.parse_response(test_input2)
    print("代码块测试:")
    print(f"  输入: {test_input2[:50]}...")
    print(f"  命令: {result2['command']}")
    print(f"  说明: {result2['explanation'][:50]}...")
    print(f"  警告: {result2['warning']}")

if __name__ == "__main__":
    main()