import re
import json
import pandas as pd
urlReg = r"^(?:([A-Za-z]+):)?(\/{0,3})([0-9.\-A-Za-z]+)(?::(\d+))?(?:\/([^?#]*))?(?:\?([^#]*))?(?:#(.*))?$"
entityRe = r'\[\@.*?\#.*?\*\](?!\#)'


def getLabelPair(text):
    label_pair = re.search(entityRe, text)
    if label_pair:
        new_string_list = label_pair.group().strip('[@*]').rsplit('#', 1)
        par_text = new_string_list[0]
        label = new_string_list[1]
        label = "Legal Basis" if label.lower() == "legal basis" else label
        label = "User Control" if label == "User Choice/Control" else label
        sentiment = 0
    else:
        par_text = text
        label = "Other"
        sentiment = 0
    return {"text": par_text, "label": label, "sentiment": sentiment}


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
                             for par in self.par_list]

        else:
            self.par_dict = [{"par": par, "tag": self._unTAG} for par in self.par_list]
        self._merged_par = []
        self.theEndofStr = ("or", "and", ";")
        self._initDict()

    def _initDict(self):
        for key, item in enumerate(self.par_dict):
            text = item["par"].strip()
            last = self._getLastItem(key)
            next = self._getNextItem(key)
            #  as follows: check if have :
            if self._isStart(text):
                self.par_dict[key]["tag"] = self._start
            # after :, the first str must be the item
            elif key != 0 and self.par_dict[key-1]["tag"] == self._start:
                self.par_dict[key]["tag"] = self._item
            # ignore the \n between start and item and set the first str (after : and \n) is item
            elif self._maybeItem(key, notNULL=False) and len(last) == 0:
                self.par_dict[key]["tag"] = self._item
                if key + 1 != len(self.par_dict):
                    self.par_dict[key+1]["tag"] = self._item
            # if the fist char is special char
            elif self._maybeItem(key) and not text[0].isalnum():
                self.par_dict[key]["tag"] = self._item
            elif self._maybeItem(key, notNULL=False) and not last[0].isalnum() and last[0] == next[0]:
                self.par_dict[key]["tag"] = self._item
            # such as "to access  your personal information."
            elif self._maybeItem(key) and text[:2].lower() == "to ":
                self.par_dict[key]["tag"] = self._item
            elif self._maybeItem(key, notNULL=False) and last[:2].lower() == "to " and last[:2] == next[:2]:
                self.par_dict[key]["tag"] = self._item
            # such as "Request a structured electronic version of your information;"
            # or "Request a structured electronic version of your information; and"
            # Besides set the next str to the item
            elif self._maybeItem(key) and text.endswith(self.theEndofStr):
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

    def _getLastItem(self, key):
        return self.par_dict[key - 1]["par"].strip() \
            if key != 0 and len(self.par_dict[key - 1]["par"].strip()) > 0 else "null"

    def _getNextItem(self, key):
        return self.par_dict[key + 1]["par"].strip() \
            if key+1 != len(self.par_dict) and len(self.par_dict[key + 1]["par"].strip()) else "null"

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


class CalDataLabel():
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        label_set = set(self.data.label)
        with open("./label.json", "r", encoding="utf8") as f:
            self.label_dict = json.load(f)
        self.split = 0.2

    def summary(self):
        summ = dict()
        summ["all_words"] = self.data.par_length.sum()
        summ["all_sent"] = self.data.sent_num.sum()
        summ["annotated_data"] = self.data[self.data.label != "Other"].count()[0]
        summ["annotators_num"] = 3
        summ["annotators_per_pp"] = 3
        summ["annotated_w"] = self.data[self.data.label != "Other"].par_length.sum()
        summ["annotated_s"] = self.data[self.data.label != "Other"].sent_num.sum()
        print("-------Summary--------")
        for key, item in summ.items():

            print(key + ":   " + str(item))

    def cal_label(self, out_path):
        # Based on the paragraph calculate the words and sentences
        pd.DataFrame(self.data[self.data.label != "Other"].par_length.describe()).to_csv(out_path+"data_status_word.csv")
        pd.DataFrame(self.data[self.data.label != "Other"].sent_num.describe()).to_csv(out_path + "data_status_sent.csv")
        label_group = self.data.groupby("label")
        doc_group = self.data.groupby("doc_id")

        # Based on the label calculate the words and sentences every paragraph
        pd.DataFrame(label_group.par_length.describe()).to_csv(out_path+"label_status_word.csv")
        pd.DataFrame(label_group.sent_num.describe()).to_csv(out_path + "label_status_sent.csv")

        # Calculate the size of label
        pd.DataFrame(label_group.size()).to_csv(out_path+"label_size.csv")

        # Based on the Document calculate the words and sentences
        doc_par_num = pd.DataFrame(doc_group.par_length.count().describe())
        doc_status_word = pd.DataFrame(doc_group.par_length.sum().describe())
        doc_status_sent = pd.DataFrame(doc_group.sent_num.sum().describe())
        pd.concat([doc_status_word, doc_status_sent], axis=1).to_csv(out_path+"doc_status.csv")

    def extract_train_data(self, out_path):
        data = self.data[self.data.label != "Other"]
        document_index = data.doc_id.drop_duplicates()
        # print(document)
        dev_index = document_index.sample(frac=self.split, random_state=666)

        train_index = document_index[~document_index.index.isin(dev_index.index)]
        train = data[data.doc_id.isin(train_index)].sample(frac=1, random_state=666)
        dev = data[data.doc_id.isin(dev_index)].sample(frac=1, random_state=666)

        train_data = []
        dev_data = []
        for i, row in train.iterrows():
            train_data.append([self.label_dict[row["label"]], row["par"]])
        for i, row in dev.iterrows():
            dev_data.append([self.label_dict[row["label"]], row["par"]])
        pd.DataFrame(train_data).to_csv(out_path+"train_data.tsv", sep="\t")
        pd.DataFrame(dev_data).to_csv(out_path+"dev_data.tsv", sep="\t")
