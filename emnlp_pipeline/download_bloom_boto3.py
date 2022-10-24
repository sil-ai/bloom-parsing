import boto3
from pathlib import Path
import time
from tqdm import tqdm
import logging
import argparse  # todo: read from creds.json
from botocore.exceptions import ClientError
import json

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="download Bloom books")

    parser.add_argument(
        "--credentials_file",
        dest="credentials_file",
        help="json file containing s3 creds",
    )
    parser.add_argument(
        "--out", dest="out", help="output directory for downloaded files"
    )

    args = parser.parse_args()
    with open(args.credentials_file, "r") as credentials_file:
        credentials = json.load(credentials_file)

    print(credentials)
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
    )

    # Connects to the bucket
    my_bucket = s3.Bucket("BloomLibraryBooks")
    master_download_folder = Path(args.out)

    print(f"downloading to {master_download_folder}")

    # list all the files
    master_download_folder.mkdir(exist_ok=True)
    keys = []

    # which extensions should we download? Actual text lives in the .htm and the .json,
    # 543010 files total
    # .png 179493
    # .css 110701
    # .jpg 92867
    # .mp3 76233
    # .BloomBookOrder 17280
    # .svg 13711
    # .json 13489
    # .htm 13476
    # .pdf 12895
    # .mp4 6000
    #  2138  <--------------- files that have no name, literally just suffix. e.g. ".jpg"
    # .bak 1372
    # .wav 1187
    # .js 586
    # .woff 316
    # .doc 247
    # .html 162
    # .opds 118
    # .jade 71
    # .ini 68
    # .md 55
    # .epub 48
    # .userPrefs(1) 44
    # .modd 41
    # .onetoc2 38
    # .map 30
    # .bloomd 26
    # .jpeg 25
    # .xhtml 22
    # .xml 19
    # .less 15
    # .pending 14
    # .au 14
    # .TMP 12
    # .db 11
    # .orig 10
    # .PNG 10
    # .tmp 10
    # .docx 10
    # .bloomCollection 7
    # .thmx 7
    # .i1q 6
    # .txt 6
    # .db_encryptable_$DATA 6
    # .userPrefs(2) 5
    # .ha5 4
    # .qu3 4
    # .ppu 4
    # .ak3 4
    # .3jl 4
    # .u50 4
    # .afi 4
    # .wpj 4
    # .status 4
    # .DOC 4
    # .msg 4
    # .htm~ 4
    # .afdesign 4
    # .ts-ignore 4
    # .itw 3
    # .BloomPack 3
    # .JPG 3
    # .rar 3
    # .ixm 2
    # .qin 2
    # .tmg 2
    # .userPrefs(3) 2
    # .old 2
    # .CSS 2
    # .42n 1
    # .odt# 1
    # .tgp 1
    # .nq3 1
    # .ryd 1
    # .f5x 1
    # .ws4 1
    # .TXT 1
    # .psd 1
    # .og2 1
    # .rtf 1

    extensions = [
        ".png",  # 179493 of these
        # ".css", # many many, but no actual content
        ".jpg",  # 92867 files
        # ".mp3",  # 76233
        # ".BloomBookOrder",  # 17280, seems to contain metadata similar to json files
        # ".svg",  # 13711, but they don't seem to be story content, mostly logos and such.
        ".json",  # 13489 # usually metadata.json
        ".htm",  # 13476, actual content.
        # ".pdf",  # 12895 of these but we don't need them.
        # ".mp4",  # 6000, mostly sign language apparently.
        # ".bak", # 1372, but obviously not what we're looking for, right
        ".wav",  # 1187
        ".html",  # 167 of these
    ]  # TODO: make this an argparse arg

    # Test code
    shouldwebreak = False
    i = 0  # index for testing
    howmanybeforebreak = 20000000

    # all the bucket objects
    all_bucket_objects = my_bucket.objects.all()  # s3.Bucket.objectsCollection
    print("looping")
    for my_bucket_object in tqdm(all_bucket_objects):  # FIXME: test code

        if shouldwebreak == True and i > howmanybeforebreak:
            print("breaking due to test code!")
            break

        keys.append(my_bucket_object.key)
        #     print("**************")
        #     print(my_bucket_object)

        #     print(my_bucket_object.key)
        path_from_key = Path(
            my_bucket_object.key
        )  # load a path object for convenient stem parsing
        download_folder = (
            master_download_folder / path_from_key.parent.stem
        )  # the stem contains the name of the book itself.

        # make the folder for the book
        download_folder.mkdir(exist_ok=True)

        # path for the file itself
        download_path = download_folder / path_from_key.name

        # print(download_path)

        # this was to filter by extension
        if any(extension in path_from_key.name for extension in extensions):
            print(f"downloading {my_bucket_object.key} to {download_path}")

            # download the file! Sleep after downloading a file
            if not download_path.exists():
                # if ".png" in download_path and not "placeholder" in download_path:
                try:
                    i = i + 1
                    print(i)
                    my_bucket.download_file(my_bucket_object.key, str(download_path))
                    time.sleep(0.1)
                except ClientError:
                    logging.exception(my_bucket_object.key)
