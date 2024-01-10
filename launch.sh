#!/bin/bash

script="isle_of_man"

python generate_coverage.py \
    --input_script_path scripts/${script}.txt \
    --output_coverage_path coverages_generated/${script}_coverage.json

python evaluate_coverage.py \
    --generated_coverage_path coverages_generated/${script}_coverage.json \
    --human_coverage_path coverages_human/${script}_coverage.json \
    --output_review_path reviews_generated/${script}_review.json
