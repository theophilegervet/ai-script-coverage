import json
import os

import fire
from openai import OpenAI


def generate_coverage(
    input_script_path: str,
    output_coverage_path: str,
    example_coverage_path: str = "coverages_human/detox_coverage.json",
):
    with open("guidelines/generate.txt") as f:
        guidelines = f.read()
    with open(example_coverage_path) as f:
        example_coverage = json.dumps(json.load(f))
    with open(input_script_path) as f:
        input_script = f.read()

    prompt = (
        "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to perform a script coverage according to the following guidelines.\n\n"
        + guidelines
        + "\n\nEXAMPLE SCRIPT COVERAGE\n\n"
        + example_coverage
        + "\n\nWrite a coverage for the following script.\n\nINPUT SCRIPT\n\n###\n"
        + input_script
        + "\n###"
    )

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant designed to output JSON.",
        },
        {"role": "user", "content": prompt},
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = json.loads(
        client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=messages,
        )
        .choices[0]
        .message.content
    )

    with open(output_coverage_path, "w") as f:
        json.dump(response, f, indent=4)

    print(response)


if __name__ == "__main__":
    """
    python generate_coverage.py \
        --input_script_path scripts/being_silver.txt \
        --output_coverage_path coverages_generated/being_silver_coverage.json
    """
    fire.Fire(generate_coverage)
