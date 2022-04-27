from collections import defaultdict
from pathlib import Path
import uuid
import hashlib
import argparse
import json
from tqdm import tqdm


def precompute_ids_and_hashes_for_dir_of_books(source_dir, output_file):
    """
    Given a directory of Bloom books, will calculate md5 and uuid for each file and output them. 
    """
    files_dict = defaultdict(dict)
    for bloom_file in tqdm(source_dir.rglob("*")):
        if bloom_file.is_file():
            book_name = bloom_file.parent.name
            filename = bloom_file.name

            hash = calculate_hash_for_file(bloom_file)

            id = str(uuid.uuid4())

            file_dict = {
                "book_name": book_name,
                "filename": filename,
                "hash": hash,
                "id": id,
            }

            files_dict[book_name][filename] = file_dict

    # print(f"We have {len(files_dict.keys())} books in our dictionary.")
    print(f"We have {len(files_dict)} books in our dictionary.")
    with open(output_file, "w") as outfile:
        json.dump(files_dict, outfile)


def calculate_hash_for_file(bloom_file):
    """
    Based on https://www.pythoncentral.io/hashing-files-with-python/
    """
    md5_hasher = hashlib.md5()
    with open(bloom_file, "rb") as bloom_file_fd:
        buf = bloom_file_fd.read()
        md5_hasher.update(buf)

    hash = md5_hasher.hexdigest()
    return hash


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Precompute Bloom book file hashes and ids"
    )

    parser.add_argument(
        "source_dir",
        # dest="source",
        type=Path,
        help="directory containing the input files for all the bloom books",
    )
    parser.add_argument(
        "--output_file",
        # dest="outputfile",
        default="./ids_and_hashes.json",
        type=Path,
        help="output file for ids and hashes. Defaults to ./ids_and_hashes.json",
    )
    args = parser.parse_args()

    source_dir = args.source_dir
    output_file = args.output_file
    print(args)

    precompute_ids_and_hashes_for_dir_of_books(source_dir, output_file)
