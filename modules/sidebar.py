import streamlit as st

class Sidebar:

    MODEL_OPTIONS = "gpt-3.5-turbo"
    TEMPERATURE_MIN_VALUE = 0.0
    TEMPERATURE_MAX_VALUE = 1.0
    TEMPERATURE_DEFAULT_VALUE = 0.0
    TEMPERATURE_STEP = 0.01


    @staticmethod
    def reset_chat_button():
        if st.button("Reset chat"):
            st.session_state["reset_chat"] = True
        st.session_state.setdefault("reset_chat", False)

    def show_options(self):
        with st.sidebar.expander("Reset", expanded=False):

            self.reset_chat_button()


    