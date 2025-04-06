def emojie():
    emoji_map = {
        "0": ":zero:",
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
        "9": ":nine:",
        " ": ":black_large_square:",
        ".": ":radio_button:",
        "!": ":grey_exclamation:",
        "?": ":grey_question:",
        "ä": ":regional_indicator_a::regional_indicator_e:",
        "ö": ":regional_indicator_o::regional_indicator_e:",
        "ü": ":regional_indicator_u::regional_indicator_e:",
        "ß": ":regional_indicator_s::regional_indicator_s:",
    }

    def text_to_emoji(text):
        result = ""
        for char in text.lower():
            if char in emoji_map:
                result += emoji_map[char]
            elif char.isalpha():
                result += f":regional_indicator_{char}:"
            else:
                result += char
        return result

    input_text = "text"
    emoji_text = text_to_emoji(input_text)
    print(emoji_text)
