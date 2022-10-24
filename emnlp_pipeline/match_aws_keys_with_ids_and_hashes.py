from pathlib import Path
import json
import csv
from urllib.parse import unquote_plus

# THIS FILE IS FOR TESTING


def match_files_with_aws_urls(ids_and_hashes_dict, aws_manifest_csv):
    # print(f"Running with {ids_and_hashes_json} and {aws_manifest_csv}")

    manifest_items = []
    with open(aws_manifest_csv, newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            # print(", ".join(row))
            manifest_items.append(row)

    # print(f"id, hash, url")
    print(len(manifest_items))

    for bucket_name, file_key in manifest_items:
        # print(file_key)
        base_url = f"https://{bucket_name}.s3.amazonaws.com/"
        generated_url = f"{base_url}/{file_key}"
        try:
            folder, filename = file_key.split("/")
        except ValueError:
            print(f"no slashes in file_key {file_key}")

            continue

        # print(folder, filename)
        try:
            matching_item = ids_and_hashes_dict[folder][filename]
            # ids_and_hashes_dict[folder][filename]["web_url"] = generated_url
            # print(ids_and_hashes_dict[folder][filename]["web_url"])
            # print("LINE 40")
        except KeyError:
            folder = unquote_plus(folder)
            filename = unquote_plus(filename)
            matching_item = ids_and_hashes_dict[folder][filename]
            # ids_and_hashes_dict[folder][filename]["web_url"] = generated_url
            # print(
            #     ids_and_hashes_dict[unquote_plus(folder)][unquote_plus(filename)][
            #         "web_url"
            #     ]
            # )

        matching_item["web_url"] = generated_url
        matching_item["s3_key"] = file_key
    print(matching_item)
    return ids_and_hashes_dict


if __name__ == "__main__":
    ids_and_hashes_json = Path.cwd() / "ids_and_hashes.json"
    aws_manifest_csv = Path.cwd() / "aws_manifest.csv"

    with open(ids_and_hashes_json) as idnhjf:
        ids_and_hashes_dict = json.load(idnhjf)
        # print(ids_and_hashes_dict)
    ids_and_hashes_dict = match_files_with_aws_urls(
        ids_and_hashes_dict=ids_and_hashes_dict, aws_manifest_csv=aws_manifest_csv
    )
    # print(ids_and_hashes_dict)
    with open("ids_and_hashes_matched_with_s3_keys_and_urls.json", "w") as testf:
        json.dump(ids_and_hashes_dict, testf)
