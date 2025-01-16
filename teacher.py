import streamlit as st
import os
from typing import List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class TeacherAgent:
    def __init__(self):
        try:
            api_key = st.secrets["openai_api_key"]
            if not api_key:
                raise ValueError("OpenAI API key not found in secrets.toml file.")
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
            self.vector_store = None
            self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            self.conversation_chain = None
        except Exception as e:
            st.error(f"Error initializing TeacherAgent: {e}")

    def load_knowledge_base(self, pdf_paths: List[str]) -> None:
        try:
            documents = []
            for pdf_path in pdf_paths:
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(documents)

            # Create FAISS vector store
            self.vector_store = FAISS.from_documents(splits, self.embeddings)

            # Create a Conversational Retrieval Chain
            self.conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=ChatOpenAI(temperature=0.7, model_name="gpt-4"),
                retriever=self.vector_store.as_retriever(),
                memory=self.memory,
                verbose=True
            )
        except Exception as e:
            st.error(f"Error loading knowledge base: {e}")

    def guide_student(self, question: str) -> str:
        try:
            if not self.conversation_chain:
                return "Knowledge base is not loaded. Please upload PDFs first."
            response = self.conversation_chain({"question": question})
            return response["answer"]
        except Exception as e:
            return f"Error guiding student: {e}"

# Streamlit app
def main():
    #st.set_page_config(page_title="Teacher", layout="wide")
    st.title("Teacher App")

    # Sidebar for PDF upload
    with st.sidebar:
        with st.expander("Upload Knowledge Base", expanded=True):
            uploaded_files = st.file_uploader("Upload PDFs:", type=["pdf"], accept_multiple_files=True)

    teacher = TeacherAgent()

    # Load Knowledge Base
    if uploaded_files and teacher:
        pdf_paths = []
        for file in uploaded_files:
            temp_path = f"temp_{file.name}"
            with open(temp_path, "wb") as f:
                f.write(file.read())
            pdf_paths.append(temp_path)

        teacher.load_knowledge_base(pdf_paths)
        st.success("Knowledge base loaded successfully!")

        # Cleanup temp files
        for temp_path in pdf_paths:
            try:
                os.remove(temp_path)
            except Exception as e:
                st.warning(f"Could not delete temporary file: {e}")

    # Chat interface
    st.subheader("Chat with the Teacher")
    if teacher and teacher.vector_store:
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        user_input = st.chat_input("Ask your question")
        if user_input:
            st.session_state["chat_history"].append(("user", user_input))
            response = teacher.guide_student(user_input)
            st.session_state["chat_history"].append(("assistant", response))

        # Display chat messages in order (top to bottom)
        for role, message in st.session_state["chat_history"]:
            st.chat_message(role).write(message)
    else:
        st.warning("Initialize TeacherAgent and load a knowledge base to start chatting.")

if __name__ == "__main__":
    main()
