import streamlit as st
import pandas as pd
from typing import List
import openai
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

# Set your OpenAI API key
openai.api_key = "your_openai_api_key_here"

# Initialize Wikipedia tool
wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=700)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)

# File analysis function
def analyze_file(file, question: str):
    """
    Analyze a file and respond to a user's question.
    
    Args:
        file: Uploaded file (CSV/XLS/XLSX).
        question: User's query about the data.
    
    Returns:
        Insights or analysis from the data.
    """
    try:
        # Read the file into a DataFrame
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return "Unsupported file format. Please upload a CSV or Excel file."
        
        # Upload file to OpenAI assistant
        file_obj = openai.File.create(file=file, purpose="assistants")
        
        assistant = openai.Assistant.create(
            name="Data Analyst Assistant",
            instructions="You are a personal Data Analyst Assistant.",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}],
            tool_resources={"code_interpreter": {"file_ids": [file_obj["id"]]}}
        )
        
        # Create a thread
        thread = openai.Thread.create()
        
        # Run assistant
        run = openai.Thread.Run.create(
            thread_id=thread["id"],
            assistant_id=assistant["id"],
            instructions=question
        )
        
        # Wait for completion
        while True:
            status = openai.Thread.Run.retrieve(
                thread_id=thread["id"],
                run_id=run["id"]
            )
            if status["status"] == "completed":
                messages = openai.Thread.Message.list(thread_id=thread["id"])
                return messages[-1]["content"]["text"]
            elif status["status"] in ["failed", "cancelled", "expired"]:
                return f"Error: {status['status']}"
    except Exception as e:
        return f"Error processing file: {str(e)}"

# Streamlit app
st.title("AI Research & Data Insights Assistant")

st.sidebar.title("Choose an Option")
option = st.sidebar.radio(
    "How would you like to interact?",
    ("Wikipedia Research", "Upload File for Data Insights")
)

if option == "Wikipedia Research":
    st.header("Wikipedia Research")
    user_query = st.text_input("Enter your query:")
    if st.button("Search"):
        if user_query.strip():
            result = wiki_tool.run(user_query)
            st.success("Result:")
            st.write(result)
        else:
            st.warning("Please enter a query.")

elif option == "Upload File for Data Insights":
    st.header("Upload File for Data Insights")
    uploaded_file = st.file_uploader(
        "Upload your CSV, XLS, or XLSX file here:",
        type=["csv", "xls", "xlsx"]
    )
    question = st.text_input("Ask a question about your dataset:")
    if st.button("Analyze"):
        if uploaded_file and question.strip():
            result = analyze_file(uploaded_file, question)
            st.success("Insight:")
            st.write(result)
        else:
            st.warning("Please upload a file and enter a question.")
