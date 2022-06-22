from collections import defaultdict
from enum import unique
import json
import langcodes


def story_quarantined(bloom_vist_annotations_dict, story_id):

    metadata_for_story = bloom_vist_annotations_dict["stories"][story_id]

    filter_results = []
    for filter_method in metadata_for_story["filter_methods"].keys():
        filter_result = metadata_for_story["filter_methods"][filter_method]
        filter_results.append(filter_result["quarantine_result"])

    return any(filter_results)


def find_languages_where_not_all_stories_are_quarantined(
    bloom_vist_annotations_dict, code_normalization_dict
):

    langs_with_valid_stories = []
    if "stories" in bloom_vist_annotations_dict.keys():

        for story_id in bloom_vist_annotations_dict["stories"].keys():
            if story_quarantined(bloom_vist_annotations_dict, story_id):
                pass
            else:
                bloom_lang = bloom_vist_annotations_dict["stories"][story_id][
                    "bloom_lang"
                ]
                langs_with_valid_stories.append(bloom_lang)
    langs_with_valid_stories = list(set(langs_with_valid_stories))

    normalized_valid_langs = []
    for valid_lang in langs_with_valid_stories:
        normalized_valid_langs.append(code_normalization_dict[valid_lang])

    normalized_valid_langs = list(set(normalized_valid_langs))
    return normalized_valid_langs


if __name__ == "__main__":
    # json_path = "data/bloom_downloads_vist_filtered_by_license_2022-04-29T1141.json"
    json_path = (
        "data/bloom_downloads_vist_filtered_by_license_with_web_urls_2022-05-02.json"
    )

    json_path = "data/bloom_vist_june15.json"

    json_path = "bar/bloom_vist_june15_deduped_langfiltered.json"

    with open(json_path, "r") as jsf:
        data = json.load(jsf)
    annotations = data["annotations"]

    print(f"there are {len(annotations)}")

    langs = []
    for annotation in annotations:
        text = annotation[0]["text"]
        lang = annotation[0]["lang"]
        langs.append(lang)
    unique_langs = set(langs)

    normalized_langs = []
    code_normalization_dict = {}
    normalized_to_original_dict = {}
    just_the_languages = []
    display_names_for_normalized = {}
    for lang in unique_langs:
        langcodes_lang = langcodes.get(lang)
        normalized_lang = langcodes_lang.to_alpha3()
        just_the_languages.append(langcodes_lang.language)
        normalized_langs.append(normalized_lang)
        code_normalization_dict[lang] = normalized_lang
        normalized_to_original_dict[normalized_lang] = lang
        display_names_for_normalized[normalized_lang] = langcodes_lang.display_name()

    # going back the other way. Not 1 to 1.
    alpha3_to_bloom_langs_deconversion_dict = defaultdict(list)
    for original_bloom_bcp47 in unique_langs:
        alpha3 = code_normalization_dict[original_bloom_bcp47]
        alpha3_to_bloom_langs_deconversion_dict[alpha3].append(original_bloom_bcp47)
    # print(dict(alpha3_to_bloom_langs_deconversion_dict))
    alpha3_to_bloom_langs_deconversion_dict = dict(
        alpha3_to_bloom_langs_deconversion_dict
    )

    normalized_langs = list(set(normalized_langs))
    normalized_langs.sort()

    print()
    print()
    print()

    # print("UNIQUE BLOOM LANGUAGES")
    # print(f"#out of {len(langs)} text element langs, {len(unique_langs)} are unique. ")
    print(
        f"# all {len(unique_langs)} unique codes parsed from from bloom_downloads text fields"
    )
    print(f"_BLOOM_LANGUAGES={unique_langs}")
    print()
    # print("NORMALIZED LANGUAGES")
    # print(len(normalized_langs))

    # print("CODE NORMALIZATION DICT")
    print(
        f"# dictionary to convert from original language codes to alpha3. There's {len(code_normalization_dict.keys())} entries"
    )
    print(f"_BLOOM_LANGUAGES_ALPHA3_CONVERSION_DICT={code_normalization_dict}")
    print()

    # print("DISPLAY NAMES")
    print(
        "# display names, natural language. Calculated using langcodes library from alpha3 codes"
    )
    print(f"_BLOOM_LANGUAGES_ALPHA3_DISPLAY_NAMES={display_names_for_normalized}")
    print()

    # print("DECONVERSION_DICT")
    print(
        "# dictionary to deconvert from alpha3 to original. Note that it's not 1 to 1!"
    )
    print(
        f"# in this direction we've got only {len(alpha3_to_bloom_langs_deconversion_dict.keys())} entries"
    )
    print(
        f"_BLOOM_LANGUAGES_ALPHA3_DECONVERSION_DICT={alpha3_to_bloom_langs_deconversion_dict}"
    )
    print()

    unique_alpha3_codes = set([code_normalization_dict[lang] for lang in unique_langs])
    print(f"# unique alpha3 codes. {len(unique_alpha3_codes)} in total")
    print(f"_BLOOM_LANGUAGES_ALPHA3={unique_alpha3_codes}")
    print()

    languages_that_have_valid_stories = find_languages_where_not_all_stories_are_quarantined(
        data, code_normalization_dict
    )
    print(
        f"# Languages that have stories that aren't quarantined {len(languages_that_have_valid_stories)} in total"
    )
    print(f"_BLOOM_LANGUAGES_ALPHA3_VALID={languages_that_have_valid_stories}")
    print()

    # print("**************8")
    # print(normalized_to_original_dict)

    # print(len(code_normalization_dict))
    # print(len(normalized_to_original_dict))

    # just_the_languages.sort()
    # print(just_the_languages)

    # print("- ".join(normalized_langs))

    print("MARKDOWN FOR DATASET CARDS")
    # for alpha3 in normalized_langs:
    #     print(f"  - {alpha3}")

