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
        "Give importance scores (from 0 to 10) for each word in the input text (you don't need to include the words in the output text) with respect to how much they contribute the output. You should format your answer using JSON syntax. "
        "You need to indicate every newline symbol by using <br>. "
        "An example format of your response is:\n```\n"
        """
{"Explain": 0,"the": 5,"concept": 6,"of": 5,"a": 10,"group": 10,"in": 7,"abstract": 10,"algebra": 10}\n```\n"""
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
