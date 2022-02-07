#!/bin/bash

for book in "$1"/*
do
    echo "$book"
    # curfile="$(basename "$book")"
    # echo "curfile $curfile"
    python3 book_parser.py --source "$book" --out "out"
done
