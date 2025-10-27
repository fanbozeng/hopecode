"""
Comprehensive Stopwords Database


This module provides comprehensive stopword collections for English and Chinese
to filter out common, non-informative words during text processing.



"""

# ============================================================
# ENGLISH STOPWORDS / 
# ============================================================

ENGLISH_ARTICLES = {
    'a', 'an', 'the'
}

ENGLISH_PRONOUNS = {
    'i', 'me', 'my', 'mine', 'myself',
    'you', 'your', 'yours', 'yourself', 'yourselves',
    'he', 'him', 'his', 'himself',
    'she', 'her', 'hers', 'herself',
    'it', 'its', 'itself',
    'we', 'us', 'our', 'ours', 'ourselves',
    'they', 'them', 'their', 'theirs', 'themselves',
    'who', 'whom', 'whose', 'which', 'what',
    'this', 'that', 'these', 'those',
    'one', 'ones', 'someone', 'something', 'anyone', 'anything',
    'everyone', 'everything', 'nobody', 'nothing'
}

ENGLISH_AUXILIARY_VERBS = {
    'be', 'is', 'am', 'are', 'was', 'were', 'been', 'being',
    'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'done',
    'will', 'would', 'shall', 'should',
    'can', 'could', 'may', 'might', 'must',
    'ought', 'need', 'dare', 'used'
}

ENGLISH_PREPOSITIONS = {
    'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by',
    'about', 'as', 'into', 'like', 'through', 'after', 'over',
    'between', 'out', 'against', 'during', 'without', 'before',
    'under', 'around', 'among', 'throughout', 'despite', 'towards',
    'upon', 'concerning', 'off', 'above', 'below', 'across',
    'behind', 'beyond', 'plus', 'except', 'but', 'up', 'down',
    'near', 'along', 'until', 'within', 'since', 'via'
}

ENGLISH_CONJUNCTIONS = {
    'and', 'or', 'but', 'nor', 'so', 'yet', 'for',
    'if', 'unless', 'while', 'because', 'although', 'though',
    'since', 'when', 'whenever', 'where', 'wherever', 'whether',
    'than', 'that', 'as', 'after', 'before', 'once', 'until'
}

ENGLISH_DETERMINERS = {
    'all', 'another', 'any', 'both', 'each', 'either', 'every',
    'few', 'many', 'more', 'most', 'much', 'neither', 'no',
    'other', 'several', 'some', 'such', 'less', 'fewer'
}

ENGLISH_ADVERBS = {
    'very', 'too', 'quite', 'rather', 'really', 'so', 'just',
    'only', 'even', 'also', 'still', 'yet', 'already', 'always',
    'never', 'often', 'sometimes', 'usually', 'frequently',
    'rarely', 'seldom', 'hardly', 'barely', 'nearly', 'almost',
    'not', 'no', 'yes', 'again', 'once', 'twice', 'ever',
    'here', 'there', 'where', 'everywhere', 'anywhere', 'nowhere',
    'then', 'now', 'today', 'yesterday', 'tomorrow', 'soon',
    'later', 'earlier', 'recently', 'currently', 'presently',
    'how', 'why', 'when', 'well', 'better', 'best', 'worse', 'worst'
}

ENGLISH_QUESTION_WORDS = {
    'what', 'which', 'who', 'whom', 'whose', 'when', 'where',
    'why', 'how', 'whichever', 'whoever', 'whomever', 'whenever',
    'wherever', 'however'
}

ENGLISH_COMMON_VERBS = {
    'go', 'goes', 'going', 'gone', 'went',
    'come', 'comes', 'coming', 'came',
    'get', 'gets', 'getting', 'got', 'gotten',
    'make', 'makes', 'making', 'made',
    'take', 'takes', 'taking', 'took', 'taken',
    'see', 'sees', 'seeing', 'saw', 'seen',
    'know', 'knows', 'knowing', 'knew', 'known',
    'think', 'thinks', 'thinking', 'thought',
    'want', 'wants', 'wanting', 'wanted',
    'give', 'gives', 'giving', 'gave', 'given',
    'use', 'uses', 'using', 'used',
    'find', 'finds', 'finding', 'found',
    'tell', 'tells', 'telling', 'told',
    'ask', 'asks', 'asking', 'asked',
    'work', 'works', 'working', 'worked',
    'seem', 'seems', 'seeming', 'seemed',
    'feel', 'feels', 'feeling', 'felt',
    'try', 'tries', 'trying', 'tried',
    'leave', 'leaves', 'leaving', 'left',
    'call', 'calls', 'calling', 'called',
    'keep', 'keeps', 'keeping', 'kept',
    'let', 'lets', 'letting',
    'begin', 'begins', 'beginning', 'began', 'begun',
    'show', 'shows', 'showing', 'showed', 'shown',
    'hear', 'hears', 'hearing', 'heard',
    'play', 'plays', 'playing', 'played',
    'run', 'runs', 'running', 'ran',
    'move', 'moves', 'moving', 'moved',
    'live', 'lives', 'living', 'lived',
    'believe', 'believes', 'believing', 'believed',
    'hold', 'holds', 'holding', 'held',
    'bring', 'brings', 'bringing', 'brought',
    'happen', 'happens', 'happening', 'happened',
    'write', 'writes', 'writing', 'wrote', 'written',
    'sit', 'sits', 'sitting', 'sat',
    'stand', 'stands', 'standing', 'stood',
    'lose', 'loses', 'losing', 'lost',
    'pay', 'pays', 'paying', 'paid',
    'meet', 'meets', 'meeting', 'met',
    'include', 'includes', 'including', 'included',
    'continue', 'continues', 'continuing', 'continued',
    'set', 'sets', 'setting',
    'learn', 'learns', 'learning', 'learned', 'learnt',
    'change', 'changes', 'changing', 'changed',
    'lead', 'leads', 'leading', 'led',
    'understand', 'understands', 'understanding', 'understood',
    'watch', 'watches', 'watching', 'watched',
    'follow', 'follows', 'following', 'followed',
    'stop', 'stops', 'stopping', 'stopped',
    'create', 'creates', 'creating', 'created',
    'speak', 'speaks', 'speaking', 'spoke', 'spoken',
    'read', 'reads', 'reading',
    'spend', 'spends', 'spending', 'spent',
    'grow', 'grows', 'growing', 'grew', 'grown',
    'open', 'opens', 'opening', 'opened',
    'walk', 'walks', 'walking', 'walked',
    'win', 'wins', 'winning', 'won',
    'offer', 'offers', 'offering', 'offered',
    'remember', 'remembers', 'remembering', 'remembered',
    'love', 'loves', 'loving', 'loved',
    'consider', 'considers', 'considering', 'considered',
    'appear', 'appears', 'appearing', 'appeared',
    'buy', 'buys', 'buying', 'bought',
    'wait', 'waits', 'waiting', 'waited',
    'serve', 'serves', 'serving', 'served',
    'die', 'dies', 'dying', 'died',
    'send', 'sends', 'sending', 'sent',
    'expect', 'expects', 'expecting', 'expected',
    'build', 'builds', 'building', 'built',
    'stay', 'stays', 'staying', 'stayed',
    'fall', 'falls', 'falling', 'fell', 'fallen',
    'cut', 'cuts', 'cutting',
    'reach', 'reaches', 'reaching', 'reached',
    'kill', 'kills', 'killing', 'killed',
    'remain', 'remains', 'remaining', 'remained',
    'suggest', 'suggests', 'suggesting', 'suggested',
    'raise', 'raises', 'raising', 'raised',
    'pass', 'passes', 'passing', 'passed',
    'sell', 'sells', 'selling', 'sold',
    'require', 'requires', 'requiring', 'required',
    'report', 'reports', 'reporting', 'reported',
    'decide', 'decides', 'deciding', 'decided',
    'pull', 'pulls', 'pulling', 'pulled'
}

ENGLISH_COMMON_ADJECTIVES = {
    'good', 'better', 'best', 'bad', 'worse', 'worst',
    'new', 'old', 'young', 'great', 'big', 'small', 'large',
    'long', 'short', 'high', 'low', 'early', 'late',
    'right', 'wrong', 'true', 'false', 'real', 'different',
    'same', 'own', 'little', 'next', 'last', 'first',
    'second', 'third', 'similar', 'certain', 'clear',
    'sure', 'easy', 'hard', 'difficult', 'simple', 'possible',
    'impossible', 'able', 'unable', 'ready', 'available',
    'important', 'general', 'public', 'private', 'common',
    'particular', 'special', 'whole', 'full', 'free',
    'various', 'single', 'main', 'major', 'minor',
    'necessary', 'significant', 'essential', 'basic'
}

ENGLISH_COMMON_NOUNS = {
    'time', 'year', 'day', 'week', 'month', 'hour', 'minute', 'second',
    'way', 'thing', 'man', 'woman', 'person', 'people', 'child',
    'world', 'life', 'hand', 'part', 'place', 'case', 'fact',
    'group', 'problem', 'number', 'point', 'question', 'answer',
    'example', 'reason', 'idea', 'name', 'end', 'side', 'kind',
    'type', 'sort', 'form', 'word', 'line', 'area', 'page',
    'room', 'home', 'house', 'water', 'body', 'face', 'eye',
    'level', 'member', 'value', 'story', 'lot', 'result',
    'change', 'morning', 'night', 'evening', 'moment', 'air',
    'teacher', 'student', 'book', 'car', 'guy', 'lady',
    'mr', 'mrs', 'ms', 'dr', 'sir', 'madam'
}

ENGLISH_NUMBER_WORDS = {
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
    'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
    'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety',
    'hundred', 'thousand', 'million', 'billion', 'trillion',
    'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
    'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth',
    'dozen', 'couple', 'pair'
}

ENGLISH_OTHER_COMMON = {
    'etc', 'ie', 'eg', 'vs', 'aka', 'per', 'via',
    'thus', 'hence', 'therefore', 'however', 'moreover',
    'furthermore', 'nevertheless', 'nonetheless', 'besides',
    'meanwhile', 'otherwise', 'instead', 'anyway', 'anyhow',
    'indeed', 'actually', 'basically', 'generally', 'specifically',
    'particularly', 'especially', 'mainly', 'mostly', 'partly',
    'completely', 'totally', 'entirely', 'fully', 'exactly',
    'simply', 'merely', 'purely', 'solely', 'literally',
    'apparently', 'obviously', 'clearly', 'certainly',
    'definitely', 'probably', 'possibly', 'perhaps', 'maybe',
    'oh', 'ah', 'um', 'uh', 'hmm', 'yeah', 'yep', 'nope',
    'okay', 'ok', 'alright', 'please', 'thanks', 'sorry',
    'hello', 'hi', 'hey', 'bye', 'goodbye', 'yes', 'no'
}

# Combine all English stopwords / 
ENGLISH_STOPWORDS = (
    ENGLISH_ARTICLES |
    ENGLISH_PRONOUNS |
    ENGLISH_AUXILIARY_VERBS |
    ENGLISH_PREPOSITIONS |
    ENGLISH_CONJUNCTIONS |
    ENGLISH_DETERMINERS |
    ENGLISH_ADVERBS |
    ENGLISH_QUESTION_WORDS |
    ENGLISH_COMMON_VERBS |
    ENGLISH_COMMON_ADJECTIVES |
    ENGLISH_COMMON_NOUNS |
    ENGLISH_NUMBER_WORDS |
    ENGLISH_OTHER_COMMON
)


# ============================================================
# CHINESE STOPWORDS / 
# ============================================================

CHINESE_PRONOUNS = {
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', ''
}

CHINESE_AUXILIARY_WORDS = {
    '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', ''
}

CHINESE_PREPOSITIONS = {
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', ''
}

CHINESE_CONJUNCTIONS = {
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', ''
}

CHINESE_ADVERBS = {
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', ''
}

CHINESE_AUXILIARY_VERBS = {
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', ''
}

CHINESE_COMMON_VERBS = {
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', ''
}

CHINESE_COMMON_ADJECTIVES = {
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', ''
}

CHINESE_COMMON_NOUNS = {
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', ''
}

CHINESE_MEASURE_WORDS = {
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', ''
}

CHINESE_NUMBER_WORDS = {
    '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', ''
}

CHINESE_OTHER_COMMON = {
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
    '', '', '', '', ''
}

# Combine all Chinese stopwords / 
CHINESE_STOPWORDS = (
    CHINESE_PRONOUNS |
    CHINESE_AUXILIARY_WORDS |
    CHINESE_PREPOSITIONS |
    CHINESE_CONJUNCTIONS |
    CHINESE_ADVERBS |
    CHINESE_AUXILIARY_VERBS |
    CHINESE_COMMON_VERBS |
    CHINESE_COMMON_ADJECTIVES |
    CHINESE_COMMON_NOUNS |
    CHINESE_MEASURE_WORDS |
    CHINESE_NUMBER_WORDS |
    CHINESE_OTHER_COMMON
)


# ============================================================
# COMBINED STOPWORDS / 
# ============================================================

# All stopwords (English + Chinese) /  + 
ALL_STOPWORDS = ENGLISH_STOPWORDS | CHINESE_STOPWORDS


# ============================================================
# HELPER FUNCTIONS / 
# ============================================================

def get_english_stopwords() -> set:
    """
    Get all English stopwords.
    

    Returns:
        Set of English stopwords
        
    """
    return ENGLISH_STOPWORDS.copy()


def get_chinese_stopwords() -> set:
    """
    Get all Chinese stopwords.
    

    Returns:
        Set of Chinese stopwords
        
    """
    return CHINESE_STOPWORDS.copy()


def get_all_stopwords() -> set:
    """
    Get all stopwords (English + Chinese).
     + 

    Returns:
        Set of all stopwords
        
    """
    return ALL_STOPWORDS.copy()


def is_stopword(word: str, language: str = 'both') -> bool:
    """
    Check if a word is a stopword.
    

    Args:
        word: Word to check
              
        language: Language to check ('english', 'chinese', or 'both')
                  'english''chinese'  'both'

    Returns:
        True if the word is a stopword, False otherwise
         True False
    """
    word_lower = word.lower()

    if language == 'english':
        return word_lower in ENGLISH_STOPWORDS
    elif language == 'chinese':
        return word in CHINESE_STOPWORDS  # Chinese is case-sensitive
    else:  # both
        return word_lower in ENGLISH_STOPWORDS or word in CHINESE_STOPWORDS


def filter_stopwords(words: list, language: str = 'both') -> list:
    """
    Filter out stopwords from a list of words.
    

    Args:
        words: List of words to filter
               
        language: Language to filter ('english', 'chinese', or 'both')
                  'english''chinese'  'both'

    Returns:
        List of words with stopwords removed
        
    """
    return [word for word in words if not is_stopword(word, language)]


def get_stopword_stats() -> dict:
    """
    Get statistics about the stopwords database.
    

    Returns:
        Dictionary with stopword counts
        
    """
    return {
        'total_stopwords': len(ALL_STOPWORDS),
        'english_stopwords': len(ENGLISH_STOPWORDS),
        'chinese_stopwords': len(CHINESE_STOPWORDS),
        'english_categories': {
            'articles': len(ENGLISH_ARTICLES),
            'pronouns': len(ENGLISH_PRONOUNS),
            'auxiliary_verbs': len(ENGLISH_AUXILIARY_VERBS),
            'prepositions': len(ENGLISH_PREPOSITIONS),
            'conjunctions': len(ENGLISH_CONJUNCTIONS),
            'determiners': len(ENGLISH_DETERMINERS),
            'adverbs': len(ENGLISH_ADVERBS),
            'question_words': len(ENGLISH_QUESTION_WORDS),
            'common_verbs': len(ENGLISH_COMMON_VERBS),
            'common_adjectives': len(ENGLISH_COMMON_ADJECTIVES),
            'common_nouns': len(ENGLISH_COMMON_NOUNS),
            'number_words': len(ENGLISH_NUMBER_WORDS),
            'other': len(ENGLISH_OTHER_COMMON)
        },
        'chinese_categories': {
            'pronouns': len(CHINESE_PRONOUNS),
            'auxiliary_words': len(CHINESE_AUXILIARY_WORDS),
            'prepositions': len(CHINESE_PREPOSITIONS),
            'conjunctions': len(CHINESE_CONJUNCTIONS),
            'adverbs': len(CHINESE_ADVERBS),
            'auxiliary_verbs': len(CHINESE_AUXILIARY_VERBS),
            'common_verbs': len(CHINESE_COMMON_VERBS),
            'common_adjectives': len(CHINESE_COMMON_ADJECTIVES),
            'common_nouns': len(CHINESE_COMMON_NOUNS),
            'measure_words': len(CHINESE_MEASURE_WORDS),
            'number_words': len(CHINESE_NUMBER_WORDS),
            'other': len(CHINESE_OTHER_COMMON)
        }
    }


# Example usage / 
if __name__ == "__main__":
    print("="*70)
    print("Stopwords Database / ")
    print("="*70)

    stats = get_stopword_stats()
    print(f"\nTotal stopwords: {stats['total_stopwords']}")
    print(f": {stats['total_stopwords']}")

    print(f"\nEnglish stopwords: {stats['english_stopwords']}")
    print(f": {stats['english_stopwords']}")

    print(f"\nChinese stopwords: {stats['chinese_stopwords']}")
    print(f": {stats['chinese_stopwords']}")

    print("\n" + "-"*70)
    print("English Categories / :")
    for category, count in stats['english_categories'].items():
        print(f"  - {category}: {count}")

    print("\n" + "-"*70)
    print("Chinese Categories / :")
    for category, count in stats['chinese_categories'].items():
        print(f"  - {category}: {count}")

    # Test filtering / 
    print("\n" + "="*70)
    print("Test Stopword Filtering / ")
    print("="*70)

    test_sentences = [
        "An object with a mass of 10 kg is at rest",
        "Calculate the area of a circle with radius 5",
        "10"
    ]

    for sentence in test_sentences:
        print(f"\nOriginal: {sentence}")
        words = sentence.split()
        filtered = filter_stopwords(words)
        print(f"Filtered: {' '.join(filtered)}")
