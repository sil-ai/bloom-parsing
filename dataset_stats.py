from enum import unique
import json
import langcodes

if __name__ == "__main__":
    # json_path = "data/bloom_downloads_vist_filtered_by_license_2022-04-29T1141.json"
    json_path = (
        "data/bloom_downloads_vist_filtered_by_license_with_web_urls_2022-05-02.json"
    )
    with open(json_path, "r") as jsf:
        data = json.load(jsf)
    annotations = data["annotations"]

    print(f"there are {len(annotations)}")

    langs = []
    for annotation in annotations:
        textdict = annotation[0]["text"]
        langs_in_text = textdict.keys()
        langs.extend(langs_in_text)
    unique_langs = set(langs)
    print(f"out of {len(langs)} text element langs, {len(unique_langs)} are unique. ")
    print(unique_langs)

    normalized_langs = []
    code_normalization_dict = {}
    normalized_to_original_dict = {}
    just_the_languages = []
    for lang in unique_langs:
        langcodes_lang = langcodes.get(lang)
        normalized_lang = langcodes_lang.to_alpha3()
        just_the_languages.append(langcodes_lang.language)
        normalized_langs.append(normalized_lang)
        code_normalization_dict[lang] = normalized_lang
        normalized_to_original_dict[normalized_lang] = lang

    normalized_langs = list(set(normalized_langs))
    normalized_langs.sort()
    print(len(normalized_langs))

    # print(code_normalization_dict)
    # print("**************8")
    # print(normalized_to_original_dict)

    # print(len(code_normalization_dict))
    # print(len(normalized_to_original_dict))

    # just_the_languages.sort()
    # print(just_the_languages)
    for alpha3 in normalized_langs:
        print(f"  - {alpha3}")
    # print("- ".join(normalized_langs))

