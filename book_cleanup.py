import argparse
import os
from os import listdir
from os.path import isfile, join
import json
from tqdm import tqdm
import pandas as pd


# fields to drop from the metadata
drop_fields = [
    "a11y_NoEssentialInfoByColor",
    "a11y_NoTextIncludedInAnyImages",
    "epub_HowToPublishImageDescriptions",
    "epub_RemoveFontStyles",
    "bloomdVersion",
    # "experimental", # used in lmset later.
    "baseUrl",
    "bookOrder",
    "downloadSource",
    "formatVersion",
    "allowUploadingToBloomLibrary",
    "bookletMakingIsAppropriate",
    "LeveledReaderTool",
    "LeveledReaderLevel",
    "xmatterName",
    "uploader",
    "tools",
    "currentTool",
    "toolboxIsOpen",
    "hazards",
    "a11yFeatures",
    "a11yLevel",
    "a11yCertifier",
    "internetLimits" "use-original-copyright",
]

# Open ISO code table
iso_table = "assets/iso-639-3_Code_Tables_20210218/iso-639-3.tab"
iso_codes = pd.read_csv(iso_table, sep="\t")


# convertISO converts language codes to iso639-3
def convertISO(lang):
    if len(lang) == 3:
        return lang
    candidates = iso_codes[iso_codes["Part1"] == lang]
    if len(candidates) > 0:
        return candidates["Id"].values.tolist()[0]
    else:
        return ""


def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Postprocess Bloom books")

    parser.add_argument(
        "--source", dest="source", help="directory containing the bloom book extracts"
    )
    parser.add_argument(
        "--out", dest="out", help="output directory for cleaned book extracts"
    )
    args = parser.parse_args()

    # Create output directory if its not there
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    # loop over book files
    i = 0
    count = 0
    for jsonfile in tqdm(listdir(args.source)):
        if ".json" in jsonfile:
            with open(join(args.source, jsonfile)) as f:
                book = json.load(f)

            print(book["title"])
            if book["experimental"] == False and "cc-" in book["license"]:

                # Clean out unwanted fields
                for field in drop_fields:
                    if field in book.keys():
                        del book[field]

                # Get content languages and samples
                samples = {}
                languages = {}
                indices = []
                for k in book.keys():
                    if k.isdecimal():
                        indices.append(k)
                        samples[int(k)] = book[k]
                        for lang in book[k]:
                            languages[lang] = lang

                # Convert language codes
                delete_langs = []
                for lang in languages.keys():
                    if len(lang) == 3:
                        pass
                    elif len(lang) == 2:
                        languages[lang] = convertISO(lang)
                    else:
                        delete_langs.append(lang)
                for l in delete_langs:
                    del languages[l]

                # Convert samples to ISO codes
                texts = {}
                i = 0
                new_samples = {}
                for idx in samples.keys():
                    entry = {}
                    for l in samples[idx].keys():
                        if l in languages.keys() and languages[l] != "":
                            entry[convertISO(l)] = samples[idx][l]
                    new_samples[i] = entry
                    i += 1
                samples = new_samples

                # Remove old samples
                for k in indices:
                    del book[k]

                # Get full book texts
                full_texts = {}
                num_samples = len(samples)
                for l in list(languages.values()):
                    full_text = []
                    for sample in range(0, num_samples):
                        if l in samples[sample].keys():
                            full_text.append(samples[sample][l])
                        else:
                            full_text.append("")
                    full_texts[l] = "\n".join(full_text)

                # If there isn't any text in a language, delete it
                # from the content languages and full_text entries.
                delete_langs = []
                for l in full_texts.keys():
                    if len(full_texts[l].strip()) == 0:
                        delete_langs.append(l)
                delete_lang_orig = []
                for l in delete_langs:
                    del full_texts[l]
                    for l_orig in languages.keys():
                        if languages[l_orig] == l:
                            delete_lang_orig.append(l_orig)
                for l in delete_lang_orig:
                    del languages[l]

                # Add new fields
                book["contentLanguages"] = list(languages.values())
                book["bookSamples"] = samples
                book["bookText"] = full_texts

                # Save out the modified file
                with open(join(args.out, jsonfile), "w") as outFile:
                    json.dump(book, outFile, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()

