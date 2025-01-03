import streamlit as st
import openai
import time
import pandas as pd
from typing import Optional

class AssistantManager:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.assistant_id = None
        self.thread_id = None
        
    def setup_assistant(self, file_path: Optional[str] = None) -> None:
        file_id = None
        if file_path:
            file = self.client.files.create(
                file=open(file_path, "rb"),
                purpose='assistants'
            )
            file_id = file.id
            
        assistant = self.client.beta.assistants.create(
            name="Data Analyst Assistant",
            instructions="You are a personal Data Analyst Assistant",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}],
            tool_resources={'code_interpreter': {'file_ids': [file_id]}} if file_id else None
        )
        self.assistant_id = assistant.id
        
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id

    def process_query(self, query: str) -> str:
        if not self.assistant_id or not self.thread_id:
            return "Assistant not initialized. Please set up the assistant first."
            
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=query
        )
        
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            instructions=query
        )
        
        while True:
            time.sleep(1)
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return f"Error: Run ended with status {run_status.status}"
        
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread_id
        )
        
        # Get the latest assistant message
        for message in messages:
            if message.role == "assistant":
                return message.content[0].text.value
        
        return "No response received"

def main():
    st.title("OpenAI Assistant Interface")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        if st.button("Submit API Key"):
            st.session_state['api_key'] = api_key
            st.success("API key saved!")
    
    if 'assistant_manager' not in st.session_state and 'api_key' in st.session_state:
        st.session_state['assistant_manager'] = AssistantManager(st.session_state['api_key'])
        st.session_state['assistant_manager'].setup_assistant()
        st.success("Assistant initialized!")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload a CSV file", type=['csv'])
    if uploaded_file and 'assistant_manager' in st.session_state:
        # Save uploaded file temporarily
        with open("temp.csv", "wb") as f:
            f.write(uploaded_file.getvalue())
        st.session_state['assistant_manager'].setup_assistant("temp.csv")
        st.success("File uploaded and assistant updated!")
    
    # Query input
    query = st.text_area("Enter your query:")
    if st.button("Submit Query"):
        if 'assistant_manager' not in st.session_state:
            st.error("Please submit an API key first")
        else:
            with st.spinner("Processing query..."):
                response = st.session_state['assistant_manager'].process_query(query)
                st.write("Response:", response)

if __name__ == "__main__":
    main()
