import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os
from io import BytesIO
import fitz  # PyMuPDF

class Document:
    """A wrapper class with page_content and metadata attributes."""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

def process_pdfs(pdf_file):
    try:
        # Set OpenAI API key from secrets
        openai_api_key = st.secrets["openai_api_key"]
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Load PDF using PyMuPDF
        pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
        documents = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            if text.strip():  # Add non-empty pages
                documents.append(Document(page_content=text, metadata={"page_number": page_num + 1}))

        if not documents:
            raise ValueError("No content extracted from PDF")

        st.success(f"Loaded {len(documents)} pages from PDF")

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        texts = text_splitter.split_documents(documents)

        if not texts:
            raise ValueError("No text chunks created")

        st.success(f"Created {len(texts)} text chunks")

        # Create embeddings
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)

        # Save vectorstore
        vectorstore.save_local("faiss_index")

        # Initialize QA chain
        llm = ChatOpenAI(model="gpt-4o")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        query = (
            "Analyze the content of this document and identify any business problems or challenges described. "
            "If no problems are mentioned, summarize the primary topics or data discussed in the PDF."
        )
        response = qa_chain.invoke(query)

        # Extract and process the result
        result = response.get("result", "No result found")
        if "no problems" in result.lower() or not result.strip():
            return "No specific business problems were identified. Here is an overview of the document's content:\n" + result
        return result

    except Exception as e:
        if "Incorrect API key provided" in str(e).lower():
            st.error("The provided OpenAI API key is invalid. Please check and try again.")
        else:
            st.error(f"Error: {str(e)}")
        return None

# Streamlit app
st.title("PDF Business Problems Extractor")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.success("File uploaded successfully.")

    if st.button("Process PDF"):
        st.info("Processing PDF. Please wait...")
        result = process_pdfs(uploaded_file.read())  # Pass file content directly
        if result:
            st.subheader("Document Analysis:")
            st.write(result)
