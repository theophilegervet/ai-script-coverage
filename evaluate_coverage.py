import json
import os

import fire
from openai import OpenAI


def evaluate_section(
    client,
    human_coverage_section,
    generated_coverage_section,
    example_review_section,
    guidelines_section,
):
    prompt = (
        "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to review and grade a coverage with respect to the original script and a reference coverage according to the following guidelines.\n\n"
        + guidelines_section
        + "\n\nEXAMPLE COVERAGE REVIEW\n\n"
        + json.dumps(example_review_section)
        + "\n###\n\nREFERENCE COVERAGE\n\n###\n"
        + json.dumps(human_coverage_section)
        + "\n###\n\nReview and grade the following coverage with respect to the reference coverage.\n\nINPUT COVERAGE\n\n###\n"
        + json.dumps(generated_coverage_section)
        + "\n###"
    )
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant designed to output JSON.",
        },
        {"role": "user", "content": prompt},
    ]
    return json.loads(
        client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=messages,
        )
        .choices[0]
        .message.content
    )


def evaluate_coverage(
    generated_coverage_path: str,
    human_coverage_path: str,
    output_review_path: str,
    example_review_path: str = "reviews_human/detox_review.json",
):
    with open(generated_coverage_path) as f:
        generated_coverage = json.load(f)
    with open(human_coverage_path) as f:
        human_coverage = json.load(f)
    with open(example_review_path) as f:
        example_review = json.load(f)

    section_to_guidelines = {
        "Metadata": "guidelines/evaluate_metadata.txt",
        "Summary": {
            "Logline": "guidelines/evaluate_summary_logline.txt",
            "Synopsis": "guidelines/evaluate_summary_synopsis.txt",
            "Characters": "guidelines/evaluate_summary_characters.txt",
        },
        "Evaluation": {
            "Concept": "guidelines/evaluate_evaluation_concept.txt",
            "Plot / Structure": "guidelines/evaluate_evaluation_plot.txt",
            "Writing / Dialogues": "guidelines/evaluate_evaluation_dialogues.txt",
            "Characters": "guidelines/evaluate_evaluation_characters.txt",
            "Commerciality": "guidelines/evaluate_evaluation_commerciality.txt",
            "Recommendation": "guidelines/evaluate_evaluation_recommendation.txt",
        },
    }

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    review = {}

    def recursion(
        human_coverage,
        generated_coverage,
        example_review,
        review,
        section_to_guidelines,
    ):
        for k, v in section_to_guidelines.items():
            if type(v) == str:
                with open(v) as f:
                    guidelines = f.read()
                review[k] = evaluate_section(
                    client,
                    human_coverage[k],
                    generated_coverage[k],
                    example_review[k],
                    guidelines,
                )
            else:
                review[k] = {}
                recursion(
                    human_coverage[k],
                    generated_coverage[k],
                    example_review[k],
                    review[k],
                    section_to_guidelines[k],
                )

    recursion(
        human_coverage,
        generated_coverage,
        example_review,
        review,
        section_to_guidelines,
    )

    metadata_grade = review["Metadata"]["Quantitative evaluation"]["Grade"]
    summary_grade = sum(
        review["Summary"][k]["Quantitative evaluation"]["Grade"]
        for k in section_to_guidelines["Summary"].keys()
    )
    evaluation_grade = sum(
        review["Evaluation"][k]["Quantitative evaluation"]["Grade"]
        for k in section_to_guidelines["Evaluation"].keys()
    )
    review["Quantitative evaluation"] = {
        "Metadata": f"{metadata_grade} / 3",
        "Summary": f"{summary_grade} / 11",
        "Evaluation": f"{evaluation_grade} / 12",
        "Total": f"{(metadata_grade + summary_grade + evaluation_grade)} / 26",
    }

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
