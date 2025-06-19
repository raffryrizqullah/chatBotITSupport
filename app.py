import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask, request, render_template
from config.settings import Config
from src.core.embeddings import get_openai_embeddings
from src.core.vector_store import get_vector_store, get_retriever
from src.services.chat_service import ChatService

app = Flask(__name__)

# Validate configuration
Config.validate()

# Initialize embeddings and vector store
embeddings = get_openai_embeddings()
vector_store = get_vector_store(embeddings)
retriever = get_retriever(vector_store)

# Initialize chat service
chat_service = ChatService(retriever)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_chat_response():
    user_message = request.form.get("msg")
    return chat_service.get_response(user_message)

if __name__ == "__main__":
    app.run(debug=False)
