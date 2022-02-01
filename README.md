# Bloom Parsing Stuff

To re-create the data:

1. Use boto3 to extract all `*htm` and `meta.json` files to `/path/to/books` with a folder per book
2. Run `./book_parse.sh /path/to/books`
3. To generate clean book, `python book_cleanup.py --source /path/to/extracts/from/1 --out /path/to/out`
4. To generate language model file for HF `python book_lmset.py --source /path/to/cleanup/files/from/2 --out /path/to/out`


