import re

import yaml


def lolcat(phrase, dictionary_file="assets/data/tranzlator.yml"):
    with open(dictionary_file, "r", encoding="utf-8") as file:
        dictionary = yaml.safe_load(file)

    lines = phrase.split("\n")
    translated_lines = []

    for line in lines:
        words = re.split(r"[ ,.!\n]+", line)
        translated_words = [dictionary.get(word, word) for word in words]
        translated_lines.append(" ".join(translated_words))

    return "\n".join(translated_lines).strip()
