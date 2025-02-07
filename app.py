from flask import Flask, request, jsonify, render_template
from source.function import read_file, text_splitter, download_openai_embeddings  
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from source.promting import * 
import os

app = Flask(__name__)

load_dotenv()

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("API keys are missing. Please check your .env file.")

embeddings = download_openai_embeddings()

index_name = "chatbot-index"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":2})

llm = ChatOpenAI(model="ft:gpt-4o-2024-08-06:personal:chtbt-081024:AFz8pTD0", temperature=0.5, max_tokens=None)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg")
    if msg:
        response = rag_chain.invoke({"input": msg})
        full_answer = response["answer"]
        answer = full_answer.split("System:", 1)[-1] if "System:" in full_answer else full_answer
        return answer.strip()
    else:
        return "No message provided", 400

if __name__ == '__main__':
    app.run(debug=False)
