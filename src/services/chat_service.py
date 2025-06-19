from langchain_openai import ChatOpenAI
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompts.templates import IT_SUPPORT_SYSTEM_PROMPT

class ChatService:
    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.6,
            max_tokens=None,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", IT_SUPPORT_SYSTEM_PROMPT),
            ("human", "{input}"),
        ])
        self.chain = self._create_chain()
    
    def _create_chain(self):
        """Create RAG chain for document retrieval and answering."""
        document_chain = create_stuff_documents_chain(self.llm, self.prompt)
        return create_retrieval_chain(self.retriever, document_chain)
    
    def get_response(self, user_message):
        """Get chat response for user message."""
        if not user_message:
            return "No message provided", 400
        
        chain_response = self.chain.invoke({"input": user_message})
        full_answer = chain_response["answer"]
        
        # Clean up the response
        final_answer = (
            full_answer.split("System:", 1)[-1]
            if "System:" in full_answer
            else full_answer
        )
        return final_answer.strip()