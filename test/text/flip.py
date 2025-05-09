# Dictionary to map characters to their upside-down counterparts
UPSIDE_DOWN_MAP = {
    ",": "\u02bb",
    "!": "\u00a1",
    "?": "\u00bf",
    ".": "\u0387",
    "'": "\u02cc",
    '"': "\u02cc\u02cc",
    "*": "\u2093",
    "&": "\u214b",
    "1": "\u0196",
    "2": "\u0547",
    "3": "\u0190",
    "4": "h",
    "5": "\ud801\udc55",
    "6": "9",
    "7": "L",
    "9": "6",
    "A": "\u2c6f",
    "a": "\u0250",
    "B": "\ua4ed",
    "b": "q",
    "C": "\ua4db",
    "c": "\u0254",
    "D": "\ua4f7",
    "d": "p",
    "E": "\u018e",
    "e": "\u01dd",
    "F": "\ua4de",
    "f": "\u025f",
    "G": "\ua4e8",
    "g": "\u0253",
    "h": "\u0265",
    "i": "\u1d09",
    "J": "\u017f",
    "j": "\ua4e9",
    "K": "\ua4d8",
    "k": "\u029e",
    "L": "\ua4f6",
    "l": "\u0285",
    "M": "W",
    "m": "\u026f",
    "n": "u",
    "P": "\ua4d2",
    "p": "d",
    "Q": "\u1ff8",
    "q": "b",
    "R": "\ua4e4",
    "r": "\u0279",
    "T": "\ua4d5",
    "t": "\u0287",
    "U": "\ua4f5",
    "u": "n",
    "V": "\ua4e5",
    "v": "\u028c",
    "W": "M",
    "w": "\u028d",
    "Y": "\u2144",
    "y": "\u028e",
}


def flip_text_vertically(input_text):
    flipped_text = "".join(UPSIDE_DOWN_MAP.get(char, char) for char in input_text)
    return flipped_text[::-1]


input_text = "test"
flipped_text = flip_text_vertically(input_text)
print(flipped_text)
