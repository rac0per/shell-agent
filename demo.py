from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import BaseOutputParser
import re

class CommandParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        code_block = re.search(r"```(?:bash|shell)?\n(.+?)```", text, re.S)
        if code_block:
            cmd = code_block.group(1).strip()
            return cmd.rstrip("`")

        cmd = re.search(r"([a-zA-Z0-9_\-]+(?:\s+[^\n\r]+)?)", text)
        if cmd:
            return cmd.group(1).strip().rstrip("`")

        return text.strip().rstrip("`")

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-1fb95b0914de4cb0819e5fcc77f19538",
    base_url="https://api.deepseek.com",
    temperature=0.2,
)

template = """
你是一名专业的 Linux 命令行助手。你的任务是根据用户需求生成一个可以直接执行的终端命令。
如果需要解释，请把解释放在命令之外。

用户需求：{query}

请给出最合适的命令。
"""

prompt = PromptTemplate(
    input_variables=["query"],
    template=template,
)

# 链式组合

parser = CommandParser()
chain = prompt | llm | parser

if __name__ == "__main__":
    user_query = "查看当前目录下所有文件，并按修改时间倒序排列"
    
    result = chain.invoke({"query": user_query})
    
    print("解析出的命令为：")
    print(result)
