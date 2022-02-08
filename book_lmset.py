import argparse
import os
from os import listdir
from os.path import isfile, join
import json
from collections import defaultdict
from tqdm import tqdm


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
    languages = defaultdict(list)
    for jsonfile in tqdm(listdir(args.source)):
        if ".json" in jsonfile:
            with open(join(args.source, jsonfile)) as f:
                book = json.load(f)

        # Get language and family 
        for lang in book['bookText']:

            # create a new dictionary to hold text and metadata for this particular language. 
            book_for_lang = {}
            book_for_lang["title"] = book["title"]
            book_for_lang["license"] = book["license"]
            book_for_lang["copyright"] = book["copyright"]
            book_for_lang["pageCount"] = book["pageCount"]
            book_for_lang["bookInstanceId"] = book["bookInstanceId"]
            book_for_lang["bookLineage"] = book["bookLineage"]
            book_for_lang["allTitles"] = book["allTitles"]
            book_for_lang["contentLanguages"] = book["contentLanguages"]
            book_for_lang["bookText"] = book["bookText"][lang] # there might be multiple languages in there. We want this specific language. 

            # Add to list of books for language # TODO: defaultdict(list)
            # languages[lang].append(book['bookText'][lang]) # works if it's a defaultdict
            languages[lang].append(book_for_lang) # works if it's a defaultdict

            # if lang in languages.keys() and languages[lang] != None:
            #     languages[lang].append(book['bookText'][lang])
            #     # languages[lang].append(book_for_lang)
            # elif book['bookText'][lang] != None:
            #     languages[lang] = [book['bookText'][lang]]
            #     # languages[lang] = [book_for_lang]
                

    total = 0
    for lang in languages.keys():
        if languages[lang] != None:
            books = list(languages[lang])
            books_count = len(books)
            print(f"for lang {lang} there are {books_count} books")
            languages[lang] = books
            total = total + books_count

    print(f"wrote out {total} books")
    # Output data for language modeling
    with open(join(args.out, 'lm.json'), 'w') as outFile:
        json.dump(languages, outFile, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()

