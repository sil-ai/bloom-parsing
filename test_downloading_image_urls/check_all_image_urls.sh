#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# jq -r gets you the URLs without quotes. 
# then shuffle them
# then see if the file exists. 
jq -r .images[].url_o ../../data/bloom_vist_june15_deduped_by_album_and_story.json|shuf|parallel wget --method=HEAD 2>&1|tee wget_head_output.txt
