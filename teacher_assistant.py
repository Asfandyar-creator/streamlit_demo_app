import streamlit as st
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
import openai
import time

# Initialize Wikipedia tool
wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)

# Initialize OpenAI Client
def initialize_openai_client(api_key):
    return openai.OpenAI(api_key=api_key)

def analyze_data_with_openai(file, client, user_prompt):
    # Step 1: Upload file to OpenAI
    uploaded_file = client.files.create(file=open(file, "rb"), purpose="assistants")

    # Step 2: Create Assistant
    assistant = client.beta.assistants.create(
        name="Data Analyst Assistant",
        instructions="You are a personal Data Analyst Assistant",
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}],
        tool_resources={"code_interpreter": {"file_ids": [uploaded_file.id]}},
    )

    # Step 3: Create Thread
    thread = client.beta.threads.create()

    # Step 4: Add Message and Run Analysis
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=user_prompt,
    )

    # Wait for run to complete
    while True:
        time.sleep(5)
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            return [{"type": "error", "value": f"Run ended with status: {run_status.status}"}]

    # Process completed results
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    results = []
    for message in reversed(list(messages)):
        for content in message.content:
            if content.type == "text":
                results.append({"type": "text", "value": content.text.value})

            elif content.type == "image_file":
                # Process image content in memory
                image_data = client.files.content(content.image_file.file_id)
                image_bytes = image_data.read()
                results.append({"type": "image", "value": image_bytes})
    return results


# Custom CSS to fix chat input at bottom
st.markdown("""
    <style>
        .stChatFloatingInputContainer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem;
            z-index: 1000;
        }
        .main {
            padding-bottom: 100px;  /* Add padding to prevent content from being hidden behind chat input */
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings
st.sidebar.header("Settings")

option = st.sidebar.selectbox(
    "Select an option:",
    ["Wikipedia Search", "Data Analysis"],
)

if option == "Wikipedia Search":
    st.header("Wikipedia Search")

    # Initialize separate session state for Wikipedia chat
    if "wiki_messages" not in st.session_state:
        st.session_state.wiki_messages = []

    main_container = st.container()

    with main_container:
        for message in st.session_state.wiki_messages:
            if message["role"] == "user":
                st.chat_message("user").markdown(f"**User**: {message['content']}")
            elif message["role"] == "assistant":
                st.chat_message("assistant").markdown(f"**Assistant**: {message['content']}")

    query = st.chat_input("Enter your search query:")

    if query:
        st.session_state.wiki_messages.append({"role": "user", "content": query})
        with main_container:
            st.chat_message("user").markdown(f"**User**: {query}")

            with st.spinner("Searching Wikipedia..."):
                try:
                    result = wiki_tool.run(query)
                    st.session_state.wiki_messages.append({"role": "assistant", "content": result})
                    st.chat_message("assistant").markdown(f"**Assistant**: {result}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

elif option == "Data Analysis":
    st.header("Data Analysis")

    # Initialize separate session state for Data Analysis chat
    if "analysis_messages" not in st.session_state:
        st.session_state.analysis_messages = []

    api_key = st.secrets["openai_api_key"]
    uploaded_file = st.sidebar.file_uploader("Upload a .csv or .xlsx file", type=["csv", "xlsx"])

    if uploaded_file and api_key:
        import pandas as pd

        # Display the first 5 rows of the uploaded file
        try:
            if uploaded_file.name.endswith(".csv"):
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                data = pd.read_excel(uploaded_file)

            st.subheader("Preview of Uploaded File")
            st.dataframe(data.head(5))
        except Exception as e:
            st.error(f"Could not read the file: {e}")

        main_container = st.container()

        with main_container:
            for message in st.session_state.analysis_messages:
                if message["role"] == "user":
                    st.chat_message("user").markdown(f"**User**: {message['content']}")
                elif message["role"] == "assistant":
                    if isinstance(message["content"], bytes):  # For image content
                        st.chat_message("assistant").image(message["content"], caption="Assistant Generated Image")
                    else:  # For text content
                        st.chat_message("assistant").markdown(f"**Assistant**: {message['content']}")

        prompt = st.chat_input("Enter your analysis request:")

        if prompt:
            st.session_state.analysis_messages.append({"role": "user", "content": prompt})
            with main_container:
                st.chat_message("user").markdown(f"**User**: {prompt}")

                with st.spinner("Analyzing data..."):
                    try:
                        client = initialize_openai_client(api_key)
                        results = analyze_data_with_openai(uploaded_file.name, client, prompt)

                        for result in results:
                            if result["type"] == "text":
                                st.session_state.analysis_messages.append({"role": "assistant", "content": result["value"]})
                                st.chat_message("assistant").markdown(f"**Assistant**: {result['value']}")
                            elif result["type"] == "image":
                                st.session_state.analysis_messages.append({"role": "assistant", "content": result["value"]})
                                st.chat_message("assistant").image(result["value"], caption="Assistant Generated Image")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
    elif not api_key:
        st.warning("Please provide your OpenAI API key in the secrets file.")
    elif not uploaded_file:
        st.warning("Please upload a file for analysis.")
