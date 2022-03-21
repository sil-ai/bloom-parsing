from pathlib import Path
from collections import defaultdict

if __name__ == "__main__":
    keys = Path("keys.txt").read_text().splitlines()
    print(len(keys))

    extension_counts = defaultdict(int)

    for key in keys:
        extension = Path(key).suffix
        extension_counts[extension] = extension_counts[extension] + 1

    # https://www.tutorialsteacher.com/articles/sort-dict-by-value-in-python
    sorted_counts = sorted(
        extension_counts.items(), key=lambda x: x[1], reverse=True
    )  # use this lambda function as sorting key, function is "take element with index 1"
    for key, value in sorted_counts:
        print(key, value)
