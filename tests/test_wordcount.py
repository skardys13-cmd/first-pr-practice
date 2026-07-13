import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordcount import count_words


def test_basic_sentence():
    assert count_words("the quick brown fox") == 4


def test_single_word():
    assert count_words("hello") == 1


def test_empty_string():
    assert count_words("") == 0
