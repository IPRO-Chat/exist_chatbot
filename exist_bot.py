import os
import PyPDF2
import openai
import streamlit as st
import random
import hashlib

base = "light"

st.set_page_config(page_title="IPRO-Chatbot", page_icon="IPRO-CHAT.png", layout="wide")
all_example_questions = [
    "Wie kann ich einen Raum finden?",
    "Wie kann ich den Professor kontaktieren?",
    "Wie bezahle ich den Semesterbeitrag?",
    "Wo finde ich Informationen zu Prüfungsterminen?",
    "Wie kann ich mich für Kurse anmelden?",
    "Was sind die Bibliotheksöffnungszeiten?",
    "Wo finde ich Studienberatung?",
    "Wie stelle ich einen BAföG-Antrag?",
    "Wie funktioniert das WLAN auf dem Campus?"
]

st.markdown(
    """
    <style>
        .stChatFloatingInputContainer {
            bottom: -50px;
            background-color: rgba(0, 0, 0, 0)
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# selected2 = option_menu(None, ["Home", "Upload", "Tasks", 'Settings'],
#     icons=['house', 'cloud-upload', "list-task", 'gear'],
#     menu_icon="cast", default_index=0, orientation="horizontal")
# selected2

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

html_code = """
    <div style="position: relative; center: 100px; left: 0px; z-index: 9999;display: flex; align-items: center; background-color: #CCE1E9; ">
        <img src="https://www.hs-emden-leer.de/typo3conf/ext/fr_sitepackage_hs_emden_leer/Resources/Public/Images/logo-header-normal.svg" alt="Logo" height="50px">
        <span style="margin-left: 10px; font-size: 30px; color: black;">  ·  IPRO-Chat</span>
    </div>
"""

st.markdown(html_code, unsafe_allow_html=True)


def generate_key(question, index):
    """ Generate a unique key for each button based on the question text. """
    hash_object = hashlib.md5(question.encode())
    return hash_object.hexdigest() + str(index)

def add_bg():
    st.markdown(
        f"""
         <style>
         .stApp {{
             background-color: #CCE1E9;
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
        unsafe_allow_html=True
    )


add_bg()


def set_info_style():
    style = """
        <style>
            .stAlert {
                background-color: #9CC4CC;  
                border-radius: 15px;  
            }
        </style>
        """
    st.markdown(style, unsafe_allow_html=True)


# 应用自定义样式
set_info_style()


# Function to set the background color for areas not covered by the image
def set_background_color(color):
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {color};
    }}
    </style>
    """, unsafe_allow_html=True)


def set_button_style():
    button_style = """
        <style>
            .stButton > button {
                color: white;  
                background-color: #003B5F; 
                border: none;  
                padding: 10px 20px; 
                border-radius: 30px; 
                font-size: 16px;  
            }
            .stButton > button:hover {
                color: white;
                background-color: #9CC4CC;  
            }
            .stButton > button:active {
                color: #3E5565;  
                background-color: #9CC4CC;  、
            }
        </style>
        """
    st.markdown(button_style, unsafe_allow_html=True)


set_button_style()


# Not Working
def set_chat_message_style():
    style = """
        <style>
            .chat-message.user:before {
                content: '';
                background-image: url('User.jpeg');  /* user icon */
            }
            .chat-message.bot:before {
                content: '';
                background-image: url('Bot.jpeg');  /* Chatbot icon */
            }
        </style>
        """
    st.markdown(style, unsafe_allow_html=True)


# Set Style
set_chat_message_style()

# Initialize the OpenAI client with the API key
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

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
    # Read valid intents from the file
    valid_intents = read_valid_intents("valid_intents.txt")

    # Prepare the prompt for the GPT model
    prompt = ("Predict the intent of the question. The answer must be one of the following: " +
              ", ".join(valid_intents) + ".\nQuestion: " + question + "\nIntent:")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]
    )

    predicted_intent = response.choices[0].message.content.strip()

    # Print the predicted intent
    print(f"Predicted Intent: {predicted_intent}")

    if predicted_intent in valid_intents:
        pdf_file_path = os.path.join("Files", predicted_intent, predicted_intent + ".pdf")
        if os.path.exists(pdf_file_path):
            return pdf_file_path
        else:
            print(f"File not found: {pdf_file_path}")
    else:
        print("Predicted intent not in valid intents.")

    # Default to a general PDF if the specific one is not found or intent is not valid
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
# st.write(" Question? ")
# Randomly select three unique questions
if 'displayed_questions' not in st.session_state:
    st.session_state.displayed_questions = random.sample(all_example_questions, 3)

cols = st.columns(3)
for i, example_question in enumerate(st.session_state.displayed_questions):
    with cols[i]:
        if st.button(example_question, key=f"example_question_{i}"):
            handle_example_question(example_question)

st.info(
    "Die Antworten basieren auf AI und sind möglicherweise nicht zu "
    "100 % korrekt. Bei Fragen oder wichtigen Problemen wenden Sie sich bitte direkt an Student Service Center"
    "oder Prüfungsamt.")

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
