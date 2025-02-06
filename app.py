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

load_dotenv()  # Load environment variables from .env file

# Fetch API keys from environment variables or raise an error if not found
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("API keys are missing. Please check your .env file.")

# Download embeddings used for generating responses
embeddings = download_openai_embeddings()

index_name = "chatbot-index"  # Define index name for the vector store

# Initialize Pinecone vector store from an existing index
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

# Set up a document retriever for similarity-based searches
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":2})

# Initialize the language model with specific settings
llm = ChatOpenAI(model="ft:gpt-4o-2024-08-06:personal:chtbt-081024:AFz8pTD0", temperature=0.5, max_tokens=None)

# Prepare chat prompt template from previous interactions
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),  # Use system prompt defined elsewhere
        ("human", "{input}"),       # User input placeholder
    ]
)

# Combine document retrieval and processing into a single operation chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

@app.route("/")
def index():
    return render_template('index.html')  # Serve the main HTML template

@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg")  # Retrieve message from POST data
    if msg:
        response = rag_chain.invoke({"input": msg})  # Generate response using RAG chain
        full_answer = response["answer"]
        
        # Extract relevant part of the response, if formatted with 'System:'
        answer = full_answer.split("System:", 1)[-1] if "System:" in full_answer else full_answer
        return answer.strip()
    else:
        return "No message provided", 400  # Handle case where no message is provided

if __name__ == '__main__':
    app.run(debug=False)  # Run the Flask application without debug mode
