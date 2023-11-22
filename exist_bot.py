import os
import PyPDF2
import openai
import streamlit as st
import re

st.set_page_config(page_title="IPRO-Chatbot", page_icon="IPRO-CHAT.png", layout="wide")
example_questions = ["Wie soll ich den Standort des Zimmers finden?", "Wie soll ich den Professor kontaktieren?",
                     "Wie soll ich meinen Semesterbeitrag bezahlen?"]


# Function to set the background color for areas not covered by the image
def set_background_color(color):
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {color};
    }}
    </style>
    """, unsafe_allow_html=True)


# Initialize the OpenAI client with the API key
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

# This Func is Not Available Now
# set_background_color("#9CC4CC")


BASE_DIR = os.getcwd()  # Set the base directory to "Files"


def generate_response(user_input):
    # GPT-3 and other parameters
    model_engine = "gpt-3.5-turbo-16k"
    temperature = 0.2
    qa_template = """
    Answer in the language of the question. If you're unsure or don't know the answer, respond with "Ich weiß es nicht,
    bitte wenden Sie sich an die zuständige Abteilung der HSEL".
    You represent the Hochschule Emden/Leer and your name is IPRO-ChatBot.
    Only answer based on the provided context. If the question is outside of the context, say "I don't know".
    For example:
        question: "What's the capital of France?"
        answer: "I don't know"

    context: {context}
    ========
    previous conversation:
    {previous_conversation}
    question: {question}
    ======
    """

    # Ensure the 'messages' list exists in the session state
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    # Build the string of previous conversation, including past Q&A
    previous_conversation = "\n".join(
        f"{msg['role']}: {msg['content']}" for msg in st.session_state['messages']
    )

    pdf_file_name = predict_intent_with_gpt(user_input)
    pdf_content = get_pdf_content(pdf_file_name)

    response = client.chat.completions.create(
        model=model_engine,
        messages=[
            {"role": "system",
             "content": qa_template.format(context=pdf_content, previous_conversation=previous_conversation,
                                           question=user_input)},
            {"role": "user", "content": user_input},
        ],
        temperature=temperature,
    )

    # Add the generated answer to the conversation history
    st.session_state['messages'].append(
        {"role": "assistant", "content": response.choices[0].message.content.strip()}
    )

    return response.choices[0].message.content.strip()


def get_pdf_content(file_path):
    file_path = file_path.strip("'")
    pdf_file_obj = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
    num_pages = len(pdf_reader.pages)
    text_content = ""
    for page in range(num_pages):
        page_obj = pdf_reader.pages[page]
        text_content += page_obj.extract_text()
    pdf_file_obj.close()
    return text_content


def predict_intent_with_gpt(question):
    # Use the updated valid_intents list
    max_attempts = 1
    attempts = 0
    while attempts < max_attempts:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "Predict the intent of the question. The answer must be one of the following: " +
                            ", ".join(valid_intents) + "."},
                {"role": "user", "content": question},
            ]
        )

        predicted_intent = response.choices[0].message.content.strip()

        if predicted_intent in valid_intents:
            # Adjust the path to match the required format
            pdf_file_path = os.path.join("Files", predicted_intent, predicted_intent + ".pdf")
            if os.path.exists(pdf_file_path):
                return pdf_file_path
            else:
                print(f"File not found: {pdf_file_path}")
                break  # Exit the loop if file is not found
        attempts += 1

    # Default to a general PDF if the specific one is not found
    return os.path.join("Files", "Main", "Main.pdf")


# Initialize chat history in session state if it doesn't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []

def read_valid_intents(file_name):
    with open(file_name, 'r') as file:
        lines = file.read().splitlines()
    return [line.strip() for line in lines if line.strip()]

valid_intents_file = "valid_intents.txt"  # Assuming this is the name of your text file
valid_intents = read_valid_intents(valid_intents_file)


def handle_example_question(question):
    # Add user input to the session state
    st.session_state.messages.append({"role": "user", "content": question})

    # Generate a response
    generate_response(question)

# Streamlit part of the code
st.title("IPRO-Demo")
cols = st.columns(3)
for i, example_question in enumerate(example_questions):
    with cols[i]:
        if st.button(example_question, key=f"example_question_{i}"):
            handle_example_question(example_question)
st.info(
    "Please note: The responses provided by this chatbot are based on AI and may not always be 100% accurate or "
    "reliable. In case of uncertainties or important inquiries, we recommend contacting the responsible office "
    "directly.")

# React to user input
user_input = st.chat_input("Frage Hier：")
if user_input:
    # Check if the user input was already processed
    if ('last_input' not in st.session_state or
            st.session_state.last_input != user_input):
        # Store the current user input to prevent processing it again
        st.session_state.last_input = user_input

        # Add user input to the session state
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate a response
        response = generate_response(user_input)

# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Add a button to clear chat history
if st.button("Clear Chat History"):
    # Clear chat history and last input to reset the chat
    st.session_state.messages = []
    if 'last_input' in st.session_state:
        del st.session_state.last_input
