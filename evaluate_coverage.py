import json
import os
import pprint

import fire
from openai import OpenAI


def evaluate_coverage(
    generated_coverage_path: str,
    human_coverage_path: str,
    output_review_path: str,
    example_review_path: str = "reviews_human/detox_review.json",
):
    with open("guidelines/evaluate_metadata.txt") as f:
        evaluate_metadata_guidelines = f.read()
    with open("guidelines/evaluate_summary.txt") as f:
        evaluate_summary_guidelines = f.read()
    with open("guidelines/evaluate_evaluation.txt") as f:
        evaluate_evaluation_guidelines = f.read()

    with open(generated_coverage_path) as f:
        generated_coverage = json.load(f)

    with open(human_coverage_path) as f:
        human_coverage = json.load(f)

    with open(example_review_path) as f:
        example_review = json.load(f)

    section_to_guidelines = {
        "Metadata": evaluate_metadata_guidelines,
        "Summary": evaluate_summary_guidelines,
        "Evaluation": evaluate_evaluation_guidelines,
    }

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    review = {}

    for section, guidelines in section_to_guidelines.items():
        prompt = (
            "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to review and grade a coverage with respect to the original script and a reference coverage according to the following guidelines.\n\n"
            + guidelines
            + "\n\nEXAMPLE COVERAGE REVIEW\n\n"
            + json.dumps(example_review[section])
            + "\n###\n\nREFERENCE COVERAGE\n\n###\n"
            + json.dumps(human_coverage[section])
            + "\n###\n\nReview and grade the following coverage with respect to the reference coverage.\n\nINPUT COVERAGE\n\n###\n"
            + json.dumps(generated_coverage[section])
            + "\n###"
        )
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        response = json.loads(
            client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=messages,
            )
            .choices[0]
            .message.content
        )
        review[section] = response

    with open(output_review_path, "w") as f:
        json.dump(review, f, indent=4)

    print(review)


if __name__ == "__main__":
    """
    python evaluate_coverage.py \
        --generated_coverage_path coverages_generated/being_silver_coverage.json \
        --human_coverage_path coverages_human/being_silver_coverage.json \
        --output_review_path reviews_generated/being_silver_review.json
    """
    fire.Fire(evaluate_coverage)
