from flask import Flask, request, render_template
from source.function import download_openai_embeddings  
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

# Ambil API key dari variabel lingkungan
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("API keys are missing. Please check your .env file.")

# Unduh embeddings dari OpenAI
openaiEmbeddings = download_openai_embeddings()

# Nama indeks untuk Pinecone
PINECONE_INDEX_NAME = "chatbot-index"

# Inisialisasi penyimpanan vektor (vector store) dari indeks yang sudah ada
pineconeVectorStore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX_NAME, embedding=openaiEmbeddings
)

# Buat retriever untuk mencari dokumen berdasarkan kemiripan
documentRetriever = pineconeVectorStore.as_retriever(
    search_type="similarity", search_kwargs={"k": 2}
)

# Inisialisasi model bahasa untuk chat
chatLanguageModel = ChatOpenAI(
    # model="ft:gpt-4o-2024-08-06:personal:chtbt-081024:AFz8pTD0",
    model="gpt-4",
    temperature=0.5,
    max_tokens=None,
)

# Buat template prompt untuk chat
chatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", it_support_system_prompt_template),
        ("human", "{input}"),
    ]
)

# Buat chain untuk menjawab pertanyaan dengan menggabungkan dokumen
documentChain = create_stuff_documents_chain(chatLanguageModel, chatPromptTemplate)
retrievalAugmentedGenerationChain = create_retrieval_chain(documentRetriever, documentChain)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_chat_response():
    user_message = request.form.get("msg")
    if user_message:
        chain_response = retrievalAugmentedGenerationChain.invoke({"input": user_message})
        full_answer = chain_response["answer"]
        final_answer = (
            full_answer.split("System:", 1)[-1]
            if "System:" in full_answer
            else full_answer
        )
        return final_answer.strip()
    else:
        return "No message provided", 400

if __name__ == "__main__":
    app.run(debug=False)
