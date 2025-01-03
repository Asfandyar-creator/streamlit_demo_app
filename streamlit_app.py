import streamlit as st
import pandas as pd
import openai
import time

# Streamlit app
st.title("AI Data Analyst Assistant")

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

# Main app logic
option = st.sidebar.radio(
    "Choose a task:",
    ("Upload Dataset for Analysis",)
)

if option == "Upload Dataset for Analysis":
    st.header("Dataset Analysis Assistant")
    uploaded_file = st.file_uploader(
        "Upload your CSV file:",
        type=["csv"]
    )
    question = st.text_input("Ask a question about your dataset:")
    
    if st.button("Analyze"):
        if openai_api_key:
            if uploaded_file and question.strip():
                try:
                    # Read the uploaded file into a DataFrame
                    df = pd.read_csv(uploaded_file)
                    
                    # Display a preview of the data
                    st.subheader("Data Preview")
                    st.dataframe(df.head())

                    # Convert DataFrame to string for model input
                    data_preview = df.head().to_string()

                    # OpenAI API call
                    st.write("Analyzing your dataset...")
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a data analyst assistant."},
                            {"role": "user", "content": f"Here is a preview of the data:\n{data_preview}\n\nQuestion: {question}"}
                        ]
                    )

                    # Display the assistant's response
                    st.success("Analysis Result:")
                    st.write(response['choices'][0]['message']['content'])
                
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
            else:
                st.warning("Please upload a file and enter a question.")
        else:
            st.error("API key is missing. Please enter it in the sidebar and click Submit.")
