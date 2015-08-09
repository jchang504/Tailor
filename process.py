'''Process raw lyrics text files into dictionaries containing all the data
needed to generate new songs.
'''
import re
from collections import Counter

LYRICS_TOKEN_REGEX = re.compile(r"([\w'-:]+|[?!,;.]+)")
PAREN_PHRASES_REGEX = re.compile(r'\(.*\)')
START_LINE_TOKEN = '<START>'
END_LINE_TOKEN = '<END>'

# Data dictionary keys
UNIGRAMS = 'uni'
BIGRAMS = 'bi'
LINES_PER_VERSE = 'lpv'
TOKENS_PER_LINE = 'tpl'

def aggregate_data(lyrics_data_list):
    '''Aggregate data about multiple songs' lyrics.

    Given a list of data dictionaries of the form returned by collect_data,
    combines the data into a single dictionary of the same form by adding
    Counters together.
    '''
    total_unigrams = Counter()
    total_bigrams = {} # string -> Counter(string -> int)
    total_lines_per_verse = Counter()
    total_tokens_per_line = Counter()

    for lyrics_data in lyrics_data_list:
        total_unigrams += lyrics_data[UNIGRAMS]
        total_lines_per_verse += lyrics_data[LINES_PER_VERSE]
        total_tokens_per_line += lyrics_data[TOKENS_PER_LINE]

        bigrams = lyrics_data[BIGRAMS]
        for first_word in bigrams:
            counter = total_bigrams.get(first_word)
            if counter is None: # First encounter of first_word
                total_bigrams[first_word] = bigrams[first_word]
            else:
                total_bigrams[first_word] = counter + bigrams[first_word]

    return {UNIGRAMS: total_unigrams, BIGRAMS: total_bigrams, LINES_PER_VERSE:
            total_lines_per_verse, TOKENS_PER_LINE: total_tokens_per_line}


def collect_data(song_lyrics):
    '''Collect data about a song's lyrics.

    Arguments:
    - song_lyrics: a string containing the song's lyrics, where each line is
        separated by \n, and each verse is separated by a blank line
    Information collected:
    - Count the unigrams and bigrams
    - Frequency distribution of number of lines per verse
    - Frequency distribution of number of tokens per line
    '''
    unigrams = Counter()
    bigrams = {} # string -> Counter(string -> int)
    lines_per_verse = Counter()
    tokens_per_line = Counter()

    current_lines = 0
    for line in song_lyrics.splitlines():
        uncap_line = smart_uncapitalize(line)
        tokens = tokenize(uncap_line) # Avoid distinguishing first word of line
        len_tokens = len(tokens)

        if len_tokens > 0:
            for i in xrange(len_tokens):
                unigrams[tokens[i]] += 1

                if i == 0: # First token: count START bigram
                    count_bigram((START_LINE_TOKEN, tokens[i]), bigrams)
                if i < len_tokens - 1: # Not last token of line: count bigram
                    count_bigram((tokens[i], tokens[i+1]), bigrams)
                else: # Last token: count END bigram
                    count_bigram((tokens[i], END_LINE_TOKEN), bigrams)

            tokens_per_line[len_tokens] += 1
            current_lines += 1

        else: # Blank line: end of verse
            lines_per_verse[current_lines] += 1
            current_lines = 0

    return {UNIGRAMS: unigrams, BIGRAMS: bigrams, LINES_PER_VERSE:
            lines_per_verse, TOKENS_PER_LINE: tokens_per_line}

def compute_frequencies(lyrics_data):
    '''Compute frequency distributions for some lyrics data.

    Given a data dictionary of the form returned by collect_data, returns a
    data dictionary with the same keys, but counts converted to probabilities.
    '''
    unigram_frequencies = frequency_dict_from_counter(lyrics_data[UNIGRAMS])
    bigram_frequencies = {first_word: frequency_dict_from_counter(counter) for
            first_word, counter in lyrics_data[BIGRAMS].iteritems()}
    lpv_frequencies = frequency_dict_from_counter(lyrics_data[LINES_PER_VERSE])
    tpl_frequencies = frequency_dict_from_counter(lyrics_data[TOKENS_PER_LINE])

    return {UNIGRAMS: unigram_frequencies, BIGRAMS: bigram_frequencies,
            LINES_PER_VERSE: lpv_frequencies, TOKENS_PER_LINE: tpl_frequencies}

def count_bigram(bigram, bigrams_map):
    '''Count an occurrence of bigram in bigrams_map.

    Arguments:
    bigram - a tuple of strings (first_word, second_word) representing a bigram
    bigrams_map - a dictionary mapping bigram first words to (Counters mapping
            second words to counts)
    '''
    (first_word, second_word) = bigram
    counter = bigrams_map.get(first_word)

    if counter is None: # First encounter of first_word
        bigrams_map[first_word] = Counter({second_word: 1})
    else:
        counter[second_word] += 1

def frequency_dict_from_counter(counter):
    '''Maps a counter to a frequency dictionary.

    The result dictionary has the same keys as the counter, but the values are
    the counts divided by the total of all counts.
    '''
    counts_total = sum(counter.values())
    frequencies = {}

    for key in counter:
        frequencies[key] = float(counter[key]) / counts_total

    return frequencies

def smart_uncapitalize(string):
    '''Uncapitalize a string correctly even if it begins with punctuation.

    Also avoid uncapitalizing a first person subject pronoun (I, I'm, etc.).
    '''
    if string.startswith('I ') or string.startswith("I'"):
        return string

    for i in xrange(len(string)):
        if string[i].isalpha():
            return string[:i] + string[i].lower() + string[i+1:]
        elif string[i] == ' ': # Don't uncapitalize past first word
            break

    return string

def tokenize(line):
    '''Split a line into tokens.

    First remove (parenthesized phrases), then match strings of word or
    punctuation characters.
    '''
    return LYRICS_TOKEN_REGEX.findall(PAREN_PHRASES_REGEX.sub('', line))
