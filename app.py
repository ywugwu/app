import streamlit as st
from prompt import *
# from annotated_text import annotated_text

CACHE = False

def chatbot_response(input1, input2,client):
    # This function simulates your chatbot. Replace this with your actual chatbot logic.
    # Currently, it just concatenates the inputs with a simple response for demonstration.
    if CACHE:
        files = os.listdir("cache")
        response = json.loads(open(f"cache/{files[-1]}").read())
    else:
        response = client.get_response(direct_prompt(input1, input2))
    return response
    

def number_to_color(n):
    # Define the RGB values for white and pink
    white = (255, 255, 255)
    pink = (255, 192, 203)

    # Ensure n is within the range of 0 to 10
    n = max(0, min(10, n))

    # Linearly interpolate between white and pink
    r = int(white[0] + (pink[0] - white[0]) * (n / 10))
    g = int(white[1] + (pink[1] - white[1]) * (n / 10))
    b = int(white[2] + (pink[2] - white[2]) * (n / 10))

    return f'rgb({r}, {g}, {b})'

def generate_html(responses, importance_scores):
    # response is a list of words, importance_scores is a list of scores
    # format the response with the importance scores: ("word", "", color(CSS-valid string))
    response_html = ""
    for word, score in zip(responses, importance_scores):
        if word == '\n':
            response_html += '<br>'
        else:
            color = number_to_color(score)
            response_html += f"<span style='background-color:{color};'>{word}</span> "
    return response_html


# Title of the app
st.title('A Demo for GPT\'s Introspection')

# Initialize session state
if 'show_prompt' not in st.session_state:
    st.session_state['show_prompt'] = False

# Creating two text input fields
api_key = st.text_input("OpenAI API key", placeholder="You API key from https://platform.openai.com/api-keys")

if st.button('Confirm API key'):
    st.write("Confirmed API key")
input1 = st.text_area("Input", placeholder="""Example: I want you to help me review an interaction I had with a patient .......
""")
input2 = st.text_area("Output", placeholder="""Example: 1. The diagnosis is not stated, but the differential diagnoses of acute pain and essential hypertension are consistent with the elevated blood pressure and the patient's complaint of pain.
""")


# Button to generate response
if st.button('Get Response'):
    # Getting the response from the chatbot function
    client = Client(api_key)
    status_message = st.empty()
    status_message.write("Getting response from GPT...")
    responses = chatbot_response(input1, input2, client)
    words = responses.keys()
    importance_scores = responses.values()
    response_html = generate_html(responses, importance_scores)
    # Display the response
    status_message.empty()
    st.markdown(response_html, unsafe_allow_html=True)
    

# Button to toggle prompt visibility
if st.button('View/Hide The Introspection Prompt Format'):
    st.session_state['show_prompt'] = not st.session_state['show_prompt']

# Display the prompt conditionally
if st.session_state['show_prompt']:
    st.write(direct_prompt("INPUT","OUTPUT"))
