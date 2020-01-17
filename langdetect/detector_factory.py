import os
from os import path
import sys

try:
    import simplejson as json
except ImportError:
    import json

from .detector import Detector
from .lang_detect_exception import ErrorCode, LangDetectException
from .utils.lang_profile import LangProfile
from .language import Language

import mafan


class DetectorFactory(object):
    '''
    Language Detector Factory Class.

    This class manages an initialization and constructions of Detector.

    Before using language detection library,
    load profiles with DetectorFactory.load_profile(str, list)
    and set initialization parameters.

    You could also specify the pool of languages to make predictions
    from by specifying supported_languages.

    When the language detection,
    construct Detector instance via DetectorFactory.create().
    See also Detector's sample code.
    '''
    seed = None

    def __init__(self):
        self.word_lang_prob_map = {}
        self.langlist = []

    def load_profile(self, profile_directory, supported_languages=None):
        """
        Loads language profiles from the given directory.

        Args:
            profile_directory: path to the language profiles
            supported_languages: set of languages from which the predictions will be made;
            The languages should be in ISO 639-1 format (eg: "fr", "en", "de" and so on)
        """
        list_files = supported_languages if supported_languages else os.listdir(profile_directory)

        if not list_files:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Not found profile: ' + profile_directory)

        langsize, index = len(list_files), 0
        for filename in list_files:
            if filename.startswith('.'):
                continue
            filename = path.join(profile_directory, filename)
            if not path.isfile(filename):
                continue

            f = None
            try:
                if sys.version_info[0] < 3:
                    f = open(filename, 'r')
                else:
                    f = open(filename, 'r', encoding='utf-8')
                json_data = json.load(f)
                profile = LangProfile(**json_data)
                self.add_profile(profile, index, langsize)
                index += 1
            except IOError:
                raise LangDetectException(ErrorCode.FileLoadError, 'Cannot open "%s"' % filename)
            except:
                raise LangDetectException(ErrorCode.FormatError, 'Profile format error in "%s"' % filename)
            finally:
                if f:
                    f.close()

    def load_json_profile(self, json_profiles):
        langsize, index = len(json_profiles), 0
        if langsize < 2:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Need more than 2 profiles.')

        for json_profile in json_profiles:
            try:
                json_data = json.loads(json_profile)
                profile = LangProfile(**json_data)
                self.add_profile(profile, index, langsize)
                index += 1
            except:
                raise LangDetectException(ErrorCode.FormatError, 'Profile format error.')

    def add_profile(self, profile, index, langsize):
        lang = profile.name
        if lang in self.langlist:
            raise LangDetectException(ErrorCode.DuplicateLangError, 'Duplicate the same language profile.')
        self.langlist.append(lang)

        for word in profile.freq:
            if word not in self.word_lang_prob_map:
                self.word_lang_prob_map[word] = [0.0] * langsize
            length = len(word)
            if 1 <= length <= 3:
                prob = 1.0 * profile.freq.get(word) / profile.n_words[length - 1]
                self.word_lang_prob_map[word][index] = prob

    def clear(self):
        self.langlist = []
        self.word_lang_prob_map = {}

    def create(self, alpha=None):
        '''Construct Detector instance with smoothing parameter.'''
        detector = self._create_detector()
        if alpha is not None:
            detector.set_alpha(alpha)
        return detector

    def _create_detector(self):
        if not self.langlist:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Need to load profiles.')
        return Detector(self)

    def set_seed(self, seed):
        self.seed = seed

    def get_lang_list(self):
        return list(self.langlist)


PROFILES_DIRECTORY = path.join(path.dirname(__file__), 'profiles')
_factory = None
_supported_languages = None

def init_factory(supported_languages=None):
    global _factory
    global _supported_languages

    if _factory is None or _supported_languages != supported_languages:
        _supported_languages = supported_languages
        _factory = DetectorFactory()
        _factory.load_profile(PROFILES_DIRECTORY, _supported_languages)

def detect(text, supported_languages=None):
    init_factory(supported_languages=supported_languages)
    detector = _factory.create()
    detector.append(text)

    return detector.detect()

def is_chinese(predicted_language):
    return predicted_language in ["zh", "zh-tw"]

def predict_simplified_traditional(text, original_languages):
    predicted_language = "zh" if mafan.text.is_simplified(text) else "zh-tw"

    return [Language(lang=predicted_language, prob=original_languages[0].prob)]

def detect_langs(text, supported_languages=None):
    init_factory(supported_languages=supported_languages)
    detector = _factory.create()
    detector.append(text)
    predicted_languages = detector.get_probabilities()

    if is_chinese(predicted_languages[0].lang):
        return predict_simplified_traditional(text, predicted_languages)

    return detector.get_probabilities()
