import argparse
import os
from os import listdir
from os.path import isfile, join
import json


def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(
            description="Postprocess Bloom books"
            )

    parser.add_argument(
            "--source",dest='source',
            help="directory containing the bloom book extracts"
            )
    parser.add_argument("--out", dest='out',
            help="output directory for cleaned book extracts"
            )
    args = parser.parse_args()

    # Create output directory if its not there
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    # loop over book files
    languages = {}
    for jsonfile in listdir(args.source):
        if ".json" in jsonfile:
            with open(join(args.source, jsonfile)) as f:
                book = json.load(f)

        # Get language and family 
        for lang in book['bookText']:

            # Add to list of books for language
            if lang in languages.keys() and languages[lang] != None:
                languages[lang].append(book['bookText'][lang])
            elif book['bookText'][lang] != None:
                languages[lang] = [book['bookText'][lang]]

    for lang in languages.keys():
        if languages[lang] != None:
            books = list(set(languages[lang]))
            languages[lang] = books

    # Output data for language modeling
    with open(join(args.out, 'lm.json'), 'w') as outFile:
        json.dump(languages, outFile, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()

