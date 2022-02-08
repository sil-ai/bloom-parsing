#!/bin/bash
# TODO: rewrite this whole bash script using Python pathlib within book_parser.py. We just need to iterate over subfolders of a folder, we can do that in Python and add tqdm progress bar. 

# make the out directory, -p so it won't crash if the directory exists already. Also doable in Python. 
mkdir -p "out"
for book in "$1"/*
do
    echo "$book"
    # curfile="$(basename "$book")"
    # echo "curfile $curfile"
    python3 book_parser.py --source "$book" --out "out"
done
