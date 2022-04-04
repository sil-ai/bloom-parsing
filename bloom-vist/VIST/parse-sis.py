from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import argparse


def write_split_urls(sis_json, split="train"):

    print(sis_json.keys())
    # valid_keys = []

    imgurls = []
    for image in sis_json["images"]:
        for imagekey in image.keys():
            if "url" in imagekey:
                imgurl = image[imagekey]
                imgurls.append(imgurl)
                # valid_keys.append(imagekey)

    print(Counter(valid_keys))
    valid_keys = set(valid_keys)
    print(valid_keys)

    outfile = Path.cwd() / f"split_imgurls.txt"

    outfile.write_text("\n".join(imgurls))


def pull_out_small_sample(sis_json, out_filename, albums_count=100):

    # iterate over images, albums, and annotations
    # pull out some albums.
    albums = sis_json["albums"][
        :albums_count
    ]  # OK if shorter. https://stackoverflow.com/questions/41284418/get-first-n-items-of-list-ok-if-list-is-shorter

    selected_albums = []
    for i, album in enumerate(albums):
        print(f"album {i} has id {album['id']}")
        selected_albums.append(album)

    data_sample = {
        "albums": selected_albums,
        "images": [],
        "annotations": [],
    }
    selected_album_ids = [x["id"] for x in selected_albums]
    # print(selected_album_ids)
    # exit()

    # for key in ["images", "annotations"]:
    sis_images = sis_json["images"]  # list of dictionaries.

    selected_images = [x for x in sis_images if x["album_id"] in selected_album_ids]

    sis_annotations = sis_json[
        "annotations"
    ]  # list of 1-element lists, and the one-element lists contain dictionaries.
    selected_annotations = [
        x for x in sis_annotations if x[0]["album_id"] in selected_album_ids
    ]

    print(f"Number of annotations read: {len(sis_annotations)}")

    # lengths = []
    # for annotation in sis_annotations:
    #     lengths.append(len(annotation))
    # print(set(lengths))    # prints {1}

    data_sample["images"] = selected_images
    data_sample["annotations"] = selected_annotations

    print(f"writing {len(data_sample['albums'])} albums to {out_filename}")
    print(f"writing {len(data_sample['images'])} images to {out_filename}")
    print(f"writing {len(data_sample['annotations'])} annotations to {out_filename}")

    with open(f"{out_filename}", "w") as jf:
        json.dump(data_sample, jf)


if __name__ == "__main__":
    splits = ["train", "val", "test"]
    sample_count = 100

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
    print(p.vist_dir, type(p.vist_dir))

    for split in splits:
        print(f"doing split {split}")

        # load in the original
        json_file_path = p.vist_dir / "sis" / f"{split}.story-in-sequence.json"
        with open(json_file_path) as jsf:
            sis_json = json.load(jsf)

            # pull out URLs
            # write_split_urls(sis_json, split=split)

            # pull out a sample
            sample_out_dir = Path.cwd() / f"VIST_SIS_sample_{sample_count}"
            sample_out_dir.mkdir(exist_ok=True, parents=True)
            pull_out_small_sample(
                sis_json,
                out_filename=sample_out_dir / f"{split}.story-in-sequence.json",
                albums_count=sample_count,
            )

