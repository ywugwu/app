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
        """I want you to show the important words and their importance score (from 0 to 10) for every word in the output text with respect to how much they influenced the outputted word in a word level. Namely, I want you to show, for every word in the output text, what words in the input text contribute to their presence the most and what is their importance score. You don't need to present the words with a 0 importance score. You can concatenate continuous words into a phrase if their important words and importance scores are the same.

You should format your answer using JSON syntax. You should make sure concatenating all keys in the JSON file can form the original output text.

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


if __name__ == "__main__":
    example_input = """
    Explain the concept of a group in abstract algebra.
"""
    example_output = "In abstract algebra, a group is a set equipped with a binary operation that satisfies four fundamental properties: closure, associativity, the existence of an identity element, and the existence of inverse elements for every element in the set. This structure allows abstract groups to model the symmetrical aspects of mathematical systems."
    prompt = direct_prompt(example_input, example_output)
    client = Client()
    prased_data = client.get_response(prompt)
    print(prased_data)
