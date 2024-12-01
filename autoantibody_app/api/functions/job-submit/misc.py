# Built-in/Generic Imports
import os
import json
from pathlib import Path

# Third-party Imports
from shortuuid import ShortUUID
from wonderwords import RandomWord, Defaults

def mnemonic_hash(
    word_min_length=3,
    word_max_length=8,
    uuid_length = 7,
    uuid_alphabet = "23456789BCDFGHJKLMNPQRSTVWXYZbcdfghjkmnpqrstvwxyz"
):

    # Create a UUID in Base49
    uuid = ShortUUID(alphabet=uuid_alphabet).random(length=uuid_length)

    # Use an extended list of words
    # TODO: if this becomes a package, use importlib.resources
    # Custom adjectives
    adjectives_file = "assets/word-lists/adjectives.tsv"
    with open(Path(__file__).parent.joinpath(adjectives_file), "r") as f:
        adjectives = f.readlines()
    adjectives = [word.strip() for word in adjectives]
    # Custom nouns
    nouns_file = "assets/word-lists/nouns.tsv"
    with open(Path(__file__).parent.joinpath(nouns_file), "r") as f:
        nouns = f.readlines()
    nouns = [word.strip() for word in nouns]

    # When creating the generator, if one of the categories will be custom, we 
    # have to define the others we would like to keep with the Defaults lists.
    # E.g. custom adjectives, default nouns
    #   generator = RandomWord(adjective=adjectives, noun=Defaults.NOUNS)
    generator = RandomWord(adjective=adjectives, noun=nouns)

    # Pick a random word from each categorical list. Words should only contain 
    # letters (no hyphens or spaces), and be between 3-16 characters long.
    categories = ["adjective", "noun"]
    words = []
    for category in categories:
        words.append(
            generator.word(
                include_categories=[category], 
                word_min_length=word_min_length, 
                word_max_length=word_max_length, 
                regex="[A-Za-z]+"
            )
        )

    return "_".join(words + [uuid])
