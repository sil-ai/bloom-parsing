from pathlib import Path
import json
import shutil
from tqdm import tqdm


if __name__ == "__main__":
    # Copy images referenced in the VIST-format JSON created by bloom_downloads_to_vist_format
    # so that we can upload it all to s3.
    # takes in: path to bloom_downloads, json output of bloom_downloads_to_vist_format.py, output_folder
    # aws s3 sync --dryrun data/images_to_upload s3://bloom-vist/
    json_to_read = Path("data/bloom_vist_june14.json")
    bloom_downloads_path = Path("data/bloom_downloads")
    output_folder = Path("data/images_to_upload")

    with open(json_to_read, "r") as jsf:
        bloom_json = json.load(jsf)

    for image in tqdm(bloom_json["images"]):
        # print(image["url_o"])
        image_path = bloom_downloads_path / image["local_image_path"]
        # print(image_path)
        output_path = output_folder / image["local_image_path"]
        Path(output_path.parent).mkdir(parents=True, exist_ok=True)
        shutil.copy(str(image_path), str(output_path))

