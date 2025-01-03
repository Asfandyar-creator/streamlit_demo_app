import streamlit as st
import openai
import time

def create_assistant(api_key, file_path):
    client = openai.OpenAI(api_key=api_key)
    
    # Upload file
    file = client.files.create(
        file=open(file_path, "rb"),
        purpose='assistants'
    )
    
    # Create assistant
    assistant = client.beta.assistants.create(
        name="Data Analyst Assistant",
        instructions="You are a personal Data Analyst Assistant",
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}],
        tool_resources={'code_interpreter': {'file_ids': [file.id]}}
    )
    
    return client, assistant, file

def process_query(client, thread_id, assistant_id, query):
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=query,
    )
    
    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=query,
    )
    
    # Wait for completion
    with st.spinner('Processing...'):
        while True:
            time.sleep(2)
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                st.error(f"Run failed with status: {run_status.status}")
                return None
    
    # Get messages
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages

def main():
    st.title("Data Analysis Assistant")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        submit_key = st.button("Submit API Key")
    
    # Initialize session state
    if 'client' not in st.session_state:
        st.session_state.client = None
        st.session_state.assistant = None
        st.session_state.thread = None
    
    # Set up assistant when API key is submitted
    if submit_key and api_key:
        try:
            client, assistant, file = create_assistant(api_key, "Titanic-Dataset.csv")
            thread = client.beta.threads.create()
            st.session_state.client = client
            st.session_state.assistant = assistant
            st.session_state.thread = thread
            st.success("Assistant configured successfully!")
        except Exception as e:
            st.error(f"Error setting up assistant: {str(e)}")
    
    # Main interface
    if st.session_state.client:
        query = st.text_input("Enter your query about the dataset:")
        if st.button("Submit Query"):
            if query:
                messages = process_query(
                    st.session_state.client,
                    st.session_state.thread.id,
                    st.session_state.assistant.id,
                    query
                )
                
                if messages:
                    st.subheader("Results")
                    for message in reversed(list(messages)):
                        with st.container():
                            st.write(f"**{message.role.title()}**:")
                            for content in message.content:
                                if content.type == 'text':
                                    st.write(content.text.value)

if __name__ == "__main__":
    main()
