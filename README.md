# Bloom Parsing 

## EMNLP Parsing Pipeline

The overall pipeline as of submission to EMNLP involves the following scripts. Starting with the one that goes through all the downloaded folders and outputs a VIST-style JSON, the rest take in a VIST JSON and perform various operations that also output a VIST-style JSON. 
- `bloom_downloads_to_vist_format.py` takes the raw downloads and makes them into a json with annotations, albums and 
- `dedupe_bloom_vist.py` takes in a VIST-style JSON, goes through and collapses albums and stories, Written primarily by Anna Filighera. Takes in a file like `bloom_vist_june15.json` and outputs `bloom_vist_june15_deduped_june21.json`
- `filter_languages_in_json.py` applies various filters to "quarantine" stories. I've set it up so that you can optionally turn on different filters, I implemented only "expected scripts" and "filter manually". TF-IIF seems doable as well, others are TODO.
- `add_in_storylet_ids_if_they_dont_exist.py` will take in a JSON, search through annotation fields, and add in the storylet_id field. Turns out having some unique value for each annotation is needed for some codebases. `bloom_vist_june15_deduped_june21_langfiltered_june22_with_storylets.json`
- pipeline_update_json_licenses.py takes in one of the previous JSON files, looks through the albums, and updates the licenses to be noncommercial. Given files like `bloom_vist_june15_deduped_june21_langfiltered_june22_with_storylets.json` it will create a file like `bloom_vist_june15_deduped_june21_langfiltered_june22_with_storylets_licenseupdated.json`
- split_vist_json.py will take VIST JSON and output splits per language. Given a file like `bloom_vist_june15_deduped_june21_langfiltered_june22.json` It creates files with the same name but appended suffixes `_aaa_test.json` and `_eng_train.json`, like `bloom_vist_june15_deduped_june21_langfiltered_june22_aaa_train.json`


### Also Important: 
- `precompute_file_uuids_and_hashes.py`: Given a directory of Bloom books, will calculate md5 and uuid for each file and output them. The resulting `ids_and_hashes.json` is used in the pipeline above. 
- `dataset_stats.py` takes the resulting json from the pipeline and outputs various stats, dicts, etc., which I copy-paste into the top of `bloom_captioning.py` (the loading script) for example. For example the `_BLOOM_LANGUAGES_ALPHA3_VALID` is generated here.  `bloom_captioning.py` is the loading script for the captioning set, depends on the dictionaries above, and uses the "quarantine" field. 
- `fix_truncated_images.py` is used to solve problems with images that were uploaded to Bloom in a truncated state. Simply put, we open them, save them with gray pixels where the file got truncated, and declare the problem "fixed". Otherwise we get file loading errors downstream. 

### Scripts for dealing with S3 bucket/image URLs
One problem we ran into was that we upload the files to S3 bucket but there's no easy way to programmatically get the public HTTP URL for the images. The most successful method involves simply setting the bucket to generate a "Manifest" and parsing the keys from that into URLs. 

Related scripts: 
-` copy_images_for_upload_to_s3.py` was the solution to uploading images in the first place. We didn't necessarily want to upload all of our raw downloads due to copyright/rights concerns. So this script takes only some of the images and puts them in a new folder that we can then upload with an `s3` commmand line command. 
- `match_aws_keys_with_ids_and_hashes.py` takes the AWS manifest CSV and the ids/hashes JSON and matches things up. It takes in the `ids_and_hashes.json` above, and `aws_manifest.csv` generated by the [AWS S3 bucket's inventory feature](https://docs.aws.amazon.com/AmazonS3/latest/userguide/configure-inventory.html) to calculate the open HTTPs urls for all the images.




### Miscellaneous: 
- `list_files_in_public_bucket.py`: just a quick script to see what files are in our bucket. 
- `how_many_languages.py:` a quick script to count unique languages in annotation elements in a VIST Json
- `get_json_top_level_keys.py` is a useful script for basically just exploring the layout of a JSON by loading it as a Python dict and printing the top-level keys.



## Former pipeline, used for lm set originally
The files for this old pipeline are in `original_bloom_lm_pipeline`

To re-create the data:

1. Use boto3 to extract all `*htm` and `meta.json` files to `/path/to/books` with a folder per book
2. Run `python book_parser.py --source /path/to/books --out /path/to/output`, which should create a folder and put in it one .json per book, containing text and metadata from the htm and meta.json above. 
3. To generate clean book, `python book_cleanup.py --source /path/to/extracts/from/2 --out /path/to/out`
4. To generate language model file for HF `python book_lmset.py --source /path/to/cleanup/files/from/3 --out /path/to/out`

## Requirements for parsing pipeline: 

Minimal requirements include...
```
beautifulsoup4
pandas
tqdm
```

See `bloom-parsing-conda-env.yml` for the exact versions used for the EMNLP pipeline. 