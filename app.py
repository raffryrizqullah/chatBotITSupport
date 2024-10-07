import os
import time
import pdfplumber
from openai import OpenAI
from flask import Flask, request, render_template, session
from flask_session import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    """Extracts and returns text from a given PDF file."""
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Extract base knowledge from PDF
base_knowledge_path = "pdf/binder-4.pdf"
base_knowledge = extract_text_from_pdf(base_knowledge_path)

@app.route('/')
def index():
    """Renders the index page and clears the session."""
    session.clear()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests and responds with AI generated text, using session for memory context."""
    user_message = request.json.get('message')

    # Update session with the conversation history
    if 'conversation' not in session:
        session['conversation'] = []
    session['conversation'].append({"role": "user", "content": user_message})

    messages = [
        {"role": "system", "content": "You are a helpful assistant for BSI UII IT Support. Use the provided knowledge base to answer user queries, but always improve upon the information by summarizing, analyzing, or adding additional helpful context. Please only provide answers in Indonesia language and based on the following document. Do not copy the information verbatim."},
        *session['conversation'],
        {"role": "assistant", "content": base_knowledge}
    ]

    time.sleep(1)  # Simulate processing delay

    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal:contoh-chatbot:AEgHLyZ2",
        messages=messages,
        temperature=0.7
    )

    ai_message = response.choices[0].message.content.strip()
    session['conversation'].append({"role": "assistant", "content": ai_message})
    return {"reply": ai_message}

if __name__ == '__main__':
    app.run(debug=True)
