import argparse
import os
from os import listdir
from os.path import isfile, join
import json

import pandas as pd


# Open Ethnologue data
langs_table = 'assets/Table_of_Languages.tab'
langs = pd.read_csv(langs_table, sep='\t')


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
    families = {}
    regions = {}
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

            # Get language family and Region
            langs_candidates = langs[langs['ISO_639'] == lang]
            if len(langs_candidates) > 0:
                family = langs_candidates['Family'].values[0]
                if family in families.keys() and families[family] != None:
                    families[family].append(book['bookText'][lang])
                else:
                    families[family] = [book['bookText'][lang]]
                region = langs_candidates['Region_Name'].values[0]
                if region in regions.keys() and regions[region] != None:
                    regions[region].append(book['bookText'][lang])
                else:
                    regions[region] = [book['bookText'][lang]]
            else:
                if 'unknown' in families.keys() and families['unknown'] != None:
                    families['unknown'].append(book['bookText'][lang])
                else:
                    families['unknown'] = [book['bookText'][lang]]
                if 'unknown' in regions.keys() and regions['unknown'] != None:
                    regions['unknown'].append(book['bookText'][lang])
                else:
                    regions['unknown'] = [book['bookText'][lang]]

    # Get stats
    family_raw = []
    region_raw = []
    language_raw = []

    for lang in languages.keys():
        if languages[lang] != None:
            books = list(set(languages[lang]))
            language_raw.append([
              lang,
              len(books),
              len('\n'.join(books))
            ])

    for fam in families.keys():
        if families[fam] != None:
            books = list(set(families[fam]))
            family_raw.append([
              fam,
              len(books),
              len('\n'.join(books))
            ])

    for region in regions.keys():
        if regions[region] != None:
            books = list(set(regions[region]))
            region_raw.append([
                region,
                len(books),
                len('\n'.join(books))
            ])

    # Output
    lang_out = pd.DataFrame(language_raw, columns=['language', 'num_books', 'num_chars'])
    reg_out = pd.DataFrame(region_raw, columns=['region', 'num_books', 'num_chars'])
    fam_out = pd.DataFrame(family_raw, columns=['family', 'num_books', 'num_chars'])

    lang_out.to_csv(join(args.out, 'languages.csv'), index=False)
    reg_out.to_csv(join(args.out, 'regions.csv'), index=False)
    fam_out.to_csv(join(args.out, 'families.csv'), index=False)

if __name__ == "__main__":
    main()

