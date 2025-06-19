import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_INDEX_NAME = "chatbot-index"
    
    @classmethod
    def validate(cls):
        if not cls.PINECONE_API_KEY or not cls.OPENAI_API_KEY:
            raise ValueError("API keys are missing. Please check your .env file.")