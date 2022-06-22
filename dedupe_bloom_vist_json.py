import argparse
import json
from copy import deepcopy
from tqdm import tqdm
from pathlib import Path
import datetime
from collections import defaultdict
from thefuzz import fuzz
import random
from itertools import combinations

# from nltk.metrics.distance import edit_distance

""" some problems:
    - albums may essentially be the same but have an additional all white image or so --> still collapsed them
    - since the perceptual hash seems to be quite generous in what constitutes the same image, it is not reliable enough
        to detect nearly identical images --> duplicate images are likely to be in the dataset. Should'nt  be a big problem
        since the annotations are likely used for the dataset construction. All images will point to a collapsed album_id 
        though, so there may be more images than expected pointing at an album"""


def collapse_duplicate_albums_and_stories(
    bloom_vist_dict,
    ids_and_hashes_dict,
    output_json_path,
    usefuzz,
    images_similarity_thresh=80,
):
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
    images = bloom_vist_dict["images"]
    annotations = bloom_vist_dict["annotations"]

    # the dictionary we're returning, with albums that have the same images collapsed, and duplicate captions deleted.
    updated_bloom_vist_dict = {}
    dupe_album_ids = {}
    # some dicts to speed up the search for images and annotations later on
    images_by_id = defaultdict(list)
    annotations_by_album_id = defaultdict(list)
    image_hashes = {}

    for album in albums:
        album_id = album["id"]
        albums_by_id[album_id] = album
    for image in images:
        images_by_id[image["album_id"]].append(image)
    # didn't see the need to keep the unnecessary list in my own dict :)
    for first_annotation in annotations:
        if len(first_annotation) > 1:
            print("assumption of unnecessary list seems false")
        annotations_by_album_id[first_annotation[0]["album_id"]].append(
            first_annotation[0]
        )
    for item in ids_and_hashes_dict.values():
        for image in item.values():
            """ 
            just checking to make sure there actually are images with the same perceptual hash --> yes there are many
            if image.get("image_hash", "no_hash") in image_hashes.values():
                print("Images with the same image hash exist.")
            """
            image_hashes[image["id"]] = image.get("image_hash", "no_hash")
    # count number of duplicate albums for sanity checks later on
    duplicate_counter = 0

    print("filtering albums")
    for album in tqdm(albums):
        album_id = album["id"]
        album_annotations = annotations_by_album_id.get(album_id, [])
        album_images = images_by_id.get(album_id, [])
        # no need to keep empty albums
        if len(album_images) == 0 or len(album_annotations) == 0:
            print(
                "This album seems to have no images and/or no annotations associated with the album id",
                album_id,
            )
            continue
        duplicateID = None

        for checked_album in checked_albums:
            checked_id = checked_album["id"]
            # this turned out to be very helpful in the beginning, but useless now. Just remains as sanity check
            if checked_id == album_id:
                print("Why are there duplicate IDs?")
                print(album_id, checked_id)
                duplicateID = checked_id
                break
            identical_image_count = 0
            checked_images = images_by_id.get(checked_id)
            if (
                checked_album["metadata_from_original_json"]["bookInstanceId"]
                == album["metadata_from_original_json"]["bookInstanceId"]
            ):
                duplicateID = checked_id
                """ considered merging titles, but probably not helpful and just wasting runtime
                titles_album = ast.literal_eval(album["metadata_from_original_json"]["allTitles"])
                titles_checked = ast.literal_eval(checked_album["metadata_from_original_json"]["allTitles"])
                checked_album["metadata_from_original_json"]["allTitles"] = str(dict(titles_album, **titles_checked))
                """
                break
            # compare perceptual hash of all images in album to identify duplicates
            for idx, album_image in enumerate(album_images):
                if idx >= len(checked_images):
                    break
                if (
                    image_hashes[album_image["id"]]
                    == image_hashes[checked_images[idx]["id"]]
                ):
                    identical_image_count += 1
            if identical_image_count != 0:
                # this may behave weirdly if the album is very small, an additional check for the number of images in
                # total may be helpful --> but some books differ in only an empty white image or so --> idk
                percentage = 100 / len(album_images) * identical_image_count
                if percentage >= images_similarity_thresh:
                    """
                    print("Percentage of identical images", percentage)
                    print(album_id, " - ", checked_id)
                    """
                    # just for checking some random edgecases in debug mode
                    if percentage < 100:
                        pass
                    duplicateID = checked_id
                    break
        # add album to our new album dict if it is not a duplicate
        if duplicateID is None:
            checked_albums.append(album)
            dupe_album_ids[album_id] = []
        # track duplicate album ids for later
        else:
            duplicate_counter += 1
            dupe_album_ids[duplicateID].append(album_id)

    print("collapsing albums")
    # COLLAPSE ALBUMS
    duplicate_album_ids_dict = dict(
        (dupe, non_dupe) for non_dupe, v in dupe_album_ids.items() for dupe in v
    )
    for image in tqdm(images):
        album_id = image["album_id"]
        if album_id in duplicate_album_ids_dict.keys():
            image["album_id"] = duplicate_album_ids_dict[album_id]

    for annotation in tqdm(annotations):
        album_id = annotation[0]["album_id"]
        if album_id in duplicate_album_ids_dict.keys():
            annotation[0]["album_id"] = duplicate_album_ids_dict[album_id]

    # Intermediate save of albums and images to speedup any debugging of the annotation deduplication
    updated_bloom_vist_dict["utc_creation_date"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    updated_bloom_vist_dict["duplicate_ids_list"] = dupe_album_ids
    updated_bloom_vist_dict["albums"] = checked_albums
    updated_bloom_vist_dict["images"] = images
    with open(output_json_path, "w") as fixed_file:
        json.dump(updated_bloom_vist_dict, fixed_file)

    # DEDUPE STORIES/CAPTIONS + DELETE DUPLICATE STORIES
    print("dedupe stories/captions")
    non_dupe_annotations = []
    number_dup_ans = 0
    dup_keys = duplicate_album_ids_dict.keys()
    dupe_annotations = []  # just for printing out later.

    # build a dictionary of _stories_. Lists of annotations with the same story ID, all associated with one album.
    stories_by_story_id = defaultdict(list)
    print(f"Building index of stories, indexed by story id")
    for first_annotation in tqdm(annotations):
        album_id = first_annotation[0]["album_id"]
        story_to_check_id = first_annotation[0]["story_id"]

        # text = annotation[0]["text"]
        stories_by_story_id[story_to_check_id].append(first_annotation)

    # build a dictionary of stories, indexed by album_id, aka the set of photos the captions go with.
    stories_by_album_id = defaultdict(list)
    print(f"Building index of stories indexed by album ID")
    for story_to_check_id in tqdm(stories_by_story_id.keys()):
        story = stories_by_story_id[story_to_check_id]  # a list of annotations.

        album_ids_in_story = []
        for first_annotation in story:
            album_id_for_annotation = first_annotation[0]["album_id"]
            album_ids_in_story.append(album_id_for_annotation)

        album_ids_in_story = list(set(album_ids_in_story))

        if len(album_ids_in_story) > 1:
            raise ValueError(
                f"ERROR: a story with story_id {story_to_check_id} contains more than one album ID: {album_ids_in_story}, how the heck"
            )
        else:
            album_id_for_story = album_ids_in_story[0]
            stories_by_album_id[album_id_for_story].append(story)

    print(f"DEDUPING STORIES")
    stories_to_keep = []
    stories_to_toss_as_indexes_pointing_to_keepers = {}

    story_ids_to_check = list(stories_by_story_id.keys())

    # DEBUG CODE
    # story_ids_to_check = story_ids_to_check[:20]
    # story_ids_to_check.extend(
    #     [
    #         "7056431e-1924-47a1-ba5a-e8b67b1b857e",
    #         "f46fc1b9-e512-429e-bf81-b47068553d48",
    #     ]
    # )
    story_combinations = list(combinations(story_ids_to_check, 2))

    # for story_to_check_id in tqdm(list(stories_by_story_id.keys())):
    #     for story_to_check_against_id in list(stories_by_story_id.keys()):

    for story_to_check_id, story_to_check_against_id in tqdm(story_combinations):
        if story_to_check_id in stories_to_toss_as_indexes_pointing_to_keepers:
            continue  # already know this one is a dupe of something, skip it.
        # TODO: limit to stories of the same language?

        story_to_check = stories_by_story_id[story_to_check_id]
        story_to_check_against = stories_by_story_id[story_to_check_against_id]

        # check story
        stories_are_the_same = is_story_to_check_a_dupe_of_story_to_check_against(
            story_to_check, story_to_check_against, usefuzz=usefuzz
        )
        if stories_are_the_same:

            # toss the other one. This one was first so it wins
            stories_to_toss_as_indexes_pointing_to_keepers[
                story_to_check_against_id
            ] = story_to_check_id
            print(
                f"story {story_to_check_against_id} is a dupe of {story_to_check_id}!"
            )

        else:
            # Not a dupe story... yet!
            # do nothing!
            pass

    # let's count dupes
    for first_annotation in annotations:
        story_id = first_annotation[0]["story_id"]
        if story_id in stories_to_toss_as_indexes_pointing_to_keepers:
            number_dup_ans += 1
        else:
            non_dupe_annotations.append(first_annotation)

    updated_bloom_vist_dict["annotations"] = non_dupe_annotations
    print("Duplicate Albums found:", duplicate_counter)
    print("Duplicate Annotations found", number_dup_ans)
    print(
        "Duplicate Stories found", len(stories_to_toss_as_indexes_pointing_to_keepers)
    )

    sample_count = min(5, len(stories_to_toss_as_indexes_pointing_to_keepers))
    dupe_story_samples = list(stories_to_toss_as_indexes_pointing_to_keepers.keys())
    random.shuffle(dupe_story_samples)

    for dupe_story_id in dupe_story_samples[:sample_count]:
        print("************************")
        print(
            f"SAMPLE DUPE STORY: {dupe_story_id}, dupe of {stories_to_toss_as_indexes_pointing_to_keepers[dupe_story_id]}, first annotation:"
        )
        dupe_story_to_show = stories_by_story_id[dupe_story_id]
        first_annotation = dupe_story_to_show[0]
        print(f"{first_annotation=}")
        # for annotation in dupe_story_to_show:
        #     print(annotation[0]["text"])
    return updated_bloom_vist_dict


def is_story_to_check_a_dupe_of_story_to_check_against(
    story_to_check: list,
    story_to_check_against: list,
    story_length_difference_threshold=5,
    usefuzz=False,
    fuzz_ratio_threshold=95,
    percent_same_threshold=0.95,
    annotations_different_threshold=5,
    different_langs_count_threshold=3,
):
    story_to_check_first_annotation = story_to_check[0]
    story_to_check_id = story_to_check_first_annotation[0]["story_id"]

    story_to_check_against_first_annotation = story_to_check_against[0]
    story_to_check_against_id = story_to_check_against_first_annotation[0]["story_id"]
    debug_statements = False

    if (
        "7056431e-1924-47a1-ba5a-e8b67b1b857e" in story_to_check_id
        and "f46fc1b9-e512-429e-bf81-b47068553d48" in story_to_check_against_id
    ):

        debug_statements = True

    if (
        "f46fc1b9-e512-429e-bf81-b47068553d48" in story_to_check_id
        and "7056431e-1924-47a1-ba5a-e8b67b1b857e" in story_to_check_against_id
    ):
        debug_statements = True

    # if (
    #     "TESTING" in story_to_check_id
    #     or "TESTING" in story_to_check_against_id
    #     or "dcaed8df0ce0" in story_to_check_id
    #     or "dcaed8df0ce0" in story_to_check_against_id
    # ):
    #     debug_statements = True
    #     if (
    #         "dcaed8df0ce0" in story_to_check_id
    #         and "dcaed8df0ce0" in story_to_check_against_id
    #     ):
    #         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #         print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #         print(
    #             f"{story_to_check_id} is being checked against {story_to_check_against_id}"
    #         )

    # I mean, if they've got the same story ID and length and first text element the same they are literally the same story.
    if (
        len(story_to_check) == len(story_to_check_against)
        and story_to_check_id == story_to_check_against_id
        and story_to_check_first_annotation[0]["text"]
        == story_to_check_against_first_annotation[0]["text"]
    ):
        if debug_statements:
            print(
                f"{story_to_check_id} is a dupe of {story_to_check_against_id}, they have the same length, id, and first annotation"
            )
        return True

    # if the lengths of the two lists are more than story_length_difference_threshold different they're different enough to keep probably.
    if abs(
        len(story_to_check) - len(story_to_check_against)
        > story_length_difference_threshold
    ):
        if debug_statements:
            print(
                f"{story_to_check_id} (length {len(story_to_check)}) is not a dupe of {story_to_check_against_id} (length {len(story_to_check_against)}), too different in length"
            )
        return False

    # if the languages are different they're not dupes.

    # check if all/most of the captions are the same.
    count_of_annotations_the_same_for_these_two_stories = 0
    dupe_pairs = []
    different_langs_count = 0
    for i, story_to_check_annotation in enumerate(story_to_check):

        
        for story_to_check_against_annotation in story_to_check_against:

            
            

            annotation_same = False
            if usefuzz:
                annotation_same = (
                    fuzz.ratio(
                        story_to_check_annotation[0]["text"],
                        story_to_check_against_annotation[0]["text"],
                    )
                    > fuzz_ratio_threshold
                )
            else:
                annotation_same = (
                    story_to_check_annotation[0]["text"]
                    == story_to_check_against_annotation[0]["text"]
                )

            if annotation_same:
                count_of_annotations_the_same_for_these_two_stories += 1
                
                count_that_are_different = i+1 - count_of_annotations_the_same_for_these_two_stories
                if count_that_are_different > annotations_different_threshold:
                    if debug_statements:
                        print(f"The story {story_to_check_id} is NOT a dupe of {story_to_check_against_id}, We've now found {count_that_are_different} items that are different langs, more than threshold {annotations_different_threshold}")
                        return False


                pair_of_dupes = (
                    story_to_check_annotation,
                    story_to_check_against_annotation,
                )
                dupe_pairs.append(pair_of_dupes)

            if not annotation_same:
                # they're not the same and also the languages are marked as different

                if (
                story_to_check_annotation[0]["lang"]
                == story_to_check_against_annotation[0]["lang"]
                ):
                    pass  # all is well
                else:
                    different_langs_count += 1
                
                if different_langs_count > different_langs_count_threshold:
                    if debug_statements:
                        print(f"The story {story_to_check_id} is NOT a dupe of {story_to_check_against_id}, We've now found {different_langs_count} items that are different langs, more than threshold {}")
                    return False
            
    percent_same = count_of_annotations_the_same_for_these_two_stories / len(story_to_check)
    if percent_same > percent_same_threshold:
        if debug_statements:
            print(
                f"The story {story_to_check_id} is a dupe of {story_to_check_against_id}, because {count_of_annotations_the_same_for_these_two_stories} out of {len(story_to_check)} annotations in the story are found within it. That's {percent_same} similar, greater than the threshold of {percent_same_threshold}"
            )
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        return True

    else:
        if debug_statements:
            print(
                f"The story {story_to_check_id} is NOT a dupe of {story_to_check_against_id}, because {count_of_annotations_the_same_for_these_two_stories} out of {len(story_to_check)} annotations in the story are found within it. That's {percent_same} similar, less than the threshold of {percent_same_threshold}"
            )
        return False


if __name__ == "__main__":

    # https://bloom-vist.s3.amazonaws.com/bloom_vist_june14.json

    # path_to_bloom_vist_json = Path("data/bloom_vist_june15.json")

    # https://bloom-vist.s3.amazonaws.com/ids_and_hashes_june_14_with_image_hashes.json
    path_to_precomputed_file_ids_and_hashes_json = Path(
        "ids_and_hashes_june_14_with_image_hashes.json"
    )
    parser = argparse.ArgumentParser(
        description="Take bloom downloads and output SIS JSON"
    )

    parser.add_argument(
        "path_to_bloom_vist_json",
        # dest="source",
        type=Path,
        default=Path("data/bloom_vist_june15.json"),
        help="json to dedupe",
    )

    parser.add_argument("--usefuzz", action="store_true", default=False)

    args = parser.parse_args()

    # output_json_path = "bloom_vist_june14_albums_images_deduped.json"
    output_json_path = args.path_to_bloom_vist_json.parent / (
        args.path_to_bloom_vist_json.stem + "_deduped.json"
    )

    with open(str(args.path_to_bloom_vist_json)) as bvf:
        bloom_vist_dict = json.load(bvf)

    with open(str(path_to_precomputed_file_ids_and_hashes_json)) as idf:
        ids_and_hashes_dict = json.load(idf)
    updated_bloom_vist_dict = collapse_duplicate_albums_and_stories(
        bloom_vist_dict, ids_and_hashes_dict, output_json_path, args.usefuzz
    )

    updated_bloom_vist_dict["dedupe_date"] = (str(datetime.datetime.utcnow()),)

    with open(output_json_path, "w") as fixed_file:
        json.dump(updated_bloom_vist_dict, fixed_file)
