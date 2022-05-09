from enum import unique
import json

if __name__ == "__main__":
    with open(
        "bloom_downloads_vist_filtered_by_license_2022-04-29T1141.json", "r"
    ) as jsf:
        data = json.load(jsf)
    annotations = data["annotations"]

    print(f"there are {len(annotations)}")

    langs = []
    for annotation in annotations:
        textdict = annotation[0]["text"]
        langs_in_text = textdict.keys()
        langs.extend(langs_in_text)
    unique_langs = set(langs)
    print(f"out of {len(langs)} text element langs, {len(unique_langs)} are unique. ")
    print(unique_langs)
