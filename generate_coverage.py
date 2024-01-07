import copy
import json
import os

import fire
from openai import OpenAI
from tqdm import tqdm


def generate(client, prompt):
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


def split_file_into_chunks(file_path, num_chunks):
    with open(file_path, "r") as file:
        lines = file.readlines()

    total_lines = len(lines)
    lines_per_chunk = total_lines // num_chunks
    chunks = []

    for chunk in range(num_chunks):
        start = chunk * lines_per_chunk
        end = None if chunk == num_chunks - 1 else (chunk + 1) * lines_per_chunk
        chunk_lines = "".join(lines[start:end])
        chunks.append(chunk_lines)

    return chunks


def coverage_from_script_chunks(
    client, input_script_path, example_coverage, num_chunks, debug=True
):
    with open("guidelines/generate_from_script_chunk.txt") as f:
        guidelines = f.read()

    entries_to_keep = {
        "Metadata": ["Period", "Location"],
        "Summary": ["Synopsis", "Characters"],
        "Evaluation": ["Writing / Dialogues", "Characters"],
    }
    example_coverage = copy.deepcopy(example_coverage)
    for section, subsections_to_keep in entries_to_keep.items():
        example_coverage[section] = {
            k: v
            for k, v in example_coverage[section].items()
            if k in subsections_to_keep
        }

    script_chunks = split_file_into_chunks(input_script_path, num_chunks)

    coverage_chunks = []
    for script_chunk in tqdm(script_chunks, desc="Coverage from script chunks"):
        prompt = (
            "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to perform a script coverage according to the following guidelines.\n\n"
            + guidelines
            + "\n\nEXAMPLE SCRIPT COVERAGE\n\n"
            + json.dumps(example_coverage)
            + "\n\nWrite a coverage for the following chunk of script.\n\nINPUT SCRIPT CHUNK\n\n###\n"
            + script_chunk
            + "\n###"
        )
        coverage_chunks.append(generate(client, prompt))

    if debug:
        for i, chunk in enumerate(coverage_chunks):
            with open(f"chunk{i}.json", "w") as f:
                json.dump(chunk, f, indent=4)

    coverage = merge_coverage_chunks(client, coverage_chunks)
    return coverage


def merge_coverage_chunks(client, coverage_chunks):
    section_to_guidelines = {
        "Metadata": "guidelines/generate_merge_metadata.txt",
        "Summary": {
            "Synopsis": "guidelines/generate_merge_summary_synopsis.txt",
            "Characters": "guidelines/generate_merge_summary_characters.txt",
        },
        "Evaluation": "guidelines/generate_merge_evaluation.txt",
    }

    coverage_merged = {}

    def recursion(coverage_chunks, coverage_merged, section_to_guidelines):
        for k, v in section_to_guidelines.items():
            print("Merging coverage chunks for", k)
            if type(v) == str:
                with open(v) as f:
                    guidelines = f.read()
                prompt = (
                    "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to merge coverage chunks according to the following guidelines.\n\n"
                    + guidelines
                    + "\n\nMerge the following chunks.\n\nINPUT COVERAGE CHUNKS\n\n###\n"
                    + json.dumps([chunk[k] for chunk in coverage_chunks])
                    + "\n###"
                )
                response = generate(client, prompt)
                if k in ["Synopsis", "Characters"]:
                    response = response["data"]  # Non-JSON fields
                coverage_merged[k] = response
            else:
                coverage_merged[k] = {}
                recursion(
                    [chunk[k] for chunk in coverage_chunks],
                    coverage_merged[k],
                    section_to_guidelines[k],
                )

    recursion(coverage_chunks, coverage_merged, section_to_guidelines)
    return coverage_merged


def coverage_from_synopsis(client, example_coverage, coverage):
    section_to_guidelines = {
        "Metadata": {
            "Genre": "guidelines/generate_from_synopsis_genre.txt",
        },
        "Summary": {
            "Logline": "guidelines/generate_from_synopsis_logline.txt",
        },
        "Evaluation": {
            "Concept": "guidelines/generate_from_synopsis_evaluation_concept.txt",
            "Plot / Structure": "guidelines/generate_from_synopsis_evaluation_plot.txt",
            "Commerciality": "guidelines/generate_from_synopsis_evaluation_commerciality.txt",
        },
    }
    synopsis = coverage["Summary"]["Synopsis"]

    def recursion(coverage, example_coverage, section_to_guidelines):
        for k, v in section_to_guidelines.items():
            print("Coverage from synopsis for", k)
            if type(v) == str:
                with open(v) as f:
                    guidelines = f.read()
                prompt = (
                    "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to perform a script coverage according to the following guidelines.\n\n"
                    + guidelines
                    + "\n\nEXAMPLE SCRIPT COVERAGE\n\n"
                    + json.dumps(example_coverage[k])
                    + "\n\nWrite a coverage for the following script synopsis.\n\nINPUT SCRIPT SYNOPSIS\n\n###\n"
                    + synopsis
                    + "\n###"
                )
                response = generate(client, prompt)
                if k in ["Genre", "Logline"]:
                    response = response["data"]  # Non-JSON fields
                coverage[k] = response
            else:
                recursion(coverage[k], example_coverage[k], section_to_guidelines[k])

    recursion(coverage, example_coverage, section_to_guidelines)
    return coverage


def generate_recommendation(evaluation):
    grade_to_score = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}
    scores = [grade_to_score[v["Grade"]] for v in evaluation.values()]
    average_score = sum(scores) / len(scores)
    if average_score >= (3 * 2 + 2 * 3) / 5:
        return "Recommend"
    elif average_score >= 2:
        return "Consider"
    else:
        return "Pass"


def generate_coverage(
    input_script_path: str,
    output_coverage_path: str,
    example_coverage_path: str = "coverages_human/detox_coverage.json",
    num_chunks: int = 3,
):
    with open(example_coverage_path) as f:
        example_coverage = json.load(f)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    coverage = coverage_from_script_chunks(
        client, input_script_path, example_coverage, num_chunks
    )
    coverage = coverage_from_synopsis(client, example_coverage, coverage)
    coverage["Evaluation"]["Recommendation"] = generate_recommendation(
        coverage["Evaluation"]
    )
    with open(output_coverage_path, "w") as f:
        json.dump(coverage, f, indent=4)

    print(coverage)


if __name__ == "__main__":
    """
    python generate_coverage.py \
        --input_script_path scripts/being_silver.txt \
        --output_coverage_path coverages_generated/being_silver_coverage.json
    """
    fire.Fire(generate_coverage)
