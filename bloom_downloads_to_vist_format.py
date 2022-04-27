import argparse
from pathlib import Path
import random
import uuid
import json
import logging
from attr import attr
from bs4 import BeautifulSoup, PageElement
import precompute_file_uuids_and_hashes


# https://stackoverflow.com/questions/4292029/how-to-get-a-list-of-file-extensions-for-a-general-file-type
BLOOM_IMAGE_FORMATS = (".jpg", ".png")  # contentful images, excluding svg on purpose.


def initialize_dict_for_image_path(image_path: Path, precomputed_id: None):
    if precomputed_id is None:
        id = str(uuid.uuid4())
    else:
        id = precomputed_id

    image_dict = {
        "datetaken": "",
        "license": "",
        "title": "",
        "text": "",
        "album_id": "",  # TODO: associate
        "longitude": "0",
        "url_o": str(image_path),
        "secret": "",
        "media": "photo",
        "latitude": "0",
        "id": id,
        "tags": "",  # todo: pull from other data?
    }
    return image_dict

    # "datetaken": "2007-07-02 03:54:30",
    # "license": "5",
    # "title": "Fourth of July prerequisite",
    # "text": "",
    # "album_id": "72157600601428727",
    # "longitude": "0",
    # "url_o": "https://farm2.staticflickr.com/1125/694227468_f6c433d7d8_o.jpg",
    # "secret": "0745b37a62",
    # "media": "photo",
    # "latitude": "0",
    # "id": "694227468",
    # "tags": "family fun fireworks bbq fourthofjuly"


def get_image_files_in_folder(book_folder):
    return [
        img for img in book_folder.iterdir() if img.name.endswith(BLOOM_IMAGE_FORMATS)
    ]


def parse_matching_images_and_captions_from_htmfile(htmfile_path):
    story = (
        []
    )  # storing the img names from img elements, e.g. 21-chuskit-goes-to-school_Page_01_Image_0001.png

    # print(f"thingamajig: {htmfile_path}")
    with open(htmfile_path) as file:
        page = file.read()

    soup = BeautifulSoup(page, "html.parser")

    # MAYBE: cross-reference with metadata?
    # booktitle = soup.find("title")
    # print(f"book title: {booktitle.text}")

    divs = soup.findAll("div")
    # topics = soup.select()
    pages = soup.find_all("div", class_="numberedPage")
    print(f"pages count: {len(pages)}")
    # print(f"first page: {pages[0]}")

    # HOW TO MATCH IMAGES TO TEXT
    # if they're in the same numberedPage that's easy.
    # But sometimes you have image on one page and captions on the next??
    # Do we, like, make tuples, and then if there's
    # (img, captions)
    # (img, None)
    # (None, captions)
    # then we collapse the two together?
    img_caption_pairs = []

    for page in pages:
        logging.debug(f"xxxxxxxxxxxxxxxxxxx parsing page xxxxxxxxxxxxxxxxxxxxxxxxxx")
        tg_divs = page.find_all("div", class_="bloom-translationGroup")

        imgs = page.find_all("img")
        logging.debug(f"found {len(imgs)} imgs in the page: {imgs}")
        logging.debug(f"found {len(tg_divs)} translation groups in the page")
        # turns out you sometimes have, like, imgs on their own page followed by a caption.

        # if len(imgs) != len(tg_divs):
        #     logging.debug(
        #         f"number of translation groups does not match number of images for {imgs}. Skipping"
        #     )
        #     continue

        if imgs:
            img = imgs[0]
            img_src = img["src"]
            logging.debug(f"img_src: {img_src}")
        else:
            img_src = None

        if tg_divs:
            tg_div = tg_divs[0]
            captions = parse_translation_group(tg_div)
            logging.debug(f"captions for tg_div: {captions}")
        else:
            captions = None

        img_caption_pairs.append((img_src, captions))

    for pair in img_caption_pairs:
        print(pair)
    print(htmfile_path)
    # exit()

    # exit()
    return story
    i = 0  # TODO: figure out what this index is for -CDL
    BookText = {}
    Images = {}

    for div in divs:
        if div.has_attr("data-book") and "topic" in div.get("data-book"):
            htmltopic = div.text.strip()
            print(f"found the topic div: {htmltopic}")

        # Get a page
        if div.has_attr("class") and "numberedPage" in div.get("class"):
            page_num = int(div.get("data-page-number"))
            print(f"found a numberedPage with data-page-number {page_num}")

        # Get the images

        # Get the book text
        if div.has_attr("class") and "bloom-translationGroup" in div.get("class"):
            captions = parse_translation_group(div)

            if len(captions.keys()) > 0:
                BookText[i] = captions

            i += 1

    return BookText


def parse_translation_group(tg_div):
    entry = {}
    subdivs = tg_div.find_all(
        "div", {"lang": True}  # finds subdivs with this attribute.
    )

    for subdiv in subdivs:
        if (
            subdiv.has_attr("lang")
            and subdiv.get("lang") != "*"
            and subdiv.get("lang") != ""
            and subdiv.get("lang") != "z"  # always empty, not a valid code
        ):
            texts = subdiv.findAll("p")

            book_text = ""
            for text in texts:
                if book_text != "":
                    book_text += "\n" + text.get_text()
                else:
                    book_text = text.get_text()
            entry[subdiv.get("lang")] = book_text
    return entry


def parse_metadata(mpath):

    with open(mpath) as metadata:
        metadata = json.load(metadata)

    return metadata


def find_book_htm(book_folder, metadata_fin):
    book_htm = None
    htm_files = list(book_folder.glob("*.htm"))

    for htm_file in htm_files:
        if metadata_fin["title"] in htm_file.name:
            book_htm = htm_file

    if not book_htm:
        logging.warning(
            f"could not find htm matching title in metadata. Trying to find htm matching foldername"
        )
        potential_book_htm = (
            book_folder / f"{book_folder.name}.htm"
        )  # example: "20  Ni Mpaari Nraanre Qahira" has "20  Ni Mpaari Nraanre Qahira.htm" has " but meta.json says "(20) Ni Mpaari Nraanre Qahira"
        if potential_book_htm.is_file():
            book_htm = potential_book_htm
        else:
            logging.warning(f"could not find htm matching foldername either")
    return book_htm


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
        default=Path.cwd() / "data" / "bloom_sis",
    )

    # https://stackoverflow.com/questions/57192387/how-to-set-logging-level-from-command-line
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=("Provide logging level. " "Example --log debug', default='warning'"),
    )

    args = parser.parse_args()

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
            f"log level given: {options.log}"
            f" -- must be one of: {' | '.join(levels.keys())}"
        )

    logging.basicConfig(level=level, format="%(filename)s:%(lineno)d -  %(message)s")
    logging.debug("debug messages visible")
    logging.info("info messages visible")
    logging.warning("warning messages visible")

    with open(args.ids_and_hashes, "r") as ids_and_hashes_fp:
        ids_and_hashes = json.load(ids_and_hashes_fp)

    bloom_downloads = args.source

    book_folders = [subdir for subdir in bloom_downloads.iterdir() if subdir.is_dir()]
    for book_folder in book_folders:
        logging.info("***************")
        logging.info(f"parsing book {book_folder}")
        book_files = list(book_folder.iterdir())
        logging.debug(f"there are {len(book_files)} files in the folder")
        image_files = get_image_files_in_folder(book_folder=book_folder)
        logging.debug(f"there are {len(image_files)} images in the folder")

        mpath = book_folder / "meta.json"
        if mpath.is_file():
            try:
                metadata_fin = parse_metadata(mpath)
            except json.decoder.JSONDecodeError:
                logging.warning(
                    "could not parse meta.json. Skipping^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
                )
                continue
        else:
            logging.warning("couldn't find meta.json. Skipping")
            continue

        book_htm = find_book_htm(book_folder, metadata_fin)
        if not book_htm:
            logging.warning(f"couldn't find book htm. Skipping")
            continue

        if not image_files:
            logging.warning(f"could not find image files. Skipping")
            continue

        # get the precomputed hashes and ids.
        try:
            file_ids_and_hashes_for_folder = ids_and_hashes[book_folder.name]
            logging.debug(
                f"for book named {book_folder.name} we have {len(file_ids_and_hashes_for_folder)} precomputed ids and hashes"
            )
        except KeyError:
            logging.warning(
                f"could not find ids/hashes for {book_folder.name}, skipping.&&&&&&&&&&&&&"
            )
            continue

        # parse htm for matching image _links_ and text
        story = parse_matching_images_and_captions_from_htmfile(book_htm)
        logging.info(f"Parsed story with {len(story)} image/caption pairs")

        # get the ids/hashes for image _files_
        image_dicts = []
        for image_file in image_files:
            try:
                hash = ids_and_hashes[book_folder.name][image_file.name]["hash"]
                id = ids_and_hashes[book_folder.name][image_file.name]["id"]
            except KeyError:
                logging.warning(
                    f"Could not find id/hash for {image_file.name} in {book_folder.name}. Calculating a new ID/Hash"
                )
                hash = precompute_file_uuids_and_hashes.calculate_hash_for_file(
                    image_file
                )
                id = str(uuid.uuid4())

            image_dict = initialize_dict_for_image_path(
                image_path=image_file, precomputed_id=id
            )
            image_dicts.append(image_dict)

        logging.debug(f"{image_dicts[0]}")

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

