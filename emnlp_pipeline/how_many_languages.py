from enum import unique
import json

# CDL: a script to count unique languages in annotation elements in a VIST Json

if __name__ == "__main__":
    with open("data/bloom_vist_june14.json", "r",) as jsf:
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
