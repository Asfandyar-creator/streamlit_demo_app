import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os

# Function to process PDFs and extract business problems
def process_pdfs(pdf_file):
    try:
        # Save uploaded PDF to a temporary file
        temp_pdf_path = f"temp_{pdf_file.name}"
        with open(temp_pdf_path, "wb") as temp_file:
            temp_file.write(pdf_file.read())

        # Load PDF
        loader = PyPDFLoader(temp_pdf_path)
        documents = loader.load()

        if not documents:
            raise ValueError("No content extracted from PDF")

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        texts = text_splitter.split_documents(documents)

        if not texts:
            raise ValueError("No text chunks created")

        # Create embeddings
        embeddings = OpenAIEmbeddings(api_key='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')
        vectorstore = FAISS.from_documents(texts, embeddings)

        # Initialize QA chain
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0, api_key='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')
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        query = "What are the main business problems described in these documents? Provide a clear and concise summary."
        result = qa_chain.invoke(query)

        # Remove temporary file
        os.remove(temp_pdf_path)

        return result

    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit app
st.title("PDF Business Problem Analyzer")
st.write("Upload a PDF document to analyze and extract a summary of the main business problems described.")

# File uploader
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None:
    st.write("Processing your PDF...")
    result = process_pdfs(uploaded_file)

    if "Error:" in result:
        st.error(result)
    else:
        st.success("Analysis Complete!")
        st.subheader("Identified Business Problems:")
        st.write(result)
