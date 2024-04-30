import streamlit as st
import json
import os
from prompt import *
from text_highlighter import text_highlighter

st.set_page_config(layout="wide")
CACHE = False

from collections import defaultdict


def parse_json(response, input_text, output_text):
    input_words = input_text.split()
    introspect_results = []
    # Process each output word
    for output_phrase, input_info in response.items():
        input_words_scores = []
        tmp_dict = defaultdict(int)
        for phrase, score in input_info.items():
            for word in phrase.split():
                tmp_dict[word] = score
        for word in input_words:
            input_words_scores.append((word, tmp_dict[word]))
        for output_word in output_phrase.split():
            introspect_results.append((output_word, input_words_scores))
    return introspect_results

def parse_json_two_stage(response, input_text, output_text):
    pseudo_response = {}
    i = 0
    for output_phrase, input_info in response.items():
        start = output_text.find(output_phrase)
        end = start + len(output_phrase)
        # map output_text[i:start] to {}
        pseudo_response[output_text[i:start]] = {}
        # map output_text[start:end] to input_info
        pseudo_response[output_phrase] = input_info
        i = end
    introspect_results = parse_json(pseudo_response, input_text, output_text)
    return introspect_results

def position_to_word_score_cache(introspect_results):
    ans = {}
    start = 0
    for output_word, input_information in introspect_results:
        n = len(output_word)
        for i in range(start, start + n):
            ans[i] = {
                'word': output_word,
                'input_information': input_information,
                'start': i == start,
            }
        ans[start + n] = {
            'word': ' ',
            'input_information': [],
            'start': False,
        }
        start += n + 1
    return ans

def chatbot_response(input1, input2, client):
    if CACHE:
        if not os.path.exists("cache"):
            os.mkdir("cache")
        files = os.listdir("cache")
        response = json.loads(open(f"cache/{files[-1]}").read())
    else:
        response = client.get_response(direct_prompt(input1, input2))
    return response

def chatty_response(input1, input2, client):
    if CACHE:
        if not os.path.exists("cache/chatty"):
            os.mkdir("cache/chatty")
        files = os.listdir("cache/chatty")
        response = json.loads(open(f"cache/chatty/{files[-1]}").read())
    else:
        response = client.get_response(chatty_prompt(input1, input2), cache_dir="cache/chatty")
    return response

def two_stage_response(input1, input2, client):
    if CACHE:
        if not os.path.exists("cache/two_stage"):
            os.mkdir("cache/two_stage")
        files = os.listdir("cache/two_stage")
        response = json.loads(open(f"cache/two_stage/{files[-1]}").read())
    else:
        response = client.get_response(two_stage_prompt(input1, input2), cache_dir="cache/two_stage")
    return response

def number_to_color(n):
    white = (255, 255, 255)
    pink = (255, 192, 203)
    n = max(0, min(10, n))
    r = int(white[0] + (pink[0] - white[0]) * (n / 10))
    g = int(white[1] + (pink[1] - white[1]) * (n / 10))
    b = int(white[2] + (pink[2] - white[2]) * (n / 10))
    return f"rgb({r}, {g}, {b})"


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

def generate_html_for_multiple_wordlevel_importance(input_informations):
    merged_input_informations = defaultdict(int)
    for input_information in input_informations:
        for input_word, importance_score in input_information:
            merged_input_informations[input_word] = max(merged_input_informations[input_word], importance_score)
    response_html = ""
    for input_word, importance_score in merged_input_informations.items():
        color = number_to_color(importance_score)
        response_html += f"<span style='background-color:{color};'>{input_word}</span> "
    return response_html

def handle_click(word, nested_responses):
    return {
        key: val.get(word, 0) for key, val in nested_responses.items() if word in key
    }


# App title
st.title("A Demo for GPT's Introspection")

# Initialize session state
if "show_prompt" not in st.session_state:
    st.session_state["show_prompt"] = False
if "text" not in st.session_state:
    st.session_state["text"] = False
if "buttons" not in st.session_state:
    st.session_state["buttons"] = False
if "cat_output" not in st.session_state:
    st.session_state["cat_output"] = ""
# Input fields
api_key = st.text_input(
    "OpenAI API key",
    placeholder="Your API key from https://platform.openai.com/api-keys",
)
if st.button("Confirm API key"):
    st.write("Confirmed API key")
input1 = st.text_area(
    "Input",
    placeholder="Example: I want you to help me review an interaction I had with a patient .......",
)
input2 = st.text_area(
    "Output",
    placeholder="Example: The diagnosis is not stated, but the differential diagnoses of acute pain and essential hypertension are consistent with the elevated blood pressure and the patient's complaint of pain.",
)

if CACHE:
    from trigger import *
    input1 = MED_INPUT
    input2 = MED_OUTPUT

if st.button("Get Response") or st.session_state.get("response_fetched", False):
    if not st.session_state.get("response_fetched", False):
        client = Client(api_key)
        
        status_message = st.empty()
        status_message.write("Getting response from GPT... (0/3)")
        responses = chatbot_response(input1, input2, client)
        introspect_results = parse_json(responses, input1, input2)
        # Cache the HTML representations
        cat_output = ' '.join([output_word for output_word, _ in introspect_results])
        
        # Store that response has been fetched
        st.session_state["response_fetched"] = True
        st.session_state["position_cache"] = position_to_word_score_cache(introspect_results)
        st.session_state["cat_output"] = cat_output
        
        # prompt for chatty
        status_message.write("Getting response from GPT... (1/3)")
        chatty_responses = chatty_response(input1, input2, client)
        chatty_introspect_results = parse_json(chatty_responses, input1, input2)
        st.session_state["chatty_position_cache"] = position_to_word_score_cache(chatty_introspect_results)
        # prompt for two stage
        status_message.write("Getting response from GPT... (2/3)")
        two_stage_responses = two_stage_response(input1, input2, client)
        two_stage_introspect_results = parse_json_two_stage(two_stage_responses['importance analysis'], input1, input2)
        st.write(f"Important words in the output: {two_stage_responses['important words']}")
        st.session_state["two_stage_position_cache"] = position_to_word_score_cache(two_stage_introspect_results)
        #
        status_message.write("Response fetched!")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        st.write("**Select Words Here:**")
        trigger_results = text_highlighter(
            text=st.session_state["cat_output"],
            labels=[("", "#d7ecf1")],
            show_label_selector=False,
        )
        print(trigger_results)
        # Store multiple selections
        st.session_state['selected_texts'] = trigger_results

    # Display HTML content based on selected output
    with col2:
        st.write("**Show Visualization Here (Direct Prompt):**")
        input_infos = []
        selected_words = []
        for select_text in st.session_state['selected_texts']:
            start = select_text['start']
            end = select_text['end']
            for i in range(start, end):
                if st.session_state['position_cache'][i]['start']:
                    input_infos.append(st.session_state['position_cache'][i]['input_information'])
                    selected_words.append(st.session_state['position_cache'][i]['word'])
        merged_input_information = generate_html_for_multiple_wordlevel_importance(input_infos)
        st.markdown(merged_input_information, unsafe_allow_html=True)

    with col3:
        st.write("**Chatty Prompt:**")
        input_infos = []
        for select_text in st.session_state['selected_texts']:
            start = select_text['start']
            end = select_text['end']
            for i in range(start, end):
                if st.session_state['chatty_position_cache'][i]['start']:
                    input_infos.append(st.session_state['chatty_position_cache'][i]['input_information'])
        merged_input_information = generate_html_for_multiple_wordlevel_importance(input_infos)
        st.markdown(merged_input_information, unsafe_allow_html=True)
        
    with col4:
        st.write("**\"First ummarize, then introspect\" Prompt:**")
        input_infos = []
        for select_text in st.session_state['selected_texts']:
            start = select_text['start']
            end = select_text['end']
            for i in range(start, end):
                if st.session_state['two_stage_position_cache'][i]['start']:
                    input_infos.append(st.session_state['two_stage_position_cache'][i]['input_information'])
        merged_input_information = generate_html_for_multiple_wordlevel_importance(input_infos)
        st.markdown(merged_input_information, unsafe_allow_html=True)
        
        
# Button to toggle prompt visibility
if st.button("Show the Used Prompts"):
    st.session_state["show_prompt"] = not st.session_state["show_prompt"]

# Display the prompt conditionally
if st.session_state["show_prompt"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.write("**Direct Prompt:**")
        st.write(direct_prompt(input1, input2))
    with col2:
        st.write("**Chatty Prompt:**")
        st.write(chatty_prompt(input1, input2))
    with col3:
        st.write("**Two Stage Prompt:**")
        st.write(two_stage_prompt(input1, input2))
