#!/usr/bin/env python

import sys
import json

from collections import defaultdict
from pprint import pformat as pf

WORD_COUNTS_JSON_FILEPATH = "big.counts.json"

class CharNode(object):
    def __init__(self, c):
        self.c = c
        self.word_end = False
        self.word_weight = 0
        self.children = {}
        self.branch_weight = 0

    def upsert_child_char(self, c):
        if c not in self.children:
            self.children[c] = CharNode(c)
        return self.children[c]

    def to_dict(self):
        d = {}
        for k in sorted(self.children.iterkeys()):
            node = self.children[k]
            s = "%s$" % node.c if node.word_end else node.c
            d[s] = node.to_dict()
        return d

    def __str__(self):
        return pf(self.to_dict())


class CharTrie(object):
    def __init__(self, verbose=False):
        self.root = CharNode('')

    @classmethod
    def find_completions(cls, prefix, node):
        completions = []
        if node.word_end:
            completions.append(prefix + node.c)

        for k, v in sorted(node.children.iteritems(), key=lambda kv: kv[1].branch_weight):
            completions += cls.find_completions(prefix + node.c, node.children[k])
        return completions

    def find_prefix_matches(self, prefix):
        curr = self.root
        for c in prefix:
            curr = curr.children.get(c)
            if not curr:
                return []
        return self.__class__.find_completions(prefix[:-1], curr)

    def __str__(self):
        return str(self.root)


class CharTrieBuilder(object):
    verbose = True
    @classmethod
    def add_word(cls, root, word, weight=1):
        curr = root
        for c in word:
            curr = curr.upsert_child_char(c)
            curr.branch_weight += weight
        curr.word_end = True
        curr.word_weight = weight

    @classmethod
    def load_words_counts_from_json_file(cls, filepath):
        trie = CharTrie()
        if cls.verbose: print "Loading words from %s" % filepath
        with open(filepath) as f:
            counts = json.loads(f.read())
            i = 0
            for word, count in counts.iteritems():
                i += 1
                cls.print_load_progress(i, word)
                cls.add_word(trie.root, word, count)
        if cls.verbose: print " ...done."
        return trie

    @classmethod
    def print_load_progress(cls, i, word):
        if not cls.verbose:
            return
        rpadding = ' '*(30 - len(word))
        sys.stdout.write("\r%8i: %s%s" % (i, word, rpadding))
        sys.stdout.flush()


if __name__=='__main__':
    def process_input(trie):
        print "\nEnter text:",
        w = raw_input()
        if not w:
            return
        matches = trie.find_prefix_matches(w.lower())
        print "Found %i suggestions:\n===============" % len(matches)
        print '\n'.join(matches[:50])

    trie = CharTrieBuilder.load_words_counts_from_json_file(WORD_COUNTS_JSON_FILEPATH)
    while True:
        process_input(trie)
