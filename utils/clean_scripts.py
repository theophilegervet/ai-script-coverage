import glob

for script_path in glob.glob("scripts_txt/*.txt"):
    with open(script_path, "r") as f:
        lines = f.readlines()
    # Remove empty lines
    cleaned_lines = [line for line in lines if line.strip()]
    cleaned_script = "".join(cleaned_lines)
    with open(script_path, "w") as f:
        f.write(cleaned_script)
