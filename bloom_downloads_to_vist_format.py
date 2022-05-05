import argparse
from collections import defaultdict
from pathlib import Path
import random
import uuid
import json
import logging
from bs4 import BeautifulSoup, PageElement
import precompute_file_uuids_and_hashes
from urllib.parse import unquote, urlparse, quote_plus
from tqdm import tqdm
import datetime
import langcodes

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


def create_vist_story_for_book(
    image_caption_pairs, book_folder, metadata_fin, ids_and_hashes, vist_album, book_htm
):
    """
    'story' is when you've got captions for an album. in VIST you might have had an album of images,
    and then have that album get turned into a story by volunteers more than once. 
    So for one album you might have multiple stories. In our case we assume one story per htm. 
    Thus we can safely use the uuid of the htm to be our story ID. 
    If we run into multiple 'stories' per book we'd have to rethink this, 
    """
    story_id = ids_and_hashes[book_folder.name][book_htm.name][
        "id"
    ]  # it is a uuid, it is unique to the story. #TODO: uuid3 for story ID?
    story = {
        "story_id": story_id,
        "image_caption_pairs": image_caption_pairs,
    }

    return story


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
        web_url = calculate_web_url_given_local_path(
            s3_bucket=s3_bucket, local_path=local_image_path
        )

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
    image_caption_pairs, book_folder, metadata_fin, ids_and_hashes, vist_album, story
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
    for image, captions in image_caption_pairs:
        image_id = ids_and_hashes[book_folder.name][image]["id"]
        album_id = vist_album["id"]
        # print(captions)

        annotation = [
            {
                # "original_text": "The local parish holds a craft show each year.", # TODO: annotation original_text
                "album_id": album_id,
                "photo_flickr_id": image_id,  # TODO: annotation photo_flickr_id
                # "setting": "first-2-pick-and-tell", # TODO: annotation setting
                # "worker_id": "FJROI8NWDRIPAM1", # TODO: annotation worker_id
                "story_id": story["story_id"],
                # "tier": "story-in-sequence",  # TODO: tier
                # "worker_arranged_photo_order": 0, # TODO: worker_arranged_photo_order
                "text": captions,  # NOTE: this is different than VIST format!
                # "storylet_id": "227650", # TODO: annotation storylet id
            }
        ]

        annotations.append(annotation)
    return annotations


def create_vist_album_for_book(image_caption_pairs, book_folder, metadata_fin):

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
        "title": f"{book_folder.name}",  # todo: set album title from metatada?
        # "farm": "",  # TODO: album farm
        # "date_update": "",  # TODO: album date_update
        # "primary": "",  # TODO: album primary
        # "server": "",  # TODO: album server
        # "date_create": "",  # TODO: album date_create
        "photos": f"{len(image_caption_pairs)}",
        # "secret": "",  # TODO: album secret
        # "owner": "",  # TODO: album owner
        # "vist_label": "",  # TODO: album vist_label
        "id": str(uuid.uuid4()),
        "license": metadata_fin["license"],  # NOTE: not in original VIST format
    }
    return vist_album


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
    # print(f"book title: {booktitle.text}")

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
            logging.debug(f"img_src: {img_src}")
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

    return img_caption_tuples


# def recursive_get_text(element):

#     print(f"parsing {element} for text")
#     text = element.get_text()

#     if text == "" and element.children:
#         print(f"couldn't find text but there's kids, let's go down a level")
#         for child in element.children:
#             print(f" CHILD: {child}")
#             text = text + recursive_get_text(child)

#     return text


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


def check_and_fix_image_caption_pairs(image_caption_pairs, book_folder, ids_and_hashes):
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
            logging.debug(f"no matching img for captions {captions}")
            return True

        if img is None:
            logging.debug(f"no matching caption for img {img}")
            return True

    return False


def license_is_valid(book_license, valid_licenses):
    if book_license in valid_licenses:
        return True
    else:
        return False


if __name__ == "__main__":
    bloom_vist = {
        "en": {"images": [], "albums": [], "annotations": []},
        "kyr": {"images": [], "albums": [], "annotations": []},
        "hni": {"images": [], "albums": [], "annotations": []},
    }

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

    logging.basicConfig(
        filename=f"logs/{datetime.datetime.now().replace(microsecond=0).isoformat()}_bloom_to_vist_out.log",
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

    bloom_downloads = args.source

    book_folders = [subdir for subdir in bloom_downloads.iterdir() if subdir.is_dir()]
    successfully_parsed_books = []

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

        # parse htm for matching image _links_ and text
        image_caption_pairs = parse_matching_images_and_captions_from_htmfile(book_htm)
        logging.info(f"Parsed htm with {len(image_caption_pairs)} image/caption pairs")

        # check if the story has any mismatches
        if story_has_image_caption_matching_issues(image_caption_pairs):
            logging.warning(f"Some images seem to lack captions. Skipping.")
            continue

        successfully_parsed_books.append(book_folder.name)

        # check if we can find ids/hashes for the images, and fix url quoting.
        # Here's a fun one! In the HTML, the file is bird%20meeting.png ,
        # but in the file system, and therefore in my json, it is bird meeting.png , with a space.
        # So I guess when trying to find that file I gotta do something like https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python
        image_caption_pairs = check_and_fix_image_caption_pairs(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            ids_and_hashes=ids_and_hashes,
        )
        if image_caption_pairs is None:
            # that means there was one we couldn't fix.
            logging.warning(
                f"There was an image we couldn't find the id for. Skipping."
            )
            continue

        ##
        # match images/captions from htm with precomputed hashes/ids,
        # then initialize dicts for the images, the "annotations" (captions), and the "album"

        vist_album_for_book = create_vist_album_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
        )
        bloom_albums.append(vist_album_for_book)

        story_for_book = create_vist_story_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            ids_and_hashes=ids_and_hashes,
            vist_album=vist_album_for_book,
            book_htm=book_htm,
        )

        vist_images_for_book = create_vist_images_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            ids_and_hashes=ids_and_hashes,
            vist_album=vist_album_for_book,
            s3_bucket=args.s3_bucket,
        )

        vist_annotations_for_book = create_vist_annotations_for_book(
            image_caption_pairs=image_caption_pairs,
            book_folder=book_folder,
            metadata_fin=metadata_fin,
            ids_and_hashes=ids_and_hashes,
            vist_album=vist_album_for_book,
            story=story_for_book,
        )

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

