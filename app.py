import streamlit as st
import json
import os
from prompt import *
st.set_page_config(layout="wide")
CACHE = True


from collections import defaultdict

def approximate_button_width(word, avg_char_width=9, padding=0):
    """
    Estimates the pixel width of a button based on its label length.
    avg_char_width: Average pixel width of one character of text.
    padding: Total horizontal padding in pixels.
    """
    return len(word) * avg_char_width + padding

def approximate_button_width(text, char_width, pad):
    # This is a simplified function to approximate button width.
    return len(text) * char_width + 2 * pad

def layout_buttons_dynamic(htmls, max_row_width=800, avg_char_width=15, padding=12):
    """
    Dynamically layout buttons based on their estimated width.
    max_row_width: Maximum width in pixels available for one row.
    """
    outputs = list(htmls.items())
    row_buffers = []
    current_row = []
    current_width = 0

    # Iterate through each item and allocate to rows based on estimated widths
    for idx, (output_word, _) in outputs:
        button_width = approximate_button_width(output_word, avg_char_width, padding)
        if current_width + button_width > max_row_width:
            if current_row:
                row_buffers.append(current_row)
            current_row = [(idx, output_word, button_width)]
            current_width = button_width
        else:
            current_row.append((idx, output_word, button_width))
            current_width += button_width
    
    if current_row:  # Append the last row if any
        row_buffers.append(current_row)

    # Render each row with appropriate columns
    for row in row_buffers:
        widths = [button_width  for _, _, button_width in row]
        cols = st.columns(widths)  # Create columns with proportional widths
        for col, (idx, output_word, _) in zip(cols, row):
            col.button(label=str(output_word).replace('.','\.'), use_container_width=True, key=f"btn_{idx}", on_click=lambda idx=idx: st.session_state.update({'selected_output': idx}))
        # use st.write to check the column width information
        # st.write(f'{widths}')
        # st.write(f'{[output_word for _, output_word, _ in row]}')

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
        os.mkdir("cache") if not os.path.exists("cache") else None
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


def handle_click(word, nested_responses):
    return {key: val.get(word, 0) for key, val in nested_responses.items() if word in key}

# App title
st.title('A Demo for GPT\'s Introspection')

# Initialize session state
if 'show_prompt' not in st.session_state:
    st.session_state['show_prompt'] = False

# Input fields
api_key = st.text_input("OpenAI API key", placeholder="Your API key from https://platform.openai.com/api-keys")
if st.button('Confirm API key'):
    st.write("Confirmed API key")
input1 = st.text_area("Input", placeholder="Example: I want you to help me review an interaction I had with a patient .......")
input2 = st.text_area("Output", placeholder="Example: The diagnosis is not stated, but the differential diagnoses of acute pain and essential hypertension are consistent with the elevated blood pressure and the patient's complaint of pain.")

# input1 = "Explain the concept of a group in abstract algebra."
# input2 = """In abstract algebra, a group is a set equipped with a binary operation that satisfies four fundamental properties: \n
#             closure, associativity, the existence of an identity element, and the existence of inverse elements for every element in the set. \n
#             This structure allows abstract groups to model the symmetrical aspects of mathematical systems.\n"""

if st.button('Get Response') or st.session_state.get('response_fetched', False):
    if not st.session_state.get('response_fetched', False):
        client = Client(api_key)
        status_message = st.empty()
        status_message.write("Getting response from GPT...")
        responses = chatbot_response(input1, input2, client)
        introspect_results = parse_json(responses, input1, input2)

        # Cache the HTML representations
        htmls = {}
        for i, (output_word, input_information) in enumerate(introspect_results):
            htmls[i] = (output_word, generate_html_for_wordlevel_importance(input_information))
        
        # Store that response has been fetched
        st.session_state['response_fetched'] = True
        st.session_state['htmls'] = htmls

    # Use cached HTMLs if available
    htmls = st.session_state.get('htmls', {})
    col1, col2 = st.columns([1, 2])
    with col2:
        st.write(f"**Output Text:**")
        layout_buttons_dynamic(htmls)
    
    # Display HTML content based on selected output
    with col1:
        if 'selected_output' in st.session_state:
            selected_output = st.session_state['selected_output']
            _, html_content = htmls[selected_output]
            st.write(f"**Word-Level Importance for: {htmls[selected_output][0]}**")
            st.markdown(html_content, unsafe_allow_html=True)
        else:
            default_input_information = {word: 0 for word in input1.split()}
            default_html = generate_html_for_wordlevel_importance(default_input_information)
            st.write(f"**Word-Level Importance for: {introspect_results[0][0]}**")
            st.markdown(default_html, unsafe_allow_html=True)


    
# Button to toggle prompt visibility
if st.button('View/Hide The Introspection Prompt Format'):
    st.session_state['show_prompt'] = not st.session_state['show_prompt']

# Display the prompt conditionally
if st.session_state['show_prompt']:
    st.write(direct_prompt(input1,input2))
