import textwrap
from openai import OpenAI
import json
import time
import os


class Client:
    def __init__(self, api_key) -> None:
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def get_response(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        parsed_data = json.loads(content)
        # use current time stamp to cache the response
        timeStamp = time.time()
        os.makedirs("cache", exist_ok=True)
        with open(f"cache/response_{timeStamp}.json", "w") as f:
            json.dump(parsed_data, f, indent=4)

        return parsed_data


def direct_prompt(input, output):
    DIRECT_TEMPLATE = (
        f"Given the input text:\n```\n"
        f"{input}\n```\nand the following output text:\n```\n{output}\n```\n"
        """I want you to analyze and report the contribution of each word or phrase in the input text to each word or phrase in the output text. Assign an importance score from 0 to 10 for each contribution, omitting contributions with scores with zero impact.

Use JSON format for your output, ensuring each entry clearly lists output words, their corresponding influential input words or phrases, and the importance scores. 
You should ensure concatenating all keys in the JSON file can form the original output text.

An example is shown below:
Input text: 
```
    Explain the concept of a group in abstract algebra.
```
Output text:
```
In abstract algebra, a group is a set equipped with a binary operation that satisfies four fundamental properties: closure, associativity, the existence of an identity element, and the existence of inverse elements for every element in the set. This structure allows abstract groups to model the symmetrical aspects of mathematical systems.
```
Answer:
```
{
  "In abstract algebra,": {"Explain": 3, "abstract algebra": 10},
  "a group is": {"group": 10},
  "a set equipped with a binary operation": {"concept": 8},
  "that satisfies four fundamental properties:": {"concept": 7},
  "closure,": {"group": 5},
  "associativity,": {"group": 5},
  "the existence of an identity element,": {"group": 5},
  "and the existence of inverse elements": {"group": 5},
  "for every element in the set.": {"group": 5},
  "This structure allows abstract groups": {"abstract algebra": 10},
  "to model the symmetrical aspects": {"concept": 6},
  "of mathematical systems.": {"abstract algebra": 9}
}
```"""
    )
    return DIRECT_TEMPLATE


def conversational_prompt(input, output):
    CONVERSATIONAL_TEMPLATE = (
        f"Given the input text:\n```\n"
        f"{input}\n```\nand the following output text:\n```\n{output}\n```\n"
        """I'm currently exploring how different parts of input text influence corresponding segments of output text in a project. I'd appreciate some guidance on this. Could you analyze and score the impact of each word or phrase in the input text on the output text, assigning importance scores from 0 to 10? Please exclude any contributions that have no impact.

Additionally, could you structure this analysis in JSON format? The keys in the JSON should align in such a way that, when concatenated, they reconstruct the full original output text. This structure will help in understanding the data flow and contribution more clearly.

Thank you for your assistance!"""
    )
    return CONVERSATIONAL_TEMPLATE

if __name__ == "__main__":
    example_input = """
    Explain the concept of a group in abstract algebra.
"""
    example_output = "In abstract algebra, a group is a set equipped with a binary operation that satisfies four fundamental properties: closure, associativity, the existence of an identity element, and the existence of inverse elements for every element in the set. This structure allows abstract groups to model the symmetrical aspects of mathematical systems."
    prompt = direct_prompt(example_input, example_output)
    client = Client()
    prased_data = client.get_response(prompt)
    print(prased_data)
