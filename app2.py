import streamlit as st
import json
import os
from prompt import *

CACHE = True

from collections import defaultdict

def parse_json(response, input_text, output_text):
    # response format: {"phrase": {"phrase": score}}
    # Split the output text into words
    input_words = input_text.split()
    # Initialize the main tuple container
    introspect_results = []
    
    # Process each output word
    for output_phrase, input_info in response.items():
        input_words_scores = []
        tmp_dict = defaultdict(int)
        # Search through the JSON for matches and their scores
        for phrase,score in input_info.items():
            for word in phrase.split():
                tmp_dict[word] = score
        for word in input_words:
            input_words_scores.append((word, tmp_dict[word]))
        for output_word in output_phrase.split():
            introspect_results.append((output_word, input_words_scores))

    return introspect_results


def chatbot_response(input1, input2, client):
    if CACHE:
        files = os.listdir("cache")
        response = json.loads(open(f"cache/{files[-1]}").read())
    else:
        response = client.get_response(direct_prompt(input1, input2))
    return response

def number_to_color(n):
    white = (255, 255, 255)
    pink = (255, 192, 203)
    n = max(0, min(10, n))
    r = int(white[0] + (pink[0] - white[0]) * (n / 10))
    g = int(white[1] + (pink[1] - white[1]) * (n / 10))
    b = int(white[2] + (pink[2] - white[2]) * (n / 10))
    return f'rgb({r}, {g}, {b})'

def generate_html_for_wordlevel_importance(input_information):
    # Initialize the HTML content string
    response_html = ""
    # Iterate over each output word and its associated input word scores
    for input_word, importance_score in input_information:
        # Calculate the maximum score for the output word from its associated input words
        
        # Get the color corresponding to the maximum score
        color = number_to_color(importance_score)
        # Append the output word formatted with the background color
        response_html += f"<span style='background-color:{color};'>{input_word}</span> "
    
    return response_html

# Function to generate buttons for output words
def generate_output_buttons(htmls):
    # Calculate the number of buttons that fit into a single row based on button width
    num_buttons = len(htmls)
    button_width = 100  # Define the width you want for your buttons
    buttons_per_row = st.session_state.get("width", 1000) // button_width
    
    # Create rows of buttons
    for i in range(0, num_buttons, buttons_per_row):
        row_buttons = htmls[i:i+buttons_per_row]
        cols = st.beta_columns(buttons_per_row)
        for col, button_info in zip(cols, row_buttons):
            idx, (output_word, _) = button_info
            with col:
                if st.button(output_word, key=f"btn_{idx}"):
                    st.session_state['selected_output'] = idx
                    
def handle_click(word, nested_responses):
    return {key: val.get(word, 0) for key, val in nested_responses.items() if word in key}

# Initialize session state for fetched response and selected output
if 'response_fetched' not in st.session_state:
    st.session_state['response_fetched'] = False
if 'selected_output' not in st.session_state:
    st.session_state['selected_output'] = None

# Input fields
api_key = st.text_input("OpenAI API key", placeholder="Your API key from https://platform.openai.com/api-keys")
input1 = st.text_area("Input", placeholder="Example: I want you to help me review an interaction I had with a patient .......")
input2 = st.text_area("Output", placeholder="Example: The diagnosis is not stated, but the differential diagnoses of acute pain and essential hypertension are consistent with the elevated blood pressure and the patient's complaint of pain.")


input1 = "Explain the concept of a group in abstract algebra."
input2 = "In abstract algebra, a group is a set equipped with a binary operation that satisfies four fundamental properties: closure, associativity, the existence of an identity element, and the existence of inverse elements for every element in the set. This structure allows abstract groups to model the symmetrical aspects of mathematical systems."

# Button to fetch or display the response
if st.button('Get Response'):
    st.session_state['response_fetched'] = True
    client = Client(api_key)
    status_message = st.empty()
    status_message.write("Getting response from GPT...")
    responses = chatbot_response(input1, input2, client)
    introspect_results = parse_json(responses, input1, input2)
    status_message.empty()

    # Cache the HTML representations
    htmls = {}
    for i, (output_word, input_information) in enumerate(introspect_results):
        htmls[i] = (output_word, generate_html_for_wordlevel_importance(input_information))
    st.session_state['htmls'] = htmls

    
# Check if response has been fetched and display buttons
if st.session_state.get('response_fetched', False):
    generate_output_buttons(st.session_state['htmls'])

    # Display HTML content based on selected output
    if 'selected_output' in st.session_state:
        selected_output = st.session_state['selected_output']
        _, html_content = st.session_state['htmls'][selected_output]
        st.write(f"**Word-Level Importance for: {st.session_state['htmls'][selected_output][0]}**")
        st.markdown(html_content, unsafe_allow_html=True)
        
# Display the output words as horizontally scrollable buttons
if st.session_state['response_fetched']:
    with st.container():
        st.write("**Output Text:**")
        for i, (output_word, _) in st.session_state['htmls'].items():
            st.button(output_word, key=f"output_btn_{i}", on_click=lambda i=i: st.session_state.update({'selected_output': i}))
        
    # Display HTML content based on selected output
    if st.session_state['selected_output'] is not None:
        selected_output = st.session_state['selected_output']
        _, html_content = st.session_state['htmls'][selected_output]
        st.write(f"**Word-Level Importance for: {st.session_state['htmls'][selected_output][0]}**")
        st.markdown(html_content, unsafe_allow_html=True)

# Button to toggle prompt visibility
if st.button('View/Hide The Introspection Prompt Format'):
    st.session_state['show_prompt'] = not st.session_state['show_prompt']

# Display the prompt conditionally
if st.session_state.get('show_prompt', False):
    st.write(direct_prompt("INPUT","OUTPUT"))
    
    