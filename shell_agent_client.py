import requests
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path

def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")



url = "http://127.0.0.1:8000/generate"

class QwenHTTP(LLM):
    @property
    def _llm_type(self) -> str:
        return "qwen_http"

    def _call(self, prompt: str, stop=None) -> str:
        resp = requests.post(
            url,
            json={
                "prompt": prompt,
                "max_new_tokens": 256,
            },
            timeout=300,
        )

        resp.raise_for_status()
        return resp.json()["response"]

def main():
    llm = QwenHTTP()

    # llm = HuggingFacePipeline(pipeline=text_gen_pipeline)
    print("--------------------------------")
    # prompt = PromptTemplate(
    #     input_variables=["history", "input"],
    #     template=("You are a helpful shell assistant.\n"
    #               "You convert natural language into safe shell commands.\n"
    #               "Conversation history: \n {history}\n\n"
    #               "User: {input}\n"
    #               "Assistant: "),
    #     )
    prompt_text = load_prompt("prompts/shell_assistant_prompt.txt")
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=prompt_text,
    )
    
    memory = ConversationBufferMemory(memory_key="history", return_messages=False,)

    chain = (
        {
            "history": lambda _: memory.load_memory_variables({})["history"],
            "input": RunnablePassthrough(),
        }
        | prompt
        | llm
    )

    while True: # CLI loop
        user_input = input("User: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break

        response = chain.invoke(user_input)
        print(f"Assistant: {response}")
        print("--------------------------------")


if __name__ == "__main__":
    main()

