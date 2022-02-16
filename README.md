# Bloom Parsing Stuff

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
