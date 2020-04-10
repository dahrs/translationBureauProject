#!/usr/bin/python
# -*- coding:utf-8 -*-


import json
from xml.etree import ElementTree as ET
from nltk.tokenize import word_tokenize


def dumpDictToJsonFile(aDict, pathOutputFile='./dump.json'):
    """
    save dict content in json file
    """
    import json
    # dumping
    with open(pathOutputFile, u'w') as dictFile:
        dictFile.write('')
        json.dump(aDict, dictFile)
    return


def make_tok_freq_dict(wikidump_path, output_path):
    freq_dict = {}
    xml_parser = ET.iterparse(wikidump_path)
    for xml_event, xml_elem in xml_parser:
        if xml_elem.tag.split("}")[1] == "text":
            # get all content
            article_content = xml_elem.text
            if type(article_content) is str:
                # tokenize
                article_tokens = word_tokenize(article_content)
                article_tokens = [t.split("|")[0] if "|" in t else t for t in article_tokens]
                # save to frequency dict
                for token in article_tokens:
                    if token not in freq_dict:
                        freq_dict[token] = 0
                    freq_dict[token] += 1
        xml_elem.clear()
    del freq_dict[""]
    dumpDictToJsonFile(freq_dict, output_path)


# make_tok_freq_dict("/home/d/Downloads/freq_tok/eswiki-20200401-pages-articles-multistream4.xml-p3119673p4080860",
#                    "/home/d/Downloads/freq_tok/esTok.json")
# make_tok_freq_dict("/home/d/Downloads/freq_tok/eswiki-20200401-pages-articles-multistream.xml",
#                    "/home/d/Downloads/freq_tok/esTok.json")


def make_reduced_freq_dict(tok_freq_dict_path, output_path, n=1000):
    with open(tok_freq_dict_path) as freq_file:
        freq_dict = json.load(freq_file)
        for k, v in dict(freq_dict).items():
            if v < n:
                del freq_dict[k]
    # dump
    dumpDictToJsonFile(freq_dict, output_path)

make_reduced_freq_dict("/home/d/Downloads/freq_tok/esTok.json",
                       "/home/d/Downloads/freq_tok/esTokTokReducedLessThan1000Instances.json", n=1000)