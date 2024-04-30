from text_highlighter import text_highlighter
import streamlit as st

# Basic usage
result = text_highlighter(
    text="John Doe is the founder of MyComp Inc. and lives in New York with his wife Jane Doe.",
    labels=[("", "#d7ecf1"), ],
    # Optionally you can specify pre-existing annotations:
    annotations=[
        {"start": 0, "end": 8, "tag": ""},
        {"start": 27, "end": 38, "tag": ""},
        {"start": 75, "end": 83, "tag": ""},
    ],
)

# Show the results (in XML format)
st.code(result.to_xml())

# Show the results (as a list)
st.write(result)