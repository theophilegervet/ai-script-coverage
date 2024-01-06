#!/bin/bash

script_dir="scripts_txt"

script_names=($(ls $script_dir | sed 's/\.txt$//'))

for name in "${script_names[@]}"; do
    python generate_coverage.py \
        --generated_coverage_path "coverages_generated/${name}_coverage.json" \
        --human_coverage_path "coverages_human/${name}_coverage.json" \
        --output_review_path "reviews_generated/${name}_review.json"
done
