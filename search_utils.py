import difflib

def compare_strings(str1, str2):
    diff = difflib.ndiff(str1.splitlines(), str2.splitlines())
    similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
    return '\n'.join(diff), similarity

def similarity(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).ratio()
