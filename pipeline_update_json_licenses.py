# Dan says:
# make sure that all the "license" entries in the datasets should be re-licensed as cc-by-nc
# except for those that are cc-by-nd, cc-by-nc-nd, or cc-by-sa.
# cc-by-sa and cc-by-nc-nd should be left unchanged,
# and cc-by-nd should be changed to cc-by-nc-nd.
# This is allowed by our terms of use on Bloom
# and the preferred (and more simplified) structure of licensing that was clarified internally
# (where we want most things NC where possible. That is, all the data should be released as non-commercial and non-derivative
# Colin: OK, the license fields are on the album fields.
# jq .albums[1] bloom_vist_june15_deduped_june21_langfiltered_june22_with_storylets.json
#
from pathlib import Path
import json
import argparse
import uuid
import datetime


def update_bloom_vist_dict_licenses(bloom_vist_dict):
    updated_bloom_vist_dict = bloom_vist_dict
    new_albums = []
    albums = bloom_vist_dict["albums"]
    for album in albums:
        license = album["license"]
        if license == "cc-by-sa":
            pass
        elif license == "cc-by-nc-nd":
            pass
        elif license == "cc-by-nd":
            license = "cc-by-nc-nd"
        else:
            license = "cc-by-nc"

        album["license"] = license
        new_albums.append(album)

    updated_bloom_vist_dict["albums"] = new_albums

    return updated_bloom_vist_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update all the license entries in a JSON"
    )
    parser.add_argument(
        "path_to_bloom_vist_json",
        # dest="source",
        type=Path,
        default=Path(
            "data/bloom_vist_june15_deduped_june21_langfiltered_june22_with_storylets.json"
        ),
        help="json to update licenses",
    )

    args = parser.parse_args()

    with open(str(args.path_to_bloom_vist_json)) as bvf:
        bloom_vist_dict = json.load(bvf)

    updated_bloom_vist_dict = update_bloom_vist_dict_licenses(bloom_vist_dict)
    out_stem = args.path_to_bloom_vist_json.stem
    append_string = "_licenseupdated"
    if append_string not in str(args.path_to_bloom_vist_json):
        output_json_path = args.path_to_bloom_vist_json.parent / (
            args.path_to_bloom_vist_json.stem + f"{append_string}.json"
        )
    else:
        output_json_path = args.path_to_bloom_vist_json
    updated_bloom_vist_dict["licenses updated"] = (str(datetime.datetime.utcnow()),)

    with open(output_json_path, "w") as fixed_file:
        json.dump(updated_bloom_vist_dict, fixed_file)
