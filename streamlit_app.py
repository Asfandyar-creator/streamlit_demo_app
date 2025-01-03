import streamlit as st
import pandas as pd
import openai
import time
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

# Initialize Wikipedia tools
wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)

# Streamlit app
st.title("AI Data Analyst Assistant")

# Sidebar settings
st.sidebar.title("Settings")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")
api_key_submit = st.sidebar.button("Submit API Key")

if api_key_submit:
    if openai_api_key:
        client = openai.OpenAI(api_key=openai_api_key)
        st.sidebar.success("API Key submitted successfully!")
    else:
        st.sidebar.error("Please provide your OpenAI API key.")

# Task selection
option = st.sidebar.radio(
    "Choose a task:",
    ("Upload Dataset for Analysis", "Wikipedia Search")
)

if option == "Upload Dataset for Analysis":
    st.header("Dataset Analysis Assistant")
    uploaded_file = st.file_uploader("Upload your CSV file:", type=["csv"])
    question = st.text_input("Ask a question about your dataset:")
    
    if st.button("Analyze"):
        if openai_api_key and uploaded_file and question.strip():
            try:
                # Create file for assistant
                file = client.files.create(
                    file=uploaded_file,
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

                # Create thread and add message
                thread = client.beta.threads.create()
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=question
                )

                # Run assistant
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    instructions=question
                )

                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    
                    if run_status.status == 'completed':
                        progress_bar.progress(100)
                        status_text.success("Analysis complete!")
                        break
                    elif run_status.status in ['failed', 'cancelled', 'expired']:
                        status_text.error(f"Analysis failed: {run_status.status}")
                        break
                    else:
                        progress_bar.progress(50)
                        status_text.info("Analyzing...")
                        time.sleep(2)

                if run_status.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    
                    for message in reversed(list(messages)):
                        if message.role == "assistant":
                            for content in message.content:
                                if content.type == 'text':
                                    st.write(content.text.value)

                # Cleanup
                client.beta.assistants.delete(assistant.id)
                client.files.delete(file.id)

            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please ensure API key is submitted and file is uploaded.")

elif option == "Wikipedia Search":
    st.header("Wikipedia Search")
    search_query = st.text_input("Enter your search query:")
    
    if st.button("Search"):
        if search_query:
            try:
                with st.spinner("Searching Wikipedia..."):
                    result = wiki_tool.run(search_query)
                    st.write("Search Results:")
                    st.write(result)
            except Exception as e:
                st.error(f"Error during search: {str(e)}")
        else:
            st.warning("Please enter a search query.")
