"""
For each profile, remove ngrams that do not belong to that language.
Reference: https://github.com/Mimino666/langdetect/pull/9
"""

import json


def is_in_language(ngram, begin_unicode_range, end_unicode_range):
    """
    Checks if all the characters in the ngram are in the unicode range
    of the language.
    """
    for character in ngram:
        if not (begin_unicode_range <= ord(character) <= end_unicode_range):
            return False

    return True


def remove_foreign_ngrams(
    ngram_freq,
    begin_unicode_range,
    end_unicode_range
):
    """
    Removes ngrams that do not belong to the particular language.
    """
    ngram_dict = {}

    for ngram, freq in ngram_freq.items():
        if is_in_language(
            ngram=ngram.strip(),
            begin_unicode_range=begin_unicode_range,
            end_unicode_range=end_unicode_range
        ):
            ngram_dict[ngram] = freq

    return ngram_dict


def fix_profile(file_name, begin_unicode_range, end_unicode_range):
    """
    Fixes the given language profile.    
    """
    profile_json_dict = json.load(open(file_name))

    ngram_data = {}

    for key, value in profile_json_dict.items():
        # Only clean the characters in the frequency part of the profile file
        if key == "freq":
            ngram_vector = remove_foreign_ngrams(
                value,
                begin_unicode_range,
                end_unicode_range
            )
            ngram_data[key] = ngram_vector
        else:
            ngram_data[key] = value

    with open(file_name, "w") as profile_handle:
        json.dump(ngram_data, profile_handle, ensure_ascii=False)



root_dir = "./langdetect/profiles"
fix_profile(f"{root_dir}/ko", 0xAC00, 0xD7AF)
fix_profile(f"{root_dir}/th", 0x0E00, 0x0E7F)
fix_profile(f"{root_dir}/hi", 0x0900, 0x097F)
fix_profile(f"{root_dir}/pa", 0x0A00, 0x0A7F)
fix_profile(f"{root_dir}/ru", 0x0400, 0x052F)
