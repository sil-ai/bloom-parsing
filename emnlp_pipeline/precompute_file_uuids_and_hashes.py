from collections import defaultdict
import itertools
from pathlib import Path
import uuid
import hashlib
import argparse
import json
from tqdm import tqdm
from PIL import Image, UnidentifiedImageError
import imagehash


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

            # # get a resized rgb version.
            # small_im = resize_image_and_save_colors(bloom_file=bloom_file)
            # if small_im is not None:
            #     file_dict["small_im_pixel_list"] = list(small_im.getdata())

            image_hash = calculate_image_hash_for_file(bloom_file=bloom_file)
            if image_hash is not None:
                file_dict["image_hash"] = str(image_hash)

            files_dict[book_name][filename] = file_dict

    # TEST CODE
    # _test_using_small_image_samples_for_image_same_checking(files_dict=file_dict)
    # _test_checking_using_image_hash(files_dict=files_dict)

    # print(f"We have {len(files_dict.keys())} books in our dictionary.")
    print(f"We have {len(files_dict)} books in our dictionary.")
    with open(output_file, "w") as outfile:
        json.dump(files_dict, outfile)


def _test_checking_using_image_hash(files_dict):
    percentage_match_threshold = 0.9

    all_files = []
    # duplicates = {}
    for bookname, book_dict in files_dict.items():

        for filename, file_dict in book_dict.items():
            if "image_hash" in file_dict:
                all_files.append(file_dict)

    for file_dict1, file_dict2 in itertools.combinations(all_files, 2):
        file_name1 = f"{file_dict1['book_name']}/{file_dict1['filename']}"
        file_name2 = f"{file_dict2['book_name']}/{file_dict2['filename']}"
        image_hash1 = file_dict1["image_hash"]
        image_hash2 = file_dict2["image_hash"]

        if image_hash1 == image_hash2:
            print(f"{file_name1} and {file_name2} have the same hash")


def _test_using_small_image_samples_for_image_same_checking(files_dict):
    percentage_match_threshold = 0.9

    all_files = []

    for bookname, book_dict in files_dict.items():

        for filename, file_dict in book_dict.items():
            all_files.append(file_dict)

    for file_dict1, file_dict2 in itertools.combinations(all_files, 2):
        file_name1 = f"{file_dict1['book_name']}/{file_dict1['filename']}"

        file_name2 = f"{file_dict2['book_name']}/{file_dict2['filename']}"
        pixel_list1 = file_dict1["small_im_pixel_list"]
        pixel_list2 = file_dict2["small_im_pixel_list"]

        if pixel_list1 is not None and pixel_list2 is not None:
            pixel_percentage_match = calculate_pixel_match(pixel_list1, pixel_list2)

            if pixel_percentage_match > percentage_match_threshold:
                print(f"{file_name1} matches {file_name2}")
            else:
                print(
                    f"{file_name1} doesn't match {file_name2}. Percentage: {pixel_percentage_match}"
                )
                pass


def calculate_image_hash_for_file(bloom_file):
    try:
        hash = imagehash.phash(Image.open(bloom_file))

        return hash
    except UnidentifiedImageError:
        # print(f"couldn't parse {bloom_file}")
        return None
    except OSError:
        # image is truncated or corrupted.
        return None


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


def resize_image_and_save_colors(bloom_file, size=(3, 3)):
    """
     The idea being to detect if images are the same but just different size.
     https://stackoverflow.com/questions/7848825/determine-if-images-are-the-same-but-different-sizes
    """
    try:
        im = Image.open(bloom_file)
        im = im.convert("RGB")  # remove transparency
        small = im.resize(size=size)
        # print(small.size)
        # print()
        # print("********")
        # print(bloom_file)
        # print(list(small.getdata()))

        return small
    except UnidentifiedImageError:
        # print(f"couldn't parse {bloom_file}")
        return None


def calculate_pixel_match(small_im1_pixel_list, small_im2_pixel_list):
    # print("calculating pixel match!")

    pixel_vals_checked_count = 0
    pixel_vals_the_same_count = 0
    for rgb1, rgb2 in zip(small_im1_pixel_list, small_im2_pixel_list):
        # print(f"{rgb1=}")
        # print(f"{rgb2=}")
        # r1, g1, b1 = rgb1
        # r2, g2, b2 = rgb2

        for i, pixel_val in enumerate(rgb1):
            pixel_vals_checked_count += 1
            other_pixel_val = rgb2[i]
            if pixel_val == other_pixel_val:
                pixel_vals_the_same_count += 1

        # print(f"r: {r1, r2}, g: {g_vals}, b: {b_vals}")
    pixel_percentage_match = pixel_vals_the_same_count / pixel_vals_checked_count
    # print(
    #     f"{pixel_vals_the_same_count=}, {pixel_vals_checked_count=}, {pixel_percentage_match=}"
    # )
    return pixel_percentage_match


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
