import enum
import math
import string

class Keys(enum.Enum):
    nb_markdown = "markdown"
    nb_metadata = "metadata"
    nb_raw = "raw"
    nb_source = "source"
    td_cell_index = "tiedown.cell_index"

class Commands(enum.Enum):
    index = "index"
    target = "target"
    toc_entry = "toc_entry"
    toc_exclude = "toc_exclude"


def roman_from_int(number, lower=False):
    """Converts an integer to a Roman numeral.

    Args:
        Number: an integer > 1 and < 3899
        lower: optional bool, defauts to False. Output is lower case if
            True.

    Raises ValueError if number < 1 or > 3899
    
    Returns: String.
    """
    if number > 3899 or number < 1:
        raise ValueError("Input must range from 0 to 3999.")
    # Storing roman values of digits from 0-9
    # when placed at different places
    m = ["", "M", "MM", "MMM"]
    c = ["", "C", "CC", "CCC", "CD", "D",
        "DC", "DCC", "DCCC", "CM "]
    x = ["", "X", "XX", "XXX", "XL", "L",
        "LX", "LXX", "LXXX", "XC"]
    i = ["", "I", "II", "III", "IV", "V",
        "VI", "VII", "VIII", "IX"]

    # Converting to roman
    thousands = m[number // 1000]
    hundreds = c[(number % 1000) // 100]
    tens = x[(number % 100) // 10]
    ones = i[number % 10]

    ans = (thousands + hundreds +
        tens + ones)

    return ans.lower() if lower else ans


def letters_from_int(number, lower=False):
    """Converts an integer to letters, similar to Excel column names.

    Args:
        Number: an integer > 1
        lower: optional bool, defauts to False. Output is lower case if
            True.

    Raises ValueError if number < 1
    
    Returns: String. 1 -> A, 26 -> Z, 27 -> AZ, 53 -> BZ, etc.
    """
    if number < 1:
        raise ValueError("Input must be an integer greater than one.")
    alphabet = string.ascii_lowercase if lower else string.ascii_uppercase
    letters = []
    num_letters = max(math.ceil(math.log(number, 26)), 1)
    for i in range(num_letters, 0, -1):
        place = 26**(i-1)
        digit = number // place
        letters.append(alphabet[digit-1])
        number -= place * digit
    return "".join(letters)


outline_mapper = {
    "I": roman_from_int,
    "i": lambda x: roman_from_int(x, lower=True),
    "A": letters_from_int,
    "a": lambda x: letters_from_int(x, lower=True),
    "1": str,
    "": lambda x: ""
}

def get_counter(outline_format):
    MAX_LEVELS = 6
    levels = outline_format.split(".")
    if len(levels) > MAX_LEVELS:
        raise ValueError("Outline format can have no more than five levels.")
    while len(levels) < MAX_LEVELS:
        levels.append("")
    return [outline_mapper[level] for level in levels]