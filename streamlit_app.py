import openai
import streamlit as st
import time
import pandas as pd
from typing import Optional

class AssistantManager:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.assistant_id = None
        self.thread_id = None

    def setup_assistant(self, file_path: Optional[str] = None) -> None:
        file_id = None
        if file_path:
            with open(file_path, "rb") as file:
                response = openai.File.create(
                    file=file,
                    purpose='answers'
                )
                file_id = response['id']

        response = openai.Assistant.create(
            name="Data Analyst Assistant",
            instructions="You are a personal Data Analyst Assistant",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}],
            tool_resources={'code_interpreter': {'file_ids': [file_id]}} if file_id else None
        )
        self.assistant_id = response['id']

        response = openai.Thread.create()
        self.thread_id = response['id']

    def process_query(self, query: str) -> str:
        if not self.assistant_id or not self.thread_id:
            return "Assistant not initialized. Please set up the assistant first."

        response = openai.ThreadMessage.create(
            thread_id=self.thread_id,
            role="user",
            content=query
        )

        response = openai.ThreadRun.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            instructions=query
        )

        while True:
            time.sleep(1)
            run_status = openai.ThreadRun.retrieve(
                thread_id=self.thread_id,
                run_id=response['id']
            )
            if run_status['status'] == 'completed':
                break
            elif run_status['status'] in ['failed', 'cancelled', 'expired']:
                return f"Error: Run ended with status {run_status['status']}"

        messages = openai.ThreadMessage.list(
            thread_id=self.thread_id
        )

        for message in messages:
            if message['role'] == "assistant":
                return message['content']

        return "No response received"

def initialize_session_state():
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = ''
    if 'assistant_manager' not in st.session_state:
        st.session_state['assistant_manager'] = None

def main():
    st.title("OpenAI Assistant Interface")
    initialize_session_state()

    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        if st.button("Submit API Key"):
            if api_key:
                st.session_state['api_key'] = api_key
                try:
                    st.session_state['assistant_manager'] = AssistantManager(api_key)
                    st.session_state['assistant_manager'].setup_assistant()
                    st.success("API key saved and assistant initialized!")
                except Exception as e:
                    st.error(f"Error initializing assistant: {str(e)}")
            else:
                st.error("Please enter an API key")

    if st.session_state['assistant_manager'] is None:
        st.warning("Please configure your API key in the sidebar")
        return

    uploaded_file = st.file_uploader("Upload a CSV file", type=['csv'])
    if uploaded_file:
        # Read the file into a DataFrame
        df = pd.read_csv(uploaded_file)
        st.write(df)
        # Process the DataFrame as needed

    query = st.text_area("Enter your query:")
    if st.button("Submit Query"):
        with st.spinner("Processing query..."):
            response = st.session_state['assistant_manager'].process_query(query)
            st.write("Response:", response)

if __name__ == "__main__":
    main()
