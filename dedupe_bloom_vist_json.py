import json
from pathlib import Path


def collapse_duplicate_albums_and_stories(bloom_vist_dict, ids_and_hashes_dict):
    # load in the bloom_vist_json (https://bloom-vist.s3.amazonaws.com/bloom_vist_june14.json) and
    # and ids_and_hashes json https://bloom-vist.s3.amazonaws.com/ids_and_hashes_june_14_with_image_hashes.json
    # get all the albums

    # TERMINOLOGY
    # book: the folder of raw data with .pngs and htm file, has its own page on Bloom. Might have a few languages included.
    # translation: the full batch of text tagged with a certain language code/name in the book.
    # story: a VIST term originally, in our json a segmented representation of a translation, where it is segmented in a way that it aligns to an ordered set of images in the book
    # album: a VIST term originally, in our the ordered set of images associated with the book

    albums = bloom_vist_dict["albums"]
    albums_by_id = {}
    checked_albums = []

    # the dictionary we're returning, with albums that have the same images collapsed, and duplicate captions deleted.
    updated_bloom_vist_dict = {}

    for album in albums:
        album_id = album["id"]

        albums_by_id[album_id] = album

    for album in albums:
        for checked_album in checked_albums:
            # Let's limit ourselves to albums that are in the same lineage.
            # if they share lineage they MIGHT be the same.
            # check the lineages of each. Just see if there's intersection between the lists.
            pass
            book_lineage = album["metadata_from_original_json"]["bookLineage"].split()
            book_lineage_from_checked = album["metadata_from_original_json"][
                "bookLineage"
            ].split()

            # Checking the images. If they have at least mostly the same images we can consider them the same album.

            # TODO: code to parse out all the associated images for each album goes here.

            # TODO: code to check the md5 hashes of the two sets of images, precomputed in ids_and_hashes.json
            # You can use ==, if they have the same md5 that means they're exactly equivalent to the byte.
            # no need to check perceptual hash if they use literally the same images to the pixel.

            # TODO: code to check the perceptual hashes of the two sets of images, precomputed in ids_and_hashes.json
            # "similar" images have the same phash/image_hash, you can literally just use ==

            ## COLLAPSE ALBUMS
            # If we determine that they are the same "Album", aka an ordered set of images, we need to go through the
            # TODO: Code that parses through the json and updates all the album ids to point to just one of these two albums.

            ## DEDUPE STORIES/CAPTIONS
            # OK, if it's the same "album" we should also check for captions that are duplicated.
            # It's often the case that the, like, English translation exists within multiple "books".

            # TODO: code that checks for sets of duplicate captions.
            # Maybe start by pulling out all sets of captions that for these albums that are marked as the same lang?
            # Maybe use editdistance library so small punctuation diffs don't ruin us
            # Maybe just be lazy and use ==

            ### DELETE DUPLICATE STORIES
            # If we've determined two "stories" (sets of image/caption pairs) are duplicates, we can just... delete one?
            # TODO: code that scrubs through the json and deletes all annotations with the story_id that is a dupe.

        checked_albums.append(album)

    return updated_bloom_vist_dict


if __name__ == "__main__":

    # https://bloom-vist.s3.amazonaws.com/bloom_vist_june14.json

    path_to_bloom_vist_json = Path("bloom_vist_june14.json ")

    # https://bloom-vist.s3.amazonaws.com/ids_and_hashes_june_14_with_image_hashes.json
    path_to_precomputed_file_ids_and_hashes_json = Path(
        "ids_and_hashes_june_14_with_image_hashes.json"
    )

    # TODO: load jsons correctly, not sure if this is right
    with open(str(path_to_bloom_vist_json)) as bvf:
        bloom_vist_dict = json.load(bvf)

    with open(str(path_to_precomputed_file_ids_and_hashes_json)) as idf:
        ids_and_hashes_dict = json.load(idf)
    updated_bloom_vist_dict = collapse_duplicate_albums_and_stories(
        bloom_vist_dict, ids_and_hashes_dict
    )
