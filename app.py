import os
import time
import pdfplumber
from openai import OpenAI
from flask import Flask, request, render_template, session
from flask_session import Session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

base_knowledge_path = "pdf/binder1.pdf"
base_knowledge = extract_text_from_pdf(base_knowledge_path)

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    template = """ """

    if 'conversation' not in session:
        session['conversation'] = []
    session['conversation'].append({"role": "user", "content": user_message})

    messages = [
        {"role": "system", "content": """You are the best bsi uii it support team representative. I have shared my knowledge base with you and you will give the best answer.
            and you will follow ALL of the rules below:
            1/ Response should be very similar or even identical to the past best practices, 
            in terms of length, ton of voice, logical arguments and other details
            2/ If the best practice are irrelevant, then try to mimic the style of the best practice to user"""},
        *session['conversation'],
        {"role": "assistant", "content": base_knowledge}
    ]

    time.sleep(1)

    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal:contoh-chatbot:AEgHLyZ2",
        messages=messages,
        temperature=0.
    )

    ai_message = response.choices[0].message.content.strip()
    session['conversation'].append({"role": "assistant", "content": ai_message})
    return {"reply": ai_message}

if __name__ == '__main__':
    app.run(debug=True)
