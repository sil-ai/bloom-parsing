from pathlib import Path
from collections import defaultdict
import random

if __name__ == "__main__":
    keys = Path("keys.txt").read_text().splitlines()
    print(len(keys))

    extension_examples = defaultdict(str)
    extension_counts = defaultdict(int)

    for key in keys:
        keypath = Path(key) # it's not a file but pathlib helps parse it. 
        extension = keypath.suffix

        # dealing with files that have a extension but no name:, e.g. ".lastUploadInfo""
        # foo.suffix gives ''
        # foo.name gives ".lastUploadInfo"
        # foo.stem gives ".lastUploadInfo"
        # name_and_stem_the_same = keypath.name == keypath.stem
        # if not keypath.suffix and name_and_stem_the_same:
            # # todo:  
            # pass
        extension_counts[extension] = extension_counts[extension] + 1

        overwrite = random.choice(list(range(1, 100)))
        if overwrite < 95 and extension_examples[extension]:
            pass
        else:
            extension_examples[extension] = key

    # https://www.tutorialsteacher.com/articles/sort-dict-by-value-in-python
    sorted_counts = sorted(
        extension_counts.items(), key=lambda x: x[1], reverse=True
    )  # use this lambda function as sorting key, function is "take element with index 1"
    for key, value in sorted_counts:
        print(key, value)

    print("examples")
    for key, value in extension_examples.items():
        print(f"extension: {key},\n\texample: {value}")
