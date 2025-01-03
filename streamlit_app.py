import streamlit as st
import pandas as pd
import tempfile
import openai
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

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

        # Convert the DataFrame to a string for model input
        data_preview = df.head().to_string()  # Use only the first few rows for brevity

        # Generate response using OpenAI ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analyst assistant."},
                {"role": "user", "content": f"Here is a preview of the data:\n{data_preview}\n\nQuestion: {question}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error processing file: {str(e)}"

# Streamlit app
st.title("AI Research & Data Insights Assistant")

# Sidebar for OpenAI API Key
st.sidebar.title("Settings")
api_key_submit = st.sidebar.button("Submit API Key")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")

if api_key_submit:
    if openai_api_key:
        openai.api_key = openai_api_key
        st.sidebar.success("API Key submitted successfully!")
    else:
        st.sidebar.error("Please provide your OpenAI API key.")

# Sidebar interaction options
option = st.sidebar.radio(
    "How would you like to interact?",
    ("Wikipedia Research", "Upload File for Data Insights")
)

if option == "Wikipedia Research":
    st.header("Wikipedia Research")
    user_query = st.text_input("Enter your query:")
    if st.button("Search"):
        if openai_api_key:
            if user_query.strip():
                result = wiki_tool.run(user_query)
                st.success("Result:")
                st.write(result)
            else:
                st.warning("Please enter a query.")
        else:
            st.error("API key is missing. Please enter it in the sidebar and click Submit.")

elif option == "Upload File for Data Insights":
    st.header("Upload File for Data Insights")
    uploaded_file = st.file_uploader(
        "Upload your CSV, XLS, or XLSX file here:",
        type=["csv", "xls", "xlsx"]
    )
    question = st.text_input("Ask a question about your dataset:")
    if st.button("Analyze"):
        if openai_api_key:
            if uploaded_file and question.strip():
                result = analyze_file(uploaded_file, question)
                st.success("Insight:")
                st.write(result)
            else:
                st.warning("Please upload a file and enter a question.")
        else:
            st.error("API key is missing. Please enter it in the sidebar and click Submit.")
