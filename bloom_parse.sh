#!/bin/bash

for book in $1/*
do
    echo $book
    curfile="$(basename "$book")"
    mkdir -p /out/$curfile
    python book_parser.py --source $book --out /out/$curfile
done
