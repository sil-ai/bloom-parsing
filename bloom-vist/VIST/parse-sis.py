from __future__ import annotations
from fileinput import filename
import json
import logging
from pathlib import Path
from collections import Counter
import argparse
import urllib.request
import random


def write_split_urls(sis_json, split="train"):

    # print(sis_json.keys())
    # valid_keys = []

    imgurls = parse_urls_from_sis_json(sis_json)

    print(Counter(valid_keys))
    valid_keys = set(valid_keys)
    print(valid_keys)

    outfile = Path.cwd() / f"split_imgurls.txt"

    outfile.write_text("\n".join(imgurls))


def parse_urls_from_sis_json(sis_json):
    imgurls = []
    for image in sis_json["images"]:
        for imagekey in image.keys():
            if "url" in imagekey:
                imgurl = image[imagekey]
                imgurls.append(imgurl)
                # valid_keys.append(imagekey)
    return imgurls


def download_images(imgurls, download_dir):
    downloaded_images_successfully = True
    # https://towardsdatascience.com/how-to-download-an-image-using-python-38a75cfa21c

    # TODO: catch the error in this function and cleanup downloaded files, then return "false",
    try:
        for imgurl in imgurls:
            filename = download_dir / Path(imgurl).name
            if not filename.exists():
                urllib.request.urlretrieve(imgurl, filename)
    except urllib.error.HTTPError:
        print(f"error downloading image {imgurl}")
        downloaded_images_successfully = False

    return downloaded_images_successfully


def pull_out_small_sample(
    sis_json, out_filename, albums_count=100, images_split_dir=Path.cwd()
):

    # iterate over images, albums, and annotations
    # pull out some albums.
    # albums = sis_json["albums"][
    #     :albums_count
    # ]  # OK if shorter. https://stackoverflow.com/questions/41284418/get-first-n-items-of-list-ok-if-list-is-shorter

    selected_albums = []
    sis_albums_shuffled = sis_json["albums"]
    random.shuffle(sis_albums_shuffled)

    i = 0
    while len(selected_albums) < albums_count and i < len(sis_albums_shuffled):
        print(f"We have {len(selected_albums)} albums selected so far, i={i}")
        candidate_album = sis_albums_shuffled[i]

        candidate_album_images = [
            x for x in sis_json["images"] if x["album_id"] == candidate_album["id"]
        ]
        imgurls = []
        for image in candidate_album_images:
            for imagekey in image.keys():
                if "url" in imagekey:
                    imgurl = image[imagekey]
                    imgurls.append(imgurl)

        print(
            f"downloading {len(imgurls)} images for candidate album {candidate_album['title']} with ID {candidate_album['id']}"
        )
        downloaded_images_successfully = download_images(
            imgurls=imgurls, download_dir=images_split_dir
        )
        if downloaded_images_successfully:
            selected_albums.append(candidate_album)
        else:
            print(
                "ERROR: couldn't download all the images for this album successfully. Not adding it to the sample"
            )
        i = i + 1

    selected_album_ids = [x["id"] for x in selected_albums]
    for i, album in enumerate(selected_albums):
        print(f"album {i} has id {album['id']}")
        # selected_albums.append(album)

    data_sample = {
        "albums": selected_albums,
        "images": [],
        "annotations": [],
        "type": sis_json["type"],
        "info": sis_json["info"],
    }
    # selected_album_ids = [x["id"] for x in selected_albums]
    # print(selected_album_ids)

    # for key in ["images", "annotations"]:
    sis_images = sis_json["images"]  # list of dictionaries.

    selected_images = [x for x in sis_images if x["album_id"] in selected_album_ids]

    sis_annotations = sis_json[
        "annotations"
    ]  # list of 1-element lists, and the one-element lists contain dictionaries.
    selected_annotations = [
        x for x in sis_annotations if x[0]["album_id"] in selected_album_ids
    ]

    # print(f"Number of annotations read: {len(sis_annotations)}")

    # lengths = []
    # for annotation in sis_annotations:
    #     lengths.append(len(annotation))
    # print(set(lengths))    # prints {1}

    data_sample["images"] = selected_images
    data_sample["annotations"] = selected_annotations

    print(
        f"writing sample: {len(data_sample['albums'])} albums, {len(data_sample['images'])} images, and {len(data_sample['annotations'])} annotations to {out_filename}"
    )

    with open(out_filename, "w") as jf:
        json.dump(data_sample, jf)


if __name__ == "__main__":
    splits = ["train", "val", "test"]
    sample_count = 5
    sample_out_dir = Path.cwd() / f"VIST_SIS_sample_{sample_count}" / "sis"
    sample_out_dir.mkdir(exist_ok=True, parents=True)

    images_dir = sample_out_dir / "images"
    images_dir.mkdir(exist_ok=True, parents=True)

    # https://dusty.phillips.codes/2018/08/13/python-loading-pathlib-paths-with-argparse/
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vist_dir",
        type=Path,
        default=Path(__file__).absolute().parent / "sis",
        help="Path to the data directory 'sis' containing annotation json files",
    )

    # parser.add_argument(
    #     "--samples_count",
    #     type=int,
    #     default=100,
    #     help="Number of samples"
    # )

    p = parser.parse_args()
    print(f"reading annotations from {p.vist_dir}")

    for split in splits:
        out_filename = sample_out_dir / f"{split}.story-in-sequence.json"
        print(f"doing split {split}")

        # load in the original
        json_file_path = p.vist_dir / "sis" / f"{split}.story-in-sequence.json"
        print(f"read annotations from {json_file_path}")
        with open(json_file_path) as jsf:
            sis_json = json.load(jsf)

            # pull out URLs
            # write_split_urls(sis_json, split=split)

            # pull out a sample
            images_split_dir = images_dir / split
            images_split_dir.mkdir(exist_ok=True, parents=True)
            pull_out_small_sample(
                sis_json,
                out_filename=out_filename,
                albums_count=sample_count,
                images_split_dir=images_split_dir,
            )

            # download the images for that sample.
            # https://github.com/lichengunc/vist_api/blob/f89d1b52c45c6b3ae6ac39cc44f6f48744e6dc1a/vist.py#L120 expects it to be in
            # images_dir/split

            # download_images(json_file_path=out_filename, download_dir=images_split_dir)

