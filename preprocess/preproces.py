import re
urlReg = r"^(?:([A-Za-z]+):)?(\/{0,3})([0-9.\-A-Za-z]+)(?::(\d+))?(?:\/([^?#]*))?(?:\?([^#]*))?(?:#(.*))?$"
entityRe = r'\[\@.*?\#.*?\*\](?!\#)'


def getLabelPair(text):
    new_string_list = text.strip('[@*]').rsplit('#', 1)
    par_text = new_string_list[0]
    label = new_string_list[1]
    return {"text": par_text, "label": label}


def removeLabel(text):
    return text.replace("[@", "").rsplit('#', 1)[0]


class MergeFollows:
    def __init__(self, document, isBMES=False):
        self.text = document
        self.isBMES = isBMES
        self._start = "start"
        self._unTAG = "unTAG"
        self._item = "item"
        self.par_list = self.text.split('\n')
        if isBMES:
            self.par_dict = [{"par": getLabelPair(par)["text"],
                              "tag": self._unTAG,
                              "label": getLabelPair(par)["label"]}
                             if re.search(entityRe, par) 
                             else {"par": par, 
                                   "tag": self._unTAG,
                                   "label": "Other"}
                             for par in self.par_list]

        else:
            self.par_dict = [{"par": par, "tag": self._unTAG} for par in self.par_list]
        self._merged_par = []
        self.theEndofStr = ("or", "and", ";")
        self._initDict()

    def _initDict(self):
        for key, item in enumerate(self.par_dict):
            text = item["par"]
            #  as follows: check if have :
            if self._isStart(text):
                self.par_dict[key]["tag"] = self._start
            # after :, the first str must be the item
            elif key != 0 and self.par_dict[key-1]["tag"] == self._start:
                self.par_dict[key]["tag"] = self._item
            # ignore the \n between start and item and set the first str (after : and \n) is item
            elif self._maybeItem(key, notNULL=False) and len(self.par_dict[key - 1]["par"]) == 0:
                self.par_dict[key]["tag"] = self._item
                if key + 1 != len(self.par_dict):
                    self.par_dict[key+1]["tag"] = self._item
            # if the fist char is special char
            elif self._maybeItem(key) and not text.strip()[0].isalnum():
                self.par_dict[key]["tag"] = self._item
            # such as "to access  your personal information."
            elif self._maybeItem(key) and text.strip()[:2].lower() == "to ":
                self.par_dict[key]["tag"] = self._item
            # such as "Request a structured electronic version of your information;"
            # or "Request a structured electronic version of your information; and"
            # Besides set the next str to the item
            elif self._maybeItem(key) and text.strip().endswith(self.theEndofStr):
                self.par_dict[key]["tag"] = self._item
                if key + 1 != len(self.par_dict):
                    self.par_dict[key + 1]["tag"] = self._item
            # the last item is start with number end this item is also start with item
            elif self._maybeItem(key) and text.strip()[0].isdigit() and self.par_dict[key - 1]["par"][0].isdigit():
                self.par_dict[key]["tag"] = self._item
            # the link of third party
            elif self._maybeItem(key) and self._calUrl(text) > 0.5:
                self.par_dict[key]["tag"] = self._item
            else:
                pass

    def _maybeItem(self, key, notNULL=True):
        if notNULL:
            maybe = key != 0 and self.par_dict[key - 1]["tag"] != self._unTAG and len(self.par_dict[key]["par"].strip()) > 0
        else:
            maybe = key != 0 and self.par_dict[key - 1]["tag"] != self._unTAG and len(self.par_dict[key]["par"].strip()) == 0
        return maybe

    @staticmethod
    def _isStart(paragraph):
        return True if len(paragraph.strip()) > 0 and paragraph.strip()[-1] == ":" else False

    @staticmethod
    def _calUrl(text):
        max_url_ken = 0
        if len(text.strip()) > 0:
            for i in text.split(" "):
                url = re.search(urlReg, i)
                if url and len(url.group()) / len(text) > max_url_ken:
                    max_url_ken = len(url.group()) / len(text)
        return max_url_ken

    @property
    def mergeBMESPair(self):
        if self.isBMES:
            for key, item in enumerate(self.par_dict):
                if item["tag"] == self._unTAG or item["tag"] == self._start:
                    self._merged_par.append({"par": item["par"], "label": item["label"]})
                else:
                    self._merged_par[-1]["par"] += item["par"]
        else:
            for key, item in enumerate(self.par_dict):
                if item["tag"] == self._unTAG or item["tag"] == self._start:
                    self._merged_par.append({"par": item["par"], "label": "None"})
                else:
                    self._merged_par[-1]["par"] += item["par"]
        return self._merged_par

    @property
    def merge(self):
        for key, item in enumerate(self.par_dict):
            if item["tag"] == self._unTAG or item["tag"] == self._start:
                self._merged_par.append(item["par"])
            else:
                self._merged_par[-1] += item["par"]
        return self._merged_par


