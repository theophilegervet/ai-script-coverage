import os

import fire
from openai import OpenAI


def evaluate_coverage(
    input_script_path: str,
    generated_coverage_path: str,
    human_coverage_path: str,
    output_comparison_path: str,
):
    with open("evaluate_guidelines.txt") as f:
        guidelines = f.read()

    with open(input_script_path) as f:
        input_script = f.read()

    with open(generated_coverage_path) as f:
        generated_coverage_path = f.read()

    with open(human_coverage_path) as f:
        human_coverage_path = f.read()

    prompt = (
        "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to review and grade a coverage with respect to the original script and a reference coverage according to the following guidelines.\n\n"
        + guidelines
        # + "\n\nREFERENCE SCRIPT\n\n###\n"
        # + input_script
        + "\n###\n\nREFERENCE COVERAGE\n\n###\n"
        + human_coverage_path
        + "\n###\n\nReview and grade the following coverage with respect to the script and reference coverage.\n\nINPUT COVERAGE\n\n###\n"
        + generated_coverage_path
        + "\n###"
    )
    messages = [
        {"role": "user", "content": prompt},
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = (
        client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )
        .choices[0]
        .message.content
    )

    with open(output_comparison_path, "w") as f:
        f.write(response)

    print(response)


if __name__ == "__main__":
    """
    python evaluate_coverage.py \
        --input_script_path scripts_txt/being_silver.txt \
        --generated_coverage_path coverages_generated_txt/being_silver_coverage.txt \
        --human_coverage_path coverages_human_txt/being_silver_coverage.txt \
        --output_comparison_path coverages_review_txt/being_silver_review.txt
    """
    fire.Fire(evaluate_coverage)
