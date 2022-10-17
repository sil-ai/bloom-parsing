# Bloom Parsing Stuff

## Parsing pipeline 
The pipeline as of submission to EMNLP.
- bloom_downloads_to_vist_format.py takes the raw downloads and makes them into a json
- dedupe_bloom_vist.py goes through and collapses albums and stories
- filter_languages_in_json.py applies various filters to "quarantine" stories. I've set it up so that you can optionally turn on different filters, I implemented only "expected scripts" and "filter manually". TF-IIF seems doable, others I dunno.
dataset_stats.py then takes the resulting json and outputs various stats, dicts, etc., which I copy-paste into the top of bloom_captioning.py for example.
- bloom_captioning.py is the loading script for the captioning set
- test_load.py tests the loading script and has some useful functions to, like, show one image or save off splits.

Other scripts: 
- dataset_stats.py is quite critical for generating some of the dictionaries and dataset card markdown that go into the sub-datasets. For example the _BLOOM_LANGUAGES_ALPHA3_VALID is generated here. 



## Former pipeline, used for lm set originally

To re-create the data:

1. Use boto3 to extract all `*htm` and `meta.json` files to `/path/to/books` with a folder per book
2. Run `python book_parser.py --source /path/to/books --out /path/to/output`, which should create a folder and put in it one .json per book, containing text and metadata from the htm and meta.json above. 
3. To generate clean book, `python book_cleanup.py --source /path/to/extracts/from/2 --out /path/to/out`
4. To generate language model file for HF `python book_lmset.py --source /path/to/cleanup/files/from/3 --out /path/to/out`

## Requirements for parsing: 

Requirements include...
```
beautifulsoup4
pandas
tqdm
```
