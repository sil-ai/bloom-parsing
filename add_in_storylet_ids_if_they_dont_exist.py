from pathlib import Path
import json
import argparse
import uuid

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Look through bloom VIST json files and add storylet ID"
    )

    parser.add_argument(
        "folder_with_jsons",
        # dest="source",
        type=Path,
        default=Path("splitting/"),
        help="folder full of bloom JSON files",
    )

    args = parser.parse_args()

    json_paths = list(args.folder_with_jsons.glob("*.json"))
    print(json_paths)

    for json_path in json_paths:
        print(f"loading {json_path}")
        with open(json_path, "r") as json_file:
            bloom_vist_dict = json.load(json_file)
            print(bloom_vist_dict["annotations"][0])
            for i, annotation in enumerate(bloom_vist_dict["annotations"]):
                if "storylet_id" in annotation[0].keys():
                    pass
                else:
                    # generate a new one.
                    story_id = annotation[0]["story_id"]
                    worker_arranged_photo_order = annotation[0][
                        "worker_arranged_photo_order"
                    ]

                    string_that_should_be_unique = (
                        f"{story_id}{worker_arranged_photo_order}"
                    )

                    storylet_id = uuid.uuid3(
                        uuid.UUID(story_id), str(worker_arranged_photo_order)
                    )
                    # storylet_id = str(i)
                    print(storylet_id)
                    annotation[0]["storylet_id"] = str(storylet_id)

            # print(bloom_vist_dict["annotations"][0])
            output_path = json_path.parent / f"{json_path.stem}_with_storylets.json"
            with open(str(output_path), "w") as out_file:
                json.dump(bloom_vist_dict, out_file)
