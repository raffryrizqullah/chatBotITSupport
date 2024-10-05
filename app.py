import pdfplumber
from openai import OpenAI
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages
        text = ''
        for page in pages:
            text += page.extract_text()
    return text

base_knowledge_path = "pdf/binder-4.pdf"
base_knowledge = extract_text_from_pdf(base_knowledge_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    messages = [
        {"role": "system", "content": "You are a helpful assistant for BSI UII IT Support. Use the provided knowledge base to answer user queries, but always improve upon the information by summarizing, analyzing, or adding additional helpful context. Please only provide answers in indonesia language and based on the following document. Do not copy the information verbatim."},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": base_knowledge}
    ]

    time.sleep(1)

    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal:contoh-chatbot:AEgHLyZ2",
        messages=messages,
        temperature=0.9    )

    ai_message = response.choices[0].message.content.strip()

    return {"reply": ai_message}

if __name__ == '__main__':
    app.run(debug=True)