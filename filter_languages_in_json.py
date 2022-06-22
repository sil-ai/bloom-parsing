from collections import defaultdict
import datetime
from functools import cache
from pathlib import Path
import argparse
import json
import langcodes
from tqdm import tqdm
import random


def count_quarantined(bloom_vist_dict):
    count = 0
    for story_id in bloom_vist_dict["stories"].keys():

        if bloom_vist_dict["stories"][story_id]["quarantine"]:
            count += 1
    return count


def update_bloom_vist_dict_with_story_metadata_dict(bloom_vist_dict):
    # a dictionary to store stories.
    stories_by_id = defaultdict(list)
    if "stories" in bloom_vist_dict.keys():
        return bloom_vist_dict  # done already

    stories_metadata = {}
    for single_element_list in bloom_vist_dict["annotations"]:
        annotation = single_element_list[0]
        story_id = annotation["story_id"]
        stories_by_id[story_id].append(single_element_list)

    for story_id in stories_by_id.keys():
        list_of_annotations_for_story = stories_by_id[story_id]

        # assuming this is consistent for the whole story, which it should be.
        langcode_for_story = list_of_annotations_for_story[0][0]["lang"]
        album_id_for_story = list_of_annotations_for_story[0][0]["album_id"]

        metadata_for_this_story = {
            "album_id": album_id_for_story,
            "bloom_lang": langcode_for_story,
            "filter_methods": {},
            "quarantine": False,
        }

        stories_metadata[story_id] = metadata_for_this_story
    bloom_vist_dict["stories"] = stories_metadata

    return bloom_vist_dict


def get_stories_by_language(bloom_vist_dict):
    stories_by_language = defaultdict(list)
    stories_by_id = defaultdict(list)

    for single_element_list in bloom_vist_dict["annotations"]:
        annotation = single_element_list[0]
        story_id = annotation["story_id"]
        stories_by_id[story_id].append(single_element_list)

    for story_id in stories_by_id.keys():
        list_of_annotations_for_story = stories_by_id[story_id]

        # assuming this is consistent for the whole story, which it should be.
        langcode_for_story = list_of_annotations_for_story[0][0]["lang"]

        stories_by_language[langcode_for_story].append(
            list_of_annotations_for_story
        )  # now it's a list of lists

    print(f"We have {len(stories_by_language.keys())} languages")
    return stories_by_language


def get_majority_scripts_from_unicode_range(x, charmap):
    # written by Joshua Nemecek/Dan Whitenack, relies on charmapping.json
    # which is based on https://www.scriptsource.org/
    x = x.replace(" ", "")
    x = x.replace("\t", "")
    x = x.replace("\n", "")
    x = "".join(x.split())
    scripts = []
    for c in list(x):
        if str(ord(c)) in charmap.keys():
            scripts.append(charmap[str(ord(c))])
    if len(scripts) > 0:
        scripts = max(set(scripts), key=scripts.count)
        scripts = scripts.split("_")
        return scripts
    else:
        return None


def get_expected_scripts_for_lang(bloom_lang_code, langtags):
    bloom_lang = langcodes.get(bloom_lang_code)
    bloom_lang_alpha3 = bloom_lang.to_alpha3()

    expected_scripts = []

    for langtag in langtags:

        try:
            langtag_lang = langcodes.get(langtag["tag"])
            try:
                langtag_lang_alpha3 = langtag_lang.to_alpha3()
                if langtag_lang_alpha3 == bloom_lang_alpha3:
                    if "script" in langtag.keys():
                        expected_scripts.append(langtag["script"])
            except LookupError:
                pass

            if "iso639_3" in langtag:
                if bloom_lang_alpha3 == langtag["iso639_3"]:
                    if "script" in langtag.keys():
                        expected_scripts.append(langtag["script"])

            if (
                langtag_lang == bloom_lang
                or bloom_lang_alpha3 == langtag_lang
                or bloom_lang == langtag_lang
            ):
                if "script" in langtag.keys():
                    expected_scripts.append(langtag["script"])
        except langcodes.tag_parser.LanguageTagError:
            pass
    expected_scripts = list(set(expected_scripts))

    return expected_scripts


def filter_with_expected_scripts(
    bloom_vist_dict,
    charmap_json,
    langtags_json,
    match_threshold=0.95,
    consistency_threshold=0.95,  # TODO:
):
    updated_bloom_vist_dict = bloom_vist_dict
    stories_by_language_dict = get_stories_by_language(bloom_vist_dict)
    languages_in_bloom = list(stories_by_language_dict.keys())

    langtags = {}
    # expecting http://ldml.api.sil.org/langtags.json
    with open(str(langtags_json)) as ltf:
        langtags = json.load(ltf)

    # based on based on https://www.scriptsource.org/
    with open(str(charmap_json)) as chf:
        charmap = json.load(chf)
    print()
    print("#########################")
    print("FILTERING WITH EXPECTED SCRIPTS:")

    # random.shuffle(languages_in_bloom)
    for lang in tqdm(list(languages_in_bloom)):
        stories_for_this_lang = stories_by_language_dict[lang]
        print(f"Checking lang {lang}, which has {len(stories_for_this_lang)} stories")

        expected_scripts_for_this_lang = get_expected_scripts_for_lang(
            bloom_lang_code=lang, langtags=langtags
        )

        print(f"expected scripts for {lang} are {expected_scripts_for_this_lang}")
        stories_quarantined_count = 0

        if (
            expected_scripts_for_this_lang is not None
            and len(expected_scripts_for_this_lang) > 0
        ):
            for story in stories_for_this_lang:
                first_annotation = story[0]
                story_id = first_annotation[0]["story_id"]  # first annotation, and then

                quarantine_story = check_story_for_expected_scripts(
                    match_threshold,
                    charmap,
                    expected_scripts_for_this_lang,
                    story,
                    story_id,
                )
                updated_bloom_vist_dict["stories"][story_id][
                    "quarantine"
                ] = quarantine_story
                if quarantine_story:
                    stories_quarantined_count += 1

                updated_bloom_vist_dict["stories"][story_id]["filter_methods"][
                    "expected_scripts"
                ] = {
                    "expected_scripts": expected_scripts_for_this_lang,
                    "match_threshold": match_threshold,
                    "quarantine_result": quarantine_story,
                }
            print(f"Quarantined {stories_quarantined_count} for lang {lang}")
    return updated_bloom_vist_dict


def check_story_for_expected_scripts(
    match_threshold, charmap, expected_scripts_for_this_lang, story, story_id
):

    quarantine_story = False

    story_length = len(story)
    annotations_that_do_not_match_expected = 0
    caption_samples = []
    scripts_in_story = []
    for annotation in story:
        caption = annotation[0]["text"]
        scripts_in_caption = get_majority_scripts_from_unicode_range(caption, charmap)
        # if scripts_in_caption is None:
        #     print("************8")
        #     print(caption)
        #     print("************8")
        scripts_in_story.append(scripts_in_caption)

        if scripts_in_caption is None:
            pass
        elif (
            len(set(scripts_in_caption).intersection(expected_scripts_for_this_lang))
            < 1
        ):

            annotations_that_do_not_match_expected += 1
            caption_samples.append((caption, scripts_in_caption))

        else:
            # script expected.
            pass
    annotations_that_are_fine_probably = (
        story_length - annotations_that_do_not_match_expected
    )
    percent_fine = annotations_that_are_fine_probably / story_length
    if percent_fine < match_threshold:
        print()
        print("SCRIPT UNEXPECTED.")
        print(
            f"quarantining story {story_id}, {percent_fine} of annotations match expected scripts, less than the threshold {match_threshold}"
        )

        caption, scripts_in_caption = random.choice(caption_samples)
        print("SAMPLE CAPTION:")
        print(caption)
        # print(scripts_in_caption)
        print(
            f"Expected scripts for {story[0][0]['lang']}: {expected_scripts_for_this_lang}"
        )
        print(f"Scripts found: {scripts_in_caption}")
        print()
        quarantine_story = True
    return quarantine_story


def filter_template(bloom_vist_dict):
    filter_method = "PUTTHINGHERE"
    print(f"Filtering with {filter_method}")
    updated_bloom_vist_dict = bloom_vist_dict
    stories_by_language_dict = get_stories_by_language(bloom_vist_dict)
    languages_in_bloom = list(stories_by_language_dict.keys())
    stories_quarantined_count = 0

    # random.shuffle(languages_in_bloom)
    for lang in tqdm(list(languages_in_bloom)):
        stories_for_this_lang = stories_by_language_dict[lang]
        print(f"Checking lang {lang}, which has {len(stories_for_this_lang)} stories")
        for story in stories_for_this_lang:
            first_annotation = story[0]
            story_id = first_annotation[0]["story_id"]  # first annotation, and then

            quarantine_story = PUTMETHODHERE()
            updated_bloom_vist_dict["stories"][story_id][
                "quarantine"
            ] = quarantine_story
            if quarantine_story:
                stories_quarantined_count += 1

            updated_bloom_vist_dict["stories"][story_id]["filter_methods"][
                filter_method
            ] = {
                "quarantine_result": quarantine_story,
            }
        print(f"Quarantined {stories_quarantined_count} for lang {lang}")
    return updated_bloom_vist_dict


def filter_manually(bloom_vist_dict, output_json_path, sample_annotations_count=4):
    print()
    print("###############################")
    print("FILTERING MANUALLY")
    annotator = input("Who is annotating this? ")
    updated_bloom_vist_dict = bloom_vist_dict
    stories_by_language_dict = get_stories_by_language(bloom_vist_dict)
    languages_in_bloom = list(stories_by_language_dict.keys())

    stories_total_count = len(bloom_vist_dict["stories"].keys())
    already_manually_checked_count = 0

    langs_that_have_received_some_checking = []

    for story_id in bloom_vist_dict["stories"].keys():
        story_metadata = bloom_vist_dict["stories"][story_id]
        if "manual" in story_metadata["filter_methods"]:
            already_manually_checked_count += 1
            langs_that_have_received_some_checking.append(story_metadata["bloom_lang"])
    langs_that_have_received_some_checking = list(
        set(langs_that_have_received_some_checking)
    )

    print(
        f"In the dict we already have {already_manually_checked_count} stories manually checked, out of {stories_total_count}. {len(langs_that_have_received_some_checking)} languages have received some checking"
    )

    random.shuffle(languages_in_bloom)
    for i, lang in enumerate(list(languages_in_bloom)):
        displayname = langcodes.get(lang).display_name()
        stories_for_this_lang = stories_by_language_dict[lang]
        random.shuffle(stories_for_this_lang)
        story_ids_for_lang = [
            story[0][0]["story_id"] for story in stories_for_this_lang
        ]
        manually_filtered_stories = [
            "manual" in bloom_vist_dict["stories"][story_id]["filter_methods"].keys()
            for story_id in story_ids_for_lang
        ]

        print()
        print()
        print("*************************************************")
        print("*************************************************")
        print(f"LANG {i}: {lang} ({displayname})")
        print(
            f"Checking lang {i} of {len(languages_in_bloom)} {lang}, which has {len(stories_for_this_lang)} stories, of which {manually_filtered_stories.count(True)} have been manually checked"
        )

        quarantine_whole_language = None
        stories_quarantined_count = 0
        skip_rest_of_stories = False

        if all(manually_filtered_stories):
            print(f"All stories in {lang} are already filtered manually")
            continue

        for j, story in enumerate(stories_for_this_lang):
            if skip_rest_of_stories:
                break
            first_annotation = story[0]
            story_id = first_annotation[0]["story_id"]  # first annotation, and then
            story_filters = bloom_vist_dict["stories"][story_id][
                "filter_methods"
            ].keys()
            story_filters = list(story_filters)
            if "manual" in list(
                bloom_vist_dict["stories"][story_id]["filter_methods"].keys()
            ):
                print(f"skipping story {story_id}, already checked manually")
                continue

            quarantine_story = False
            if quarantine_whole_language is None:

                story_length = len(story)
                sample_annotations_count_for_this_story = min(
                    story_length, sample_annotations_count
                )

                sample_annotations = random.sample(
                    story, k=sample_annotations_count_for_this_story
                )

                print()
                print(
                    f"MANUALLY CHECKING {sample_annotations_count_for_this_story} ANNOTATIONS out of {story_length} FOR story {j+1}/{len(stories_for_this_lang)} with id {story_id}, already filtered by {story_filters}"
                )
                print("``````````````````")
                print()
                for sample_annotation in sample_annotations:
                    print(sample_annotation[0]["text"])
                print()
                print("``````````````````")

                answer = input(
                    f"{j+1}/{len(stories_for_this_lang)} {lang} ({displayname}): Are these annotations probably fine/not obviously wrong-language? y/n, or g to mark whole language as good, b for whole language as bad, or s to skip to next language: "
                )
                if answer.lower() == "y" or answer.lower() == "yes":
                    quarantine_story = False
                    print("story kept")
                elif answer.lower() == "n":
                    quarantine_story = True
                    print("story quarantined")
                elif answer.lower() == "b":
                    quarantine_whole_language = True
                    print("marking whole language as quarantined")
                elif answer.lower() == "g":
                    quarantine_whole_language = False
                    print("marking whole language as not quarantined")
                elif answer.lower() == "s":
                    skip_rest_of_stories = True
                    print("Skipping to the next language")
                    break
                else:
                    quarantine_story = False
            else:
                quarantine_story = quarantine_whole_language

            updated_bloom_vist_dict["stories"][story_id][
                "quarantine"
            ] = quarantine_story

            if quarantine_story:
                stories_quarantined_count += 1

            updated_bloom_vist_dict["stories"][story_id]["filter_methods"]["manual"] = {
                "quarantine_result": quarantine_story,
                "actually_checked_manually": True,
                "annotator": annotator,
            }
            if quarantine_whole_language is not None:
                updated_bloom_vist_dict["stories"][story_id]["filter_methods"][
                    "manual"
                ]["actually_checked_manually"] = False

        print(f"Quarantined {stories_quarantined_count} for lang {lang}")
        answer = input("Would you like to save your progress? y/n: ")
        if answer.lower() == "y":
            print(f"Saving to {output_json_path}")
            with open(output_json_path, "w") as outf:
                json.dump(updated_bloom_vist_dict, outf)

    return updated_bloom_vist_dict


def check_story_with_tf_iif(story, lang, tf_iif_path):

    wordlist = tf_iif_path.read_text().splitlines()


def filter_with_tf_iif(bloom_vist_dict, tf_iif_path):
    print("Filtering with TF IFF: NOT FULLY IMPLEMENTED")
    updated_bloom_vist_dict = bloom_vist_dict
    stories_by_language_dict = get_stories_by_language(bloom_vist_dict)
    languages_in_bloom = list(stories_by_language_dict.keys())

    # random.shuffle(languages_in_bloom)
    for lang in tqdm(list(languages_in_bloom)):
        stories_for_this_lang = stories_by_language_dict[lang]
        print(f"Checking lang {lang}, which has {len(stories_for_this_lang)} stories")
        for story in stories_for_this_lang:
            first_annotation = story[0]
            story_id = first_annotation[0]["story_id"]  # first annotation, and then

            quarantine_story = check_story_with_tf_iif(story, lang, tf_iif_path)
            updated_bloom_vist_dict["stories"][story_id][
                "quarantine"
            ] = quarantine_story
            if quarantine_story:
                stories_quarantined_count += 1

            updated_bloom_vist_dict["stories"][story_id]["filter_methods"]["tf_iif"] = {
                "quarantine_result": quarantine_story,
            }
        print(f"Quarantined {stories_quarantined_count} for lang {lang}")
    return updated_bloom_vist_dict


def filter_with_fasttext(bloom_vist_dict):
    print("Filtering with Fasttext: NOT IMPLEMENTED")
    updated_bloom_vist_dict = bloom_vist_dict  # TODO:
    return updated_bloom_vist_dict


if __name__ == "__main__":
    # based in part on https://colab.research.google.com/drive/1puXHXxNDCgZyRDdesutzoP1MJqCWw69y by Joshua Nemecek
    parser = argparse.ArgumentParser(
        description="Take bloom downloads and output SIS JSON"
    )

    parser.add_argument(
        "path_to_bloom_vist_json",
        # dest="source",
        type=Path,
        default=Path("data/bloom_vist_june15_deduped_by_album_and_story.json"),
        help="json to dedupe",
    )

    parser.add_argument("--filter_manually", action="store_true")

    parser.add_argument("--filter_with_fasttext", action="store_true")

    # https://github.com/google/cld3
    parser.add_argument("--filter_with_cld3", action="store_true")

    parser.add_argument("--filter_with_tf_iif", action="store_true")
    parser.add_argument(
        "--tf_iif_path",
        type=Path,
        default=Path.cwd() / "data/TF-IDF-IIF-top100-wordlists",
    )

    parser.add_argument("--filter_with_expected_scripts", action="store_true")
    parser.add_argument(
        "--filter_with_expected_scripts_charmap",
        type=Path,
        default=Path.cwd() / "data" / "charmapping" / "charmapping.json",
    )
    parser.add_argument(
        "--filter_with_expected_scripts_langtags",
        type=Path,
        default=Path.cwd() / "data" / "charmapping" / "langtags.json",
    )

    args = parser.parse_args()
    with open(str(args.path_to_bloom_vist_json)) as bvf:
        bloom_vist_dict = json.load(bvf)

    updated_bloom_vist_dict = update_bloom_vist_dict_with_story_metadata_dict(
        bloom_vist_dict
    )
    updated_bloom_vist_dict["last_filter_date"] = (str(datetime.datetime.utcnow()),)
    print(f"We have {len(bloom_vist_dict['stories'].keys())} stories")

    out_stem = args.path_to_bloom_vist_json.stem
    if "_langfiltered" not in str(args.path_to_bloom_vist_json):
        output_json_path = args.path_to_bloom_vist_json.parent / (
            args.path_to_bloom_vist_json.stem + "_langfiltered.json"
        )
    else:
        output_json_path = args.path_to_bloom_vist_json

    if args.filter_with_expected_scripts:
        updated_bloom_vist_dict = filter_with_expected_scripts(
            bloom_vist_dict,
            args.filter_with_expected_scripts_charmap,
            args.filter_with_expected_scripts_langtags,
        )

    if args.filter_manually:
        updated_bloom_vist_dict = filter_manually(bloom_vist_dict, output_json_path)

    if args.filter_with_tf_iif:
        updated_bloom_vist_dict = filter_with_tf_iif(bloom_vist_dict, args.tf_iif_path)

    quarantined_count = count_quarantined(updated_bloom_vist_dict)
    print(
        f"Quarantined {quarantined_count} stories out of {len(bloom_vist_dict['stories'].keys())}"
    )

    with open(output_json_path, "w") as fixed_file:
        json.dump(updated_bloom_vist_dict, fixed_file)
