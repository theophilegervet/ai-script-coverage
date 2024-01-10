import concurrent
import json
import os
import re

import fire
from openai import OpenAI
from tqdm import tqdm


def generate(client, prompt, model):
    messages = [
        {
            "role": "system",
            "content": "You are an expert movie producer.",
        },
        {"role": "user", "content": prompt},
    ]
    return (
        client.chat.completions.create(
            model=model,
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


def split_script_into_scenes(file_path):
    with open(file_path, "r") as file:
        script = file.read()
    pattern = r"(EXT\.|INT\.)(.*?)(?=(\nEXT\.|\nINT\.|$))"
    matches = re.findall(pattern, script, re.DOTALL)
    scenes = [f"{match[0]}{match[1].strip()}" for match in matches]
    return scenes


def generate_synopsis(
    input_script_path: str,
    output_synopsis_path: str,
    store_scene_summaries: bool = True,
    read_scene_summaries: bool = False,
):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def synthesize_scene(scene, scene_idx):
        prompt = (
            "INSTRUCTIONS\n\nDescribe the main event in this scene. Reply concisely with just the event, without an intro. Keep full character names capitalized with their age parenthesized, e.g., JOHN DOE (42).\n\n"
            + "\n\nINPUT SCENE\n\n###\n"
            + scene
            + "\n###"
        )
        return generate(client, prompt, "gpt-3.5-turbo-1106"), scene_idx

    if read_scene_summaries:
        with open("scene_summaries.json", "r") as f:
            scene_summaries = json.load(f)
    else:
        scenes = split_script_into_scenes(input_script_path)
        scene_summaries = []
        with tqdm(total=len(scenes), desc="Coverage from scenes") as pbar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(synthesize_scene, s, i)
                    for i, s in enumerate(scenes)
                ]
                for future in concurrent.futures.as_completed(futures):
                    summary, scene_idx = future.result()
                    scene_summaries.append((summary, scene_idx))
                    pbar.update(1)
                scene_summaries = sorted(scene_summaries, key=lambda x: x[1])
                scene_summaries = [s for s, _ in scene_summaries]

        if store_scene_summaries:
            with open("scene_summaries.json", "w") as f:
                json.dump(scene_summaries, f, indent=4)

    scene_headers = [s.split("\n")[0] for s in scenes]
    scene_summaries = [
        f"{header}: {summary}"
        for header, summary in zip(scene_headers, scene_summaries)
    ]

    with open("guidelines/synopsis_merge.txt") as f:
        guidelines = f.read()

    prompt = (
        "INSTRUCTIONS\n\nYou are an expert at script coverage and will be asked to merge scene summaries into a coherent script Synopsis according to the following guidelines.\n\n"
        + guidelines
        + "\n\nMerge the following scene summaries.\n\nSCENE SUMMARIES\n\n###\n"
        + json.dumps(scene_summaries)
        + "\n###"
    )
    synopsis = generate(client, prompt, "gpt-4-1106-preview")

    with open(output_synopsis_path, "w") as f:
        f.write(synopsis)

    print(synopsis)


if __name__ == "__main__":
    """
    python generate_synopsis.py \
        --input_script_path scripts/being_silver.txt \
        --output_synopsis_path synopsis_generated/being_silver_synopsis.txt
    """
    fire.Fire(generate_synopsis)
