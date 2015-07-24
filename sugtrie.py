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
        self.word_freq = 0
        self.children = {}
        self.branch_score = 0

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


class Completion(object):
    def __init__(self, completion=None, append_nodes=None):
        self.nodes = []
        self.score = 0
        if completion:
            self.nodes += completion.nodes
            self.score = completion.score
        if append_nodes:
            self.nodes += append_nodes
        if self.nodes:
            self.score = self.nodes[-1].word_freq

    def word(self):
        return ''.join([node.c for node in self.nodes])
    def __str__(self):
        word_freq = self.nodes[-1].word_freq if self.nodes else -1
        return "freq: %6i, score: %6i, word: %s" % (word_freq, self.score, self.word())
    def __cmp__(self, completion):
        return self.score - completion.score

class CharTrie(object):
    def __init__(self, verbose=False):
        self.root = CharNode('')

    @classmethod
    def find_completions(cls, partial, node):
        completions = []
        if node.word_end:
            completions.append(Completion(completion=partial, append_nodes=[node]))

        for k, v in sorted(node.children.iteritems(), key=lambda kv: kv[1].branch_score):
            completions += cls.find_completions(Completion(partial, [node]), node.children[k])
        return completions

    def find_prefix_matches(self, prefix):
        curr = self.root
        partial = Completion(append_nodes=[curr])
        for c in prefix:
            curr = curr.children.get(c)
            if not curr:
                return []
            partial.nodes.append(curr)

        node = partial.nodes[-1]
        partial.nodes = partial.nodes[:-1]
        return self.__class__.find_completions(partial, node)

    def __str__(self):
        return str(self.root)


class CharTrieBuilder(object):
    verbose = True
    @classmethod
    def add_word(cls, root, word, weight=1):
        curr = root
        for c in word:
            curr = curr.upsert_child_char(c)
            curr.branch_score += weight
        curr.word_end = True
        curr.word_freq = weight

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
        matches = sorted(matches, reverse=True)
        print '\n'.join(map(str, matches[:60]))

    trie = CharTrieBuilder.load_words_counts_from_json_file(WORD_COUNTS_JSON_FILEPATH)
    while True:
        process_input(trie)
