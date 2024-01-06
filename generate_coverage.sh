#!/bin/bash

script_dir="scripts_txt"

# script_names=($(ls $script_dir | sed 's/\.txt$//'))
script_names=("anchorite" "moth" "goin_hard" "forever_marilyn")

for name in "${script_names[@]}"; do
    python generate_coverage.py \
        --input_script_path "${script_dir}/${name}.txt" \
        --output_coverage_path "coverages_generated_txt/${name}_coverage.txt"
done
