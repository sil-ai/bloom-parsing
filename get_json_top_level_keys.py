import argparse
import json
from pathlib import Path

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()

    print(args.json_path)

    with open(args.json_path) as jp:
        json_data = json.load(jp)
        for k, v in json_data.items():
            if isinstance(v, list):
                print(f"{k}: {type(v)}: {len(v)} items")
            elif isinstance(v, dict):
                print(f"{k}: {type(v)}: {len(v)} items, {len(v.keys())} keys")
            elif isinstance(v, str):
                print(f"{k}: {v}")
            else: 
                print(f"{k}: {type(v)}")


