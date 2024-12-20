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

# Load environment variables
load_dotenv()

# Retrieve Pinecone and OpenAI API keys from environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Ensure API keys are present
if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("API keys are missing. Please check your .env file.")

# Initialize embeddings
embeddings = download_openai_embeddings()

# Define Pinecone index name
index_name = "chatbot-index"

# Initialize Pinecone Vector Store from an existing index
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

# Configure retriever for similarity search with top 3 results
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":2})

# Setup OpenAI language model with specified parameters
llm = ChatOpenAI(model="ft:gpt-4o-2024-08-06:personal:chtbt-081024:AFz8pTD0",temperature=0.5, max_tokens=None)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# llm = ChatOpenAI(model="gpt-4",temperature=0.7, max_tokens=500)
# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", system_prompt),
#         ("human", "{input}"),
#     ]
# )

# Combine retrieval and answering chains
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# Define index route to render the main page
@app.route("/")
def index():
    return render_template('index.html')

# Define route to handle chat messages
@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg")
    if msg:
        response = rag_chain.invoke({"input": msg})
        full_answer = response["answer"]
        
        # Process and return the response, stripping out "System:" part if present
        answer = full_answer.split("System:", 1)[-1] if "System:" in full_answer else full_answer
        return answer.strip()  # Return only the text part of the answer
    else:
        return "No message provided", 400

# Run the application
if __name__ == '__main__':
    app.run(debug=True)  # Set debug=False for production settings
