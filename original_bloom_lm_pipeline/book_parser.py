import os
import json
from os import listdir
from os.path import isfile, join

import argparse
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

# TODO: track process in clearML


def parse_htmfiles(source_dir):
    # print(f"source {source}")

    htmfiles = [f for f in listdir(source_dir) if "htm" in f]
    print(f"htmfile {htmfiles}")

    book_texts = []
    for htmfile in htmfiles:
        htmfile_path = os.path.join(source_dir, htmfile)
        book_text = parse_text_from_one_htmfile(htmfile_path)
        book_texts.append(book_text)

    return book_texts


def parse_text_from_one_htmfile(htmfile_path):

    # print(f"thingamajig: {htmfile_path}")
    with open(htmfile_path) as file:
        page = file.read()

    soup = BeautifulSoup(page, "html.parser")

    # MAYBE: cross-reference with metadata?
    # booktitle = soup.find("title")
    # print(f"book title: {booktitle.text}")

    divs = soup.findAll("div")

    i = 0  # TODO: figure out what this index is for -CDL
    BookText = {}

    for div in divs:
        if div.has_attr("data-book") and "topic" in div.get("data-book"):
            print("found the topic div")
            htmltopic = div.text.strip()

        if div.has_attr("class") and "bloom-translationGroup" in div.get("class"):
            entry = {}
            subdivs = div.findAll("div")

            for subdiv in subdivs:
                if (
                    subdiv.has_attr("lang")
                    and subdiv.get("lang") != "*"
                    and subdiv.get("lang") != ""
                ):
                    texts = subdiv.findAll("p")

                    book_text = ""
                    for text in texts:
                        if book_text != "":
                            book_text += "\n" + text.get_text()
                        else:
                            book_text = text.get_text()
                    entry[subdiv.get("lang")] = book_text

            if len(entry.keys()) > 0:
                BookText[i] = entry

            i += 1

    return BookText


def parse_metadata(mpath):

    with open(mpath) as metadata:
        metadata = json.load(metadata)

    return metadata


def output(metadata, book_content, outdir):
    metadata.update(book_content)

    key = metadata["downloadSource"]
    split_key = key.split("/")
    filename = split_key[1] + ".json"
    print(f"output to {filename}")

    with open(os.path.join(outdir, filename), "w") as f:
        metadata_full = json.dump(
            metadata,
            f,
            indent="  ",
            check_circular=True,
            allow_nan=True,
            cls=None,
            separators=None,
        )

    return metadata_full


def main():
    parser = argparse.ArgumentParser(description="Preprocess Bloom books")

    parser.add_argument(
        "--source",
        dest="source",
        help="directory containing the input files for all the bloom books",
    )
    parser.add_argument(
        "--out", dest="out", help="output directory for parsed book files"
    )

    args = parser.parse_args()
    output_folder = Path(args.out)
    output_folder.mkdir(parents=True, exist_ok=True)
    # print(f"args.source {args.source}")

    # book_texts = parse_htmfiles(args.source)
    source_path = Path(args.source)
    for book_folder in source_path.iterdir():
        if book_folder.is_dir():

            htmfiles = list(book_folder.glob("*.htm"))
            mpath = book_folder / "meta.json"
            if mpath.exists():
                metadata_fin = parse_metadata(mpath)
                print(htmfiles)
                for htmfile in htmfiles:
                    if metadata_fin["title"] in htmfile.name:
                        book_text = parse_text_from_one_htmfile(htmfile)
                        # exit()

                        output(metadata_fin, book_text, args.out)


if __name__ == "__main__":
    main()
