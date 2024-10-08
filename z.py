import fitz  # PyMuPDF
import os
import time
from pinecone import Pinecone, ServerlessSpec
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as LangchainPinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chains import RetrievalQA
from langchain.agents import Tool, initialize_agent

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Path to the PDF file
pdf_path = "pdf/Binder1.pdf"
pdf_text = extract_text_from_pdf(pdf_path)

# Create a DataFrame with the extracted text
import pandas as pd
data = {'text': [pdf_text]}
dataset = pd.DataFrame(data)

# Initialize Pinecone
api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)

cloud = os.environ.get('PINECONE_CLOUD') or 'aws'
region = os.environ.get('PINECONE_REGION') or 'us-east-1'
spec = ServerlessSpec(cloud=cloud, region=region)
index_name = 'langchain-retrieval-agent-fast'

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # Adjust dimension as needed
        metric='dotproduct',  # Adjust metric as needed
        spec=spec
    )

# Wait for the index to be ready
while not pc.describe_index(index_name).status['ready']:
    time.sleep(1)

index = pc.Index(index_name)
index.upsert_from_dataframe(dataset, batch_size=100)

openai_api_key = os.environ.get('OPENAI_API_KEY') or 'OPENAI_API_KEY'
model_name = 'text-embedding-ada-002'
embed = OpenAIEmbeddings(model=model_name, openai_api_key=openai_api_key)

text_field = "text"
vectorstore = LangchainPinecone(index, embed.embed_query, text_field)

query = "when was the college of engineering in the University of Notre Dame established?"
vectorstore.similarity_search(query, k=3)

llm = ChatOpenAI(openai_api_key=openai_api_key, model_name='gpt-3.5-turbo', temperature=0.0)
conversational_memory = ConversationBufferWindowMemory(memory_key='chat_history', k=5, return_messages=True)

qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())
qa.run(query)

tools = [
    Tool(
        name='Knowledge Base',
        func=qa.run,
        description='use this tool when answering general knowledge queries to get more information about the topic'
    )
]

agent = initialize_agent(
    agent='chat-conversational-react-description',
    tools=tools,
    llm=llm,
    verbose=True,
    max_iterations=3,
    early_stopping_method='generate',
    memory=conversational_memory
)

agent(query)
agent("what is 2 * 7?")
agent("can you tell me some facts about the University of Notre Dame?")
agent("can you summarize these facts in two short sentences")

# Uncomment below line to delete the index when done
# pc.delete_index(index_name)
