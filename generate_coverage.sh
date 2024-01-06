#!/bin/bash

script_dir="scripts"

script_names=($(ls $script_dir | sed 's/\.txt$//'))

for name in "${script_names[@]}"; do
    python generate_coverage.py \
        --input_script_path "${script_dir}/${name}.txt" \
        --output_coverage_path "coverages_generated/${name}_coverage.json"
done
