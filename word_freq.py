#!/usr/bin/env python

from collections import Counter
import re


def build_bag_of_words(text):
    return re.findall('[a-z]+', text.lower())

def build_word_counts(text):
    word_list = build_bag_of_words(text)
    return Counter(word_list)

if __name__=='__main__':
    import sys, json
    raw_text = sys.stdin.read()
    counts = build_word_counts(raw_text)

    total = float(sum(counts.values()))
    probabilities = {}
    for k, v in counts.iteritems():
        probabilities[k] = v / total

    print json.dumps({'counts': dict(counts),
                      'probabilities': probabilities})
