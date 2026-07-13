"""Simple word counting utility."""

import sys


def count_words(text):
    """Return the number of whitespace-separated words in text."""
    return len(text.split())


def main():
    if len(sys.argv) < 2:
        print("Usage: python wordcount.py <file>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        text = f.read()

    print(count_words(text))


if __name__ == "__main__":
    main()
