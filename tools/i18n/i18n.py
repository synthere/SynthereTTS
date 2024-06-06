import json
import locale
import os

import os,sys
def load_language_list(languagef):
    with open(languagef, "r", encoding="utf-8") as f:
        language_list = json.load(f)
    return language_list


class I18nAuto:
    def __init__(self, language=None):
        if language in ["Auto", None]:
            language = locale.getdefaultlocale()[
                0
            ]  # getlocale can't identify the system's language ((None, None))
        self.base_path = self.get_base_path()
        lp = "./i18n/locale/" + language + ".json"
        langp = os.path.join(self.base_path, lp)
        if not os.path.exists(langp):
            language = "en_US"
        self.language = language
        lp = "./i18n/locale/" + language + ".json"
        langp = os.path.join(self.base_path, lp)
        self.language_map = load_language_list(langp)

    def get_base_path(self):
        if getattr(sys, 'frozen', False):  # 是否Bundle Resource
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return base_path

    def __call__(self, key):
        return self.language_map.get(key, key)

    def __repr__(self):
        return "Use Language: " + self.language
