#!/bin/bash

script_dir="scripts_txt"

script_names=($(ls $script_dir | sed 's/\.txt$//'))

for name in "${script_names[@]}"; do
    python generate_coverage.py \
        --input_script_path "${script_dir}/${name}.txt" \
        --generated_coverage_path "coverages_generated_txt/${name}_coverage.txt" \
        --human_coverage_path "coverages_human_txt/${name}_coverage.txt" \
        --output_comparison_path "coverages_comparison_txt/${name}_comparison.txt"
done
