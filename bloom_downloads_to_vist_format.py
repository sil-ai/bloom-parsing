from __future__ import annotations
import argparse
from collections import defaultdict
from pathlib import Path
import random
import uuid
import json
import logging
from bs4 import BeautifulSoup, PageElement
import precompute_file_uuids_and_hashes
from urllib.parse import unquote, urlparse, quote_plus, unquote_plus
from tqdm import tqdm
import datetime
import langcodes
import csv

# usage example: python bloom_downloads_to_vist_format.py data/bloom_downloads/ ./ids_and_hashes.json --out bloom_downloads_vist_filtered_by_license_with_web_urls_and_improved_subdiv_fallback_parsing_and_urls_from_aws_manifest_2022-05-09.json --log info


# https://stackoverflow.com/questions/4292029/how-to-get-a-list-of-file-extensions-for-a-general-file-type
BLOOM_IMAGE_FORMATS = (".jpg", ".png")  # contentful images, excluding svg on purpose.

# licenses I found by searching all meta.json files in bloom_downloads -CDL
BLOOM_LICENSES_OBSERVED = [
    "ask",
    "cc0",
    "cc-by",
    "cc-by-nc",
    "cc-by-nc-nd",
    "cc-by-nc-sa",
    "cc-by-nd",
    "cc-by-sa",
    "custom",
    "null",
]
OPEN_LICENSES = [
    "cc0",
    "cc-by",
    "cc-by-nc",
    "cc-by-nc-nd",
    "cc-by-nc-sa",
    "cc-by-nd",
    "cc-by-sa",
]


def get_image_files_in_folder(book_folder):
    return [
        img for img in book_folder.iterdir() if img.name.endswith(BLOOM_IMAGE_FORMATS)
    ]


# def create_vist_stories_for_book(
#     image_caption_pairs, book_folder, metadata_fin, ids_and_hashes, vist_album, book_htm
# ):
#     """
#     'story' is when you've got captions for an album. in VIST you might have had an album of images,
#     and then have that album get turned into a story by volunteers more than once.
#     So for one album you might have multiple stories.

#     We originally wrote this code here assuming there was one "story" per book, but
#     in fact have multiple "stories" per htm, one per language. TODO: fix this problem.

#     Each bloom "translation" will be given a story id
#     """
#     # dictionary indexed by language code. each book/translation combo is a story.
#     story_ids = {}

#     image_caption_pairs_with_story_ids = []
#     for image, caption_dict in image_caption_pairs:
#         print(caption_dict)

#         # update the caption dict, which currently just contains "text", with the story ID
#         for lang, text in caption_dict.items():
#             if lang not in story_ids.keys():
#                 story_ids[lang] = str(uuid.uuid4())
#             caption_dict[lang]["story_id"] = story_ids[lang]

#         image_caption_pairs_with_story_ids.append(image, caption_dict)

#     # story_id = ids_and_hashes[book_folder.name][book_htm.name][
#     #     "id"
#     # ]  # it is a uuid, it is unique to the story. #TODO: uuid3 for story ID?
#     # image_caption_pairs_with_story_ids = {
#     #     "story_id": story_id,
#     #     "image_caption_pairs": image_caption_pairs,
#     # }

#     return stories_dict


def calculate_web_url_given_local_path(s3_bucket, local_path):

    # local_path should be something like book_folder_path.name / image_path.name, e.g. "My Face Tells a Story/1 Cover1.jpg"
    # web_url should be something like "https://bloom-vist.s3.amazonaws.com/My+Face+Tells+a+Story/1+Cover1.jpg" aka using quote_plus
    bucket_name = urlparse(
        s3_bucket
    ).hostname  # given "s3://bloom-vist" should give "bloom-vist"
    web_url = f"https://{bucket_name}.s3.amazonaws.com"
    for part in Path(local_path).parts:
        web_url = web_url + "/" + quote_plus(part)

    logging.debug(
        f"for local path {local_path} and s3 bucket {s3_bucket}, calculated {web_url}"
    )
    return web_url


def create_vist_images_for_book(
    image_caption_pairs,
    book_folder,
    metadata_fin,
    ids_and_hashes,
    vist_album,
    s3_bucket,
):
    """
    VIST dataset had an array of image dictionaries called 'images'. 
    Each entry contained a URL. We're just gonna put 
    """
    # example_images = {
    #     "images": [
    #         {
    #             "datetaken": "2004-11-27 10:40:46",
    #             "license": "1",
    #             "title": "The venue.",
    #             "text": "",
    #             "album_id": "44277",
    #             "longitude": "-0.212688",
    #             "url_o": "https://farm1.staticflickr.com/2/1741642_81837e8e9e_o.jpg",
    #             "secret": "81837e8e9e",
    #             "media": "photo",
    #             "latitude": "51.920449",
    #             "id": "1741642",
    #             "tags": "stevenage fairies craftfair xmas 2004",
    #         },
    #     ]
    # }
    vist_images_for_book = []
    for image, _ in image_caption_pairs:
        image_id = ids_and_hashes[book_folder.name][image]["id"]

        local_image_path = f"{book_folder.name}/{image}"

        try:
            web_url = ids_and_hashes[book_folder.name][image]["web_url"]
        except KeyError:
            web_url = calculate_web_url_given_local_path(
                s3_bucket=s3_bucket, local_path=local_image_path
            )  # obsolete, we simply match the aws manifest above.

        image_dict = {
            # "datetaken": "", # TODO: image datetaken
            # "license": "1", # TODO: image license
            # "title": "",  # TODO: image title
            # "text": "",  # TODO: image text
            "album_id": vist_album["id"],  # TODO: image
            # "longitude": "-0.212688",  # TODO: image longitude
            "url_o": web_url,
            "local_image_path": local_image_path,
            # "secret": "81837e8e9e",  # TODO: image secret
            "media": "photo",
            # "latitude": "51.920449",  # TODO: image latitude
            "id": str(image_id),
            # "tags": "stevenage fairies craftfair xmas 2004", # TODO: image tags
        }

        vist_images_for_book.append(image_dict)
    return vist_images_for_book


def create_vist_annotations_for_book(
    image_caption_pairs, book_folder, metadata_fin, ids_and_hashes, vist_album,
):
    # Copied from original VIST test.story-in-sequence.json
    # example_annotations = {
    #     "annotations": [
    #         [
    #             {
    #                 "original_text": "The local parish holds a craft show each year.",
    #                 "album_id": "44277",
    #                 "photo_flickr_id": "1741642",
    #                 "setting": "first-2-pick-and-tell",
    #                 "worker_id": "FJROI8NWDRIPAM1",
    #                 "story_id": "45530",
    #                 "tier": "story-in-sequence",
    #                 "worker_arranged_photo_order": 0,
    #                 "text": "the local parish holds a craft show each year .",
    #                 "storylet_id": "227650",
    #             }
    #         ],
    #     ]
    # }

    # annotations is a list of lists, of dicts. Each annotation is a 1-element list.
    annotations = []

    story_ids_for_book = {}  # one per translation
    for image, captions in image_caption_pairs:
        image_id = ids_and_hashes[book_folder.name][image]["id"]
        album_id = vist_album["id"]

        for lang in captions:
            if lang not in story_ids_for_book.keys():
                story_ids_for_book[lang] = str(uuid.uuid4())
            story_id = story_ids_for_book[lang]

            # lots of MY downstream code expects a dictionary with the key being the langid.
            # but original VIST does not want it.
            # we could also just add a lang field?
            # Also had to edit bloom-vist and bloom-captioning loading scripts.
            # caption = {lang: captions[lang]}

            annotation = [
                {
                    # "original_text": "The local parish holds a craft show each year.", # TODO: annotation original_text
                    "album_id": album_id,
                    "photo_flickr_id": image_id,  # TODO: annotation photo_flickr_id
                    # "setting": "first-2-pick-and-tell", # TODO: annotation setting
                    # "worker_id": "FJROI8NWDRIPAM1", # TODO: annotation worker_id
                    "story_id": story_id,
                    # "tier": "story-in-sequence",  # TODO: tier
                    # "worker_arranged_photo_order": 0, # TODO: worker_arranged_photo_order
                    # "storylet_id": "227650"
                    "text": captions[lang],  # original VIST format
                    "lang": lang,  # NOT IN ORIGINAL VIST
                }
            ]

        annotations.append(annotation)
    return annotations


def create_vist_album_for_book(
    image_caption_pairs, book_folder, metadata_fin, htm_book_metadata
):

    # Took the following from original VIST
    # example_album = {
    #     "description": "I left Stevenage over twenty years ago, having lived there between the ages of 7 and 20. Yesterday (on International Buy Nothing Day!) we returned for a 'Victorian Craft Fair' in the Church above the town Museum. Very strange...",
    #     "title": "A trip to Stevenage",
    #     "farm": "1",
    #     "date_update": "1396811566",
    #     "primary": "1741611",
    #     "server": "2",
    #     "date_create": "44277",
    #     "photos": "23",
    #     "secret": "3f374c96e5",
    #     "owner": "37996585435@N01",
    #     "vist_label": "fair",
    #     "id": "44277",
    # }
    vist_album = {
        # "description": "",  # TODO: album description
        "title": f"{book_folder.name}",  # todo: set album title from metadata?
        # "farm": "",  # TODO: album farm
        # "date_update": "",  # TODO: album date_update
        # "primary": "",  # TODO: album primary
        # "server": "",  # TODO: album server
        # "date_create": "",  # TODO: album date_create
        "photos": f"{len(image_caption_pairs)}",
        # "secret": "",  # TODO: album secret
        # "owner": "",  # TODO: album owner
        # "vist_label": "",  # TODO: album vist_label
        "id": metadata_fin["bookInstanceId"],
        "license": metadata_fin["license"],  # NOTE: not in original VIST format
        "metadata_from_original_json": metadata_fin,
        "metadata_from_htm_file": htm_book_metadata,
    }
    return vist_album


def parse_book_htm_for_metadata(book_htm):

    with open(book_htm) as file:
        page = file.read()

    soup = BeautifulSoup(page, "html.parser")

    book_htm_metadata = {}

    metas = soup.find_all("meta")
    for meta in metas:  # <class 'bs4.element.Tag'>

        if meta.has_attr("name") and meta.has_attr("content"):

            book_htm_metadata[meta.get("name")] = meta.get("content")

    # https://www.geeksforgeeks.org/extract-json-from-html-using-beautifulsoup-in-python/
    book_htm_metadata["bloomDataDiv"] = {}
    book_data = soup.find("div", id="bloomDataDiv")
    book_htm_metadata["bloomDataDiv"]["raw_html"] = book_data.text

    book_data.find_all("div", attrs={"book-data": True})
    for item in book_data.find_all("div", attrs={"data-book": True}):
        # bs4.element.Tag.attrs

        meta_item = {}
        metadata_name = item.get("data-book")

        for attr_key, attr_value in item.attrs.items():

            if attr_key == "data-book":
                meta_item[metadata_name] = item.text
            else:
                meta_item[attr_key] = attr_value
        book_htm_metadata["bloomDataDiv"][metadata_name] = meta_item

    return book_htm_metadata


def parse_matching_images_and_captions_from_htmfile(htmfile_path):

    # HOW TO MATCH IMAGES TO TEXT? TODO: handle special cases
    # if they're in the same numberedPage that's easy.
    # But sometimes you have image on one page and captions on the next??
    # Do we, like, make tuples, and then if there's
    # (img, captions)
    # (img, None)
    # (None, captions)
    # then we collapse the two together?
    img_caption_tuples = []
    with open(htmfile_path) as file:
        page = file.read()

    soup = BeautifulSoup(page, "html.parser")

    # MAYBE: cross-reference with metadata?
    # booktitle = soup.find("title")

    divs = soup.findAll("div")
    # topics = soup.select()
    pages = soup.find_all("div", class_="numberedPage")
    logging.info(f"pages count: {len(pages)}")

    for page in pages:
        logging.debug(f"xxxxxxxxxxxxxxxxxxx parsing page xxxxxxxxxxxxxxxxxxxxxxxxxx")
        tg_divs = page.find_all("div", class_="bloom-translationGroup")

        imgs = page.find_all("img")
        logging.warning(f"found {len(imgs)} imgs in the page: {imgs}")
        logging.warning(f"found {len(tg_divs)} translation groups in the page")
        # turns out you sometimes have, like, imgs on their own page followed by a caption.

        # if len(imgs) != len(tg_divs):
        #     logging.debug(
        #         f"number of translation groups does not match number of images for {imgs}. Skipping"
        #     )
        #     continue

        if imgs:
            img = imgs[0]
            img_src = img["src"]
            logging.warning(f"img_src: {img_src}")
        else:
            img_src = None

        if tg_divs:
            captions = defaultdict(str)
            for tg_div in tg_divs:
                tg_div_captions = parse_translation_group(tg_div)

                for key in tg_div_captions.keys():
                    captions[key] = captions[key] + tg_div_captions[key]

            captions = dict(captions)
            logging.warning(
                f"captions found in {len(tg_divs)} translationGroups: {captions}"
            )
        else:
            captions = None
        img_caption_tuples.append((img_src, captions))

    logging.info(
        f"From '{htmfile_path.name}', extracted {len(img_caption_tuples)} tuples containing images and/or captions from numberedPage divs"
    )

    # attempting to fix books which have caption following image on a separate page.
    fixed_tuples = []
    for i, img_caption_tuple in enumerate(img_caption_tuples):
        if i > 0:
            prev_img, prev_caption = img_caption_tuples[i - 1]
            img, caption = img_caption_tuple

            if img is not None and caption is not None:
                fixed_tuples.append(img_caption_tuple)
            elif img is None and caption is not None:

                if prev_img is not None and prev_caption is None:
                    new_tuple = (prev_img, caption)
                    fixed_tuples.append(new_tuple)
            elif img is not None and caption is None:

                pass
    logging.info(
        f"attempted to fix image/caption tuples. Before we had {len(img_caption_tuples)}, after: {len(fixed_tuples)} "
    )
    return fixed_tuples


def parse_translation_group(tg_div):
    entry = defaultdict(str)
    subdivs = tg_div.find_all(
        "div", {"lang": True}  # finds subdivs with this attribute.
    )
    # return recursive_get_text(tg_div)

    logging.debug(f"found subdivs in tg: {len(subdivs)}")

    for subdiv in subdivs:

        if (
            subdiv.has_attr("lang")
            and subdiv.get("lang") != "*"
            and subdiv.get("lang") != ""
            and subdiv.get("lang") != "z"  # always empty, not a valid code
        ):
            subdiv_lang = subdiv.get("lang")
            p_elements = subdiv.findAll("p")
            logging.debug(f"found texts for {subdiv_lang}: {p_elements}")

            book_text = ""
            for p_element in p_elements:
                if book_text != "":
                    book_text += "\n" + p_element.get_text()

                else:
                    book_text = p_element.get_text()

            if not p_elements:
                subdiv_text = subdiv.get_text()
                logging.debug(
                    f"Couldn't find any <p>, trying to parse the subdiv directly. Found: {subdiv_text}"
                )
                book_text += subdiv_text

            logging.debug(
                f"Existing entry before adding {book_text}: {entry[subdiv_lang]}"
            )
            entry[subdiv_lang] = entry[subdiv_lang] + book_text
    return entry


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
    # "LeveledReaderTool", # might be useful
    # "LeveledReaderLevel", # might be useful
    "xmatterName",
    "uploader",
    "tools",
    "currentTool",
    "toolboxIsOpen",
    "hazards",
    "a11yFeatures",
    "a11yLevel",
    "a11yCertifier",
    "internetLimits",
    "use-original-copyright",
]


def parse_metadata(mpath):

    with open(mpath) as metadata:
        metadata = json.load(metadata)

        # Clean out unwanted fields
    for field in drop_fields:
        if field in metadata.keys():
            del metadata[field]
    return metadata


def find_book_htm(book_folder, metadata_fin):
    book_htm = None
    htm_files = list(book_folder.glob("*.htm"))

    for htm_file in htm_files:
        if metadata_fin["title"] in htm_file.name:
            book_htm = htm_file

    if not book_htm:
        logging.warning(
            f"could not find htm matching title '{metadata_fin['title']}' in metadata. Trying to find htm matching foldername"
        )
        potential_book_htm = (
            book_folder / f"{book_folder.name}.htm"
        )  # example: "20  Ni Mpaari Nraanre Qahira" has "20  Ni Mpaari Nraanre Qahira.htm" has " but meta.json says "(20) Ni Mpaari Nraanre Qahira"
        if potential_book_htm.is_file():
            book_htm = potential_book_htm
        else:
            logging.warning(
                f"could not find htm matching '{book_folder.name}' either. Checking if there's only one htm file"
            )
            if len(htm_files) == 1:
                book_htm = htm_files[0]
            else:
                logging.warning(
                    f"There is not just one htm, there are {len(htm_files)}. Giving up. "
                )

    return book_htm


def check_and_fix_image_caption_pairs_html_quoting(
    image_caption_pairs, book_folder, ids_and_hashes
):
    image_caption_pairs_checked = []
    for image, captions in image_caption_pairs:
        if image not in ids_and_hashes[book_folder.name]:

            unquote_image = unquote(image)
            if unquote_image != image:
                logging.debug(f"{image} unquoted is {unquote_image}")
            if unquote_image in ids_and_hashes[book_folder.name]:
                image = unquote_image
            else:
                return None
        pair = (image, captions)
        image_caption_pairs_checked.append(pair)
    return image_caption_pairs_checked


def story_has_image_caption_matching_issues(image_caption_tuples: list):

    for img, captions in image_caption_tuples:
        if captions is None:
            logging.warning(f"no matching caption for img {img}")
            return True

        if img is None:
            logging.warning(f"no matching img for caption {captions}")
            return True

    return False


def license_is_valid(book_license, valid_licenses):
    if book_license in valid_licenses:
        return True
    else:
        return False


def match_files_with_aws_urls(ids_and_hashes_dict, aws_manifest_csv):
    logging.info(f"Matching IDs and hashes from using csv {aws_manifest_csv}")
    manifest_items = []
    with open(aws_manifest_csv, newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            manifest_items.append(row)

    for bucket_name, file_key in manifest_items:
        base_url = f"https://{bucket_name}.s3.amazonaws.com"
        generated_url = f"{base_url}/{file_key}"
        try:
            folder, filename = file_key.split("/")
        except ValueError:
            logging.debug(
                f"While trying to find aws URLs, no slashes in file_key {file_key}"
            )

            continue

        try:
            matching_item = ids_and_hashes_dict[folder][filename]
        except KeyError:
            folder = unquote_plus(folder)
            filename = unquote_plus(filename)
            matching_item = ids_and_hashes_dict[folder][filename]

        matching_item["web_url"] = generated_url
        matching_item["s3_key"] = file_key
    return ids_and_hashes_dict


def strip_whitespace_from_around_captions(image_caption_pairs):
    stripped_image_caption_pairs = []
    for image, caption_dict in image_caption_pairs:
        for lang in caption_dict:
            caption = caption_dict[lang]
            caption_dict[lang] = caption.strip()

        stripped_image_caption_pair = (image, caption_dict)
        stripped_image_caption_pairs.append(stripped_image_caption_pair)
    return stripped_image_caption_pairs


def remove_languages_with_mostly_whitespace(image_caption_pairs, len_threshold=5):
    lang_captions = defaultdict(list)
    for image, caption_dict in image_caption_pairs:

        for lang in caption_dict:
            caption = caption_dict[lang]
            lang_captions[lang].append(caption)

    langs_to_drop = []
    for lang in lang_captions:
        captions = lang_captions[lang]
        if len("".join(captions)) < len_threshold:
            langs_to_drop.append(lang)

    langs_to_drop = list(set(langs_to_drop))
    if langs_to_drop:
        logging.warning(
            f"Dropping the following languages, which had less than {len_threshold} characters after stripping in the whole translation caption set: {langs_to_drop}"
        )

    fixed_pairs = []
    for image, caption_dict in image_caption_pairs:
        fixed_caption_dict = {}
        for lang in caption_dict:

            if lang not in langs_to_drop:
                fixed_caption_dict[lang] = caption_dict[lang]

        fixed_pair = (image, fixed_caption_dict)
        fixed_pairs.append(fixed_pair)

    return fixed_pairs


def dedupe_based_on_captions(bloom_vist_json):
    """
    UNFINISHED CODE - find stories that have the same captions 
    """
    return bloom_vist_json
    stories = []
    for single_element_list in bloom_vist_json["annotations"]:
        annotation = single_element_list[0]


def collapse_albums_based_on_image_similarity(bloom_vist_json, ids_and_hashes):
    return bloom_vist_json


def collapse_duplicate_albums_based_on_lineage_and_language(
    bloom_vist_json, ids_and_hashes
):
    """
    UNFINISHED CODE - tried to combine albums with the same language together by looking through bookLineage
    """
    return bloom_vist_json

    albums = bloom_vist_json["albums"]

    albums_by_id = {}

    lineage_clusters = []

    # first add them all to the dictionary for convenient access.
    for album in albums:
        album_id = album["id"]

        albums_by_id[album_id] = album
        albums_by_id[album_id]["books_in_lineage"] = album[
            "metadata_from_original_json"
        ]["bookLineage"].split()

        annotations_for_book = []
        for annotation in bloom_vist_json["annotations"]:
            if annotation[0]["album_id"] == album_id:
                annotations_for_book.append(annotation)

        albums_by_id["annotations_for_book"] = annotations_for_book

    # now we get all the ones in the same lineage together
    # how the heck do we do that.
    for album in albums:
        album_id = album["id"]
        album_title = album["title"]
        books_in_lineage = album["metadata_from_original_json"]["bookLineage"].split()
        print(
            f"For album with title {album_title}, there are these books in the lineage: {books_in_lineage}"
        )

        my_lineage_cluster = books_in_lineage.append(album_id)
        my_lineage_cluster = list(set(my_lineage_cluster))

        for lineage_cluster in lineage_clusters:
            intersection = set(lineage_cluster).intersection(set(my_lineage_cluster))
            if intersection:
                lineage_cluster.extend(my_lineage_cluster)

        lineage_clusters.append(my_lineage_cluster)

    print(lineage_clusters)
    return bloom_vist_json


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Take bloom downloads and output SIS JSON"
    )

    parser.add_argument(
        "source",
        # dest="source",
        type=Path,
        default=Path.cwd() / "data" / "bloom_downloads",
        help="directory containing the input files for all the bloom books, defaults to ./data/bloom_downloads",
    )
    parser.add_argument(
        "ids_and_hashes",
        # dest="ids_and_hashes",
        type=Path,
        help="json file containing precomputed ids and hashes",
    )

    parser.add_argument(
        "--out",
        dest="out",
        help="output directory for SIS-format JSON, defaults to ./data/bloom_sis",
        type=Path,
        default=Path.cwd() / "data" / "bloom_sis.json",
    )

    # https://stackoverflow.com/questions/57192387/how-to-set-logging-level-from-command-line
    default_logging_level = "info"
    parser.add_argument(
        "-log",
        "--log",
        default="info",
        help=(
            f"Provide logging level. "
            "Example --log debug', default='{default_logging_level}'"
        ),
    )

    default_license_string = ",".join(OPEN_LICENSES)
    parser.add_argument(
        "--valid_licenses",
        dest="valid_licenses",
        help=f"comma-separated licenses, e.g. 'cc-by-sa,cc-by-nd' defaults to {default_license_string}",
        type=str,
        default=default_license_string,
    )

    default_bucket = "s3://bloom-vist/"
    parser.add_argument(
        "--s3_bucket",
        dest="s3_bucket",
        help=f"s3 bucket where the images can be found, organized by book/image. Defaults to  {default_bucket}",
        type=str,
        default=default_bucket,
    )

    default_aws_manifest = "./aws_manifest.csv"
    parser.add_argument(
        "--aws_manifest_csv",
        dest="aws_manifest_csv",
        help=f"manifest.csv from s3 bucket. Defaults to {default_aws_manifest}",
        type=str,
        default=default_aws_manifest,
    )

    args = parser.parse_args()

    valid_licenses = args.valid_licenses.split(",")

    levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    level = levels.get(args.log.lower())
    if level is None:
        raise ValueError(
            f"log level given: {args.log}"
            f" -- must be one of: {' | '.join(levels.keys())}"
        )

    default_logging_folder = Path.cwd() / "logs"
    default_logging_folder.mkdir(exist_ok=True, parents=True)
    default_logging_path = (
        default_logging_folder
        / f"{datetime.datetime.now().replace(microsecond=0).isoformat()}_bloom_to_vist_out.log"
    )
    logging.basicConfig(
        filename=default_logging_path,
        level=level,
        format="%(filename)s:%(lineno)d -  %(message)s",
    )
    logging.debug("debug messages visible")
    logging.info("info messages visible")
    logging.warning("warning messages visible")
    logging.error("error messages are visible")
    logging.critical("error messages are visible")

    logging.warning(f"VALID LICENSES: {valid_licenses}")

    with open(args.ids_and_hashes, "r") as ids_and_hashes_fp:
        ids_and_hashes = json.load(ids_and_hashes_fp)

    ids_and_hashes = match_files_with_aws_urls(
        ids_and_hashes_dict=ids_and_hashes, aws_manifest_csv=args.aws_manifest_csv
    )

    bloom_downloads = args.source

    # Each Bloom book is in its own folder. Ideally.
    book_folders = [subdir for subdir in bloom_downloads.iterdir() if subdir.is_dir()]
    successfully_parsed_books = []  # used to calculate statistics later.

    bloom_images = []  # a list of dicts
    bloom_albums = []  # a list of dicts
    bloom_annotations = []  # a list of 1-element lists, each containing a dict.

    for book_folder in tqdm(book_folders):
        logging.info("***************")
        logging.info(f"parsing book '{book_folder}'")
        book_files = list(book_folder.iterdir())
        logging.debug(f"there are {len(book_files)} files in the folder")
        image_files = get_image_files_in_folder(book_folder=book_folder)
        logging.debug(f"there are {len(image_files)} images in the folder")

        mpath = book_folder / "meta.json"
        if mpath.is_file():
            try:
                metadata_fin = parse_metadata(mpath)
            except json.decoder.JSONDecodeError:
                logging.warning("could not parse meta.json. Skipping")
                continue
        else:
            logging.warning("couldn't find meta.json. Skipping")
            continue

        ###########################
        # Check license.
        book_license = metadata_fin["license"]

        if license_is_valid(book_license, valid_licenses):
            logging.debug(f"Checked license, and it is valid")
        else:
            logging.warning(
                f"License {book_license} not in {args.valid_licenses}. Skipping."
            )
            continue

        ###########################
        # Find the book htm file
        book_htm = find_book_htm(book_folder, metadata_fin)

        if not book_htm:
            logging.warning(f"couldn't find book htm. Skipping")
            continue

        if not image_files:
            logging.warning(f"could not find image files. Skipping")
            continue

        # load the precomputed hashes and ids.
        try:
            file_ids_and_hashes_for_folder = ids_and_hashes[book_folder.name]
            logging.debug(
                f"for book named {book_folder.name} we have {len(file_ids_and_hashes_for_folder)} precomputed ids and hashes"
            )
        except KeyError:
            logging.warning(
                f"could not find ids/hashes for {book_folder.name}, skipping"
            )
            continue

        htm_book_metadata = parse_book_htm_for_metadata(book_htm)

        # parse htm for matching image _links_ and text
        image_caption_pairs = parse_matching_images_and_captions_from_htmfile(book_htm)
        logging.info(f"Parsed htm with {len(image_caption_pairs)} image/caption pairs")

        # check if the story has any mismatches
        if story_has_image_caption_matching_issues(image_caption_pairs):
            logging.warning(f"Some images seem to lack captions. Skipping.")
            continue

        successfully_parsed_books.append(book_folder.name)

        ##############################
        # match images/captions from htm with precomputed hashes/ids,
        # then initialize dicts for the images, the "annotations" (captions), and the "album"

        # check if we can find ids/hashes for the images, and fix url quoting.
        # Here's a fun one! In the HTML, the file is bird%20meeting.png ,
        # but in the file system, and therefore in my json, it is bird meeting.png , with a space.
        # So I guess when trying to find that file I gotta do something like https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python
        image_caption_pairs = check_and_fix_image_caption_pairs_html_quoting(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            ids_and_hashes=ids_and_hashes,
        )

        image_caption_pairs = strip_whitespace_from_around_captions(
            image_caption_pairs=image_caption_pairs
        )

        image_caption_pairs = remove_languages_with_mostly_whitespace(
            image_caption_pairs=image_caption_pairs
        )

        if image_caption_pairs is None:
            # that means there was one we couldn't fix.
            logging.warning(
                f"There was an image we couldn't find the id for. Skipping."
            )
            continue

        if len(image_caption_pairs) == 0:
            # that means there was one we couldn't fix.
            logging.warning(
                f"Somehow the image/caption pairs is length zero. Skipping."
            )
            continue

        ## ALBUMS:
        # in VIST, albums are collections or sets of images, in some sequential order.
        # They don't have associated captions, those come later in "stories"
        vist_album_for_book = create_vist_album_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            htm_book_metadata=htm_book_metadata,
        )

        ## IMAGES
        # In VIST, we've got an "image", hosted on flickr.
        # Each of them it has a unique ID, referenced in
        vist_images_for_book = create_vist_images_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            ids_and_hashes=ids_and_hashes,
            vist_album=vist_album_for_book,
            s3_bucket=args.s3_bucket,
        )

        ## STORIES:
        # Stories are a concept that shows up in VIST, separate from "album."
        # Basically an "album" is a set of pictures,
        # then a volunteer comes and begins adding captions to that set.
        # Together the images and captions form a "story".
        # You can have multiple "stories" told about each album of pictures.
        # Each of these has its own unique ID.
        # We effectively have one "story" per book, one per translation.
        # stories_for_book = create_vist_stories_for_book(
        #     image_caption_pairs=image_caption_pairs,
        #     book_folder=book_folder,
        #     metadata_fin=metadata_fin,
        #     ids_and_hashes=ids_and_hashes,
        #     vist_album=vist_album_for_book,
        #     book_htm=book_htm,
        # )

        ## ANNOTATIONS
        # In VIST, these are the captions added by a volunteer, each associated with some image.
        # You can often have different captions added by different volunteers.
        vist_annotations_for_book = create_vist_annotations_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            ids_and_hashes=ids_and_hashes,
            vist_album=vist_album_for_book,
        )

        bloom_albums.append(vist_album_for_book)
        bloom_images.extend(vist_images_for_book)
        bloom_annotations.extend(vist_annotations_for_book)

        logging.info(f"Parsed {book_folder.name} successfully")

    logging.info(
        f"successfully parsed: {len(successfully_parsed_books)} out of {len(book_folders)}"
    )

    bloom_vist_json = {
        "albums": bloom_albums,
        "images": bloom_images,
        "annotations": bloom_annotations,
        "utc_creation_date": str(datetime.datetime.utcnow()),
    }

    # bloom_vist_json = collapse_duplicate_albums_based_on_lineage_and_language(
    #     bloom_vist_json, ids_and_hashes
    # )

    # bloom_vist_json = collapse_albums_based_on_image_similarity(
    #     bloom_vist_json, ids_and_hashes
    # )

    # bloom_vist_json = dedupe_based_on_captions(bloom_vist_json)

    with open(args.out, "w") as outf:
        logging.warning(f"writing results to {args.out}")
        json.dump(bloom_vist_json, outf)

    # # sample_book = random.choice(book_folders)

    # sample_book = (
    #     bloom_downloads / "Chuskit Goes to School!"
    # )  # https://bloomlibrary.org/book/WogbtL0C1D
    # sample_book_contents = list(sample_book.iterdir())
    # # print(sample_book_contents)

    # image_paths = [
    #     img for img in sample_book_contents if img.name.endswith(BLOOM_IMAGE_FORMATS)
    # ]
    # # print(image_paths)

    # vist_format_image_array = []  # we want to make a VIST-formatted array of dicts.

    # for image_path in image_paths:
    #     image_dict = initialize_dict_for_image_path(image_path=image_path)
    #     print(image_dict)

