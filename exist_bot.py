import os
import sys
from io import StringIO
import logging

logging.basicConfig(level=logging.DEBUG)
import streamlit as st


# To be able to update the changes made to modules in localhost (press r)
def reload_module(module_name):
    import importlib
    import sys
    sys.path.append('modules')
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)
    return sys.modules[module_name]


history_module = reload_module('history')
layout_module = reload_module('layout')
utils_module = reload_module('utils')
sidebar_module = reload_module('sidebar')

ChatHistory = history_module.ChatHistory
Layout = layout_module.Layout
Utilities = utils_module.Utilities
Sidebar = sidebar_module.Sidebar

st.set_page_config(layout="wide", page_icon="💬", page_title="IPRO-FileReader 🤖")

# Instantiate the main components
layout, sidebar, utils = Layout(), Sidebar(), Utilities()

layout.show_header("PDF, TXT")

os.environ["OPENAI_API_KEY"] = "OPENAI_API_KEY"

uploaded_file = utils.handle_upload(["pdf", "txt", "csv"])

if uploaded_file:

    # Configure the sidebar
    sidebar.show_options()

    # Initialize chat history
    history = ChatHistory()
    try:
        st.write("Before setting up chatbot")
        chatbot = utils.setup_chatbot(
            uploaded_file
        )
        st.write("After setting up chatbot")
        st.session_state["chatbot"] = chatbot

        if st.session_state["ready"]:
            # Create containers for chat responses and user prompts
            response_container, prompt_container = st.container(), st.container()

            with prompt_container:
                # Display the prompt form
                is_ready, user_input = layout.prompt_form()

                # Initialize the chat history
                history.initialize(uploaded_file)

                # Reset the chat history if button clicked
                if st.session_state["reset_chat"]:
                    history.reset(uploaded_file)

                if is_ready:
                    # Update the chat history and display the chat messages
                    history.append("user", user_input)

                    old_stdout = sys.stdout
                    sys.stdout = captured_output = StringIO()

                    output = st.session_state["chatbot"].conversational_chat(user_input)

                    sys.stdout = old_stdout

                    history.append("assistant", output)

                    # # Clean up the agent's thoughts to remove unwanted characters
                    # thoughts = captured_output.getvalue()
                    # cleaned_thoughts = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', thoughts)
                    # cleaned_thoughts = re.sub(r'\[1m>', '', cleaned_thoughts)

                    # # Display the agent's thoughts
                    # with st.expander("Display the agent's thoughts"):
                    #     st.write(cleaned_thoughts)

            history.generate_messages(response_container)
    except Exception as e:
        st.error(f"Error: {str(e)}")
