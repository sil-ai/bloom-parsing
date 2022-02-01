# Bloom Parsing Stuff

To re-create the data:

1. Run `./book_parse.sh /path/to/books`
2. To generate clean book, `python book_cleanup.py --source /path/to/extracts/from/1 --out /path/to/out`
3. To generate language model file for HF `python book_lmset.py --source /path/to/cleanup/files/from/2 --out /path/to/out`


