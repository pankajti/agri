from langchain_openai import ChatOpenAI
from agri.config.config import load_env
import os
#load_env()
# Replace with your actual API key
llm = ChatOpenAI(
    model="gpt-4.1",   # Or gpt-5-turbo, gpt-5.5, etc., depending on API release
    temperature=0,
)

response = llm.invoke("Write me a haiku about LangChain and GPT-5.")
print(response.content)
