# Bloom Parsing Stuff

### Parsing pipeline scripts
The overall pipeline as of submission to EMNLP.
- bloom_downloads_to_vist_format.py takes the raw downloads and makes them into a json
- dedupe_bloom_vist.py goes through and collapses albums and stories
- filter_languages_in_json.py applies various filters to "quarantine" stories. I've set it up so that you can optionally turn on different filters, I implemented only "expected scripts" and "filter manually". TF-IIF seems doable, others I dunno.
- dataset_stats.py then takes the resulting json and outputs various stats, dicts, etc., which I copy-paste into the top of bloom_captioning.py for example. For example the _BLOOM_LANGUAGES_ALPHA3_VALID is generated here. 
- bloom_captioning.py is the loading script for the captioning set, depends on the dictionaries above, and uses the "quarantine" field. 
- test_load.py tests the loading script and has some useful functions to, like, show one image or save off splits.


Important: 
- precompute_file_uuids_and_hashes: Given a directory of Bloom books, will calculate md5 and uuid for each file and output them. The resulting ids_and_hashes JSON is used in the pipeline above. 

### Scripts for dealing with S3 bucket/image URLs
One problem we ran into was that we upload the files to S3 bucket but there's no easy way to programmatically get the public HTTP URL for the images. The most successful method involves simply setting the bucket to generate a "Manifest" and parsing the keys from that into URLs. 

Related scripts: 
- copy_images_for_upload_to_s3.py was the solution to uploading images in the first place. We didn't necessarily want to upload all of our raw downloads due to copyright/rights concerns. So this script takes only some of the images and puts them in a new folder that we can then upload with an `s3` commmand line command. 
- match_aws_keys_with_ids_and_hashes.py takes the AWS manifest CSV and the ids/hashes JSON and matches things up. 




### Miscellaneous: 
- list_files_in_public_bucket.py: just a quick script to see what files are in our bucket. 
- how_many_languages.py: a script to count unique languages in annotation elements in a VIST Json



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
