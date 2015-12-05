"""Text feature extraction module.

This module contains several helper classes for extracting textual features
used in Text Mining applications, partly based on instances parsed with parse.
It also includes a wrapper class to cleverly hanlde this within the shed
environment.

"""

import numpy as np
import operator
import re
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.preprocessing import LabelEncoder
from collections import OrderedDict, Counter, defaultdict
from time import sleep
import pickle

# Author:       Chris Emmery
# Contributors: Mike Kestemont, Ben Verhoeven, Janneke van de Loo
# License:      BSD 3-Clause
# pylint:       disable=E1103,W0512


class Featurizer(object):

    """
    Wrapper for looping feature extractors in fit and transform operations.

    Calls helper classes which extract different features from text data. Given
    a list of initialized feature extractor classes, correctly streams or dumps
    instances along these classes. Also provides an interface to fit and
    transform methods.

    Parameters
    ----------
    features : list
        List of initialized feature extractor classes. The classes can be
        found within this module.

    Attributes
    ----------
    helper : list of classes
        Store for the provided features.

    X : list of lists of shape [n_samples, n_words]
        All data instances used by space_based featurizer helpers.

    Y : list of labels
        Labels for X.

    Examples
    --------
    Note: this is just for local use only.

    During training with a full space and a generator:
    >>> loader = reader.load  # assumes that this is a generator
    >>> features = [Ngrams(level='char', n_list=[1,2])]
    >>> ftr = _Featurizer(features)
    >>> ftr.fit(loader())
    X, Y = ftr.transform(loader()), ftr.labels

    During testing with only one instance:
    >>> new_data = 'this is some string to test'
    >>> tex, tey = ftr.transform(new_data), ftr.labels

    Notes
    -----
    For an explanation regarding the parse features, please refer either to
    utils.parse.extract_tags or http://ilk.uvt.nl/parse/.
    """

    def __init__(self, features):
        """Initialize the wrapper and set the provided features to a var."""
        self.labels, self.labelc = {}, 0
        self.metaf, self.metafc = {}, 0
        self.helpers = features

    def call_helpers(self, stream, func):
        """Call all the helpers to extract features.

        Parameters
        ----------
        stream : generator
            Yields an instance with (label, raw, parse, meta).
        func : function
            Function object from etiher the fit or transform method.

        Returns
        -------
        X : numpy array of shape [n_samples, n_features]
            Training data returns when applying the transform function.
        """
        for label, raw, parse, meta in stream:
            v = {}
            if label not in self.labels:
                self.labels[label] = self.labelc
                self.labelc += 1
            for helper in self.helpers:
                helper.fit(raw, parse)
                if func == self.transform:
                    v.update(helper.transform(raw, parse))
            if func == self.transform:
                for meta_inst in meta:
                    if meta_inst not in self.metaf:
                        self.metaf[label] = self.metafc
                        self.metafc += 1
                        v.update({self.metaf[meta_inst]: 1})
            yield self.labels[label], v

    def fit(self, stream):
        """Fit the extractors according to their requirements."""
        return self.call_helpers(stream, self.fit)

    def transform(self, stream):
        """Transform an instance according to the fitted extractors."""
        return self.call_helpers(stream, self.transform)


class Ngrams(object):

    """
    Calculate n-gram frequencies.

    Can either be applied on token, POS or character level. The transform
    method dumps a feature dictionary that can be used for feature hashing.

    Parameters
    ----------
    n_list : list of integers
        Amount of grams that have to be extracted, can be multiple. Say that
        uni and bigrams have to be extracted, n_list has to be [1, 2].

    max_feats : integers
        Limits how many features will be generated.

    Examples
    --------
    Token-level uni and bigrams with a maximum of 2000 feats per n:

    In [1]: ng = Ngrams(level='token', n_list=[1, 2], max_feats=2000)

    In [2]: ng.transform('this is text')
    Out[2]: {'this': 1, 'is': 1, 'text': 1, 'this is': 1, 'is text': 1}

    Notes
    -----
    Implemented: Chris Emmery
    """

    def __init__(self, level='token', n_list=None):
        """Set parameters for N-gram extraction."""
        self.name = level+'_ngram'
        self.n_list = [2] if not n_list else n_list
        self.level = level
        self.row = 0 if level is 'token' else 2
        self.index, self.counter = 0, 0

    def __str__(self):
        """Report on feature settings."""
        return """
        feature:   {0}
        n_list:    1
        """.format(self.name, self.n_list)

    def _find_ngrams(self, input_list, n):
        """Magic n-gram function.

        Calculate n-grams from a list of tokens/characters with added begin and
        end items. Based on the implementation by Scott Triglia http://locally
        optimal.com/blog/2013/01/20/elegant-n-gram-generation-in-python/
        """
        inp = [''] * n + input_list + [''] * n
        return zip(*[inp[i:] for i in range(n)])

    def fit(self, raw, parse=None):
        """Placeholder fit."""
        return 'placeholder'

    def transform(self, raw, parse=None):
        """Given a document, return level-grams as Counter dict."""
        if self.level == 'char':
            needle = list(raw)
        elif self.level == 'token' or self.level == 'pos':
            needle = parse[self.row] if parse else raw.split()
            if self.level == 'pos' and not parse:
                raise EnvironmentError("There's no POS annotation.")

        c = Counter()
        for n in self.n_list:
            c += Counter([self.level+"-"+"_".join(item) for
                          item in self._find_ngrams(needle, n)])
        return c


class FuncWords:

    """
    Extract function word frequencies.

    Computes relative frequencies of function words according to parse data,
    and adds the respective frequencies as a feature.

    Notes
    -----
    Implemented by: Chris Emmery
    Dutch functors: Ben Verhoeven
    """

    def __init__(self, lang='en'):
        """Set parameters for function word extraction."""
        self.name = 'func_words'

        if lang == 'en':
            raise NotImplementedError
        elif lang == 'nl':
            self.functors = {
                'VNW': 'pronouns', 'LID': 'determiners','VZ': 'prepositions',
                'BW': 'adverbs', 'TW': 'quantifiers', 'VG': 'conjunction'}

    def fit(self, raw, parse):
        """Fit possible function words."""
        return "placeholder"

    def transform(self, _, parse):
        """Extract frequencies for fitted function word possibilites."""
        tokens = [item[0] for item in parse if item[2].split('(')[0]
                  in self.functors]
        return Counter()


class SentimentFeatures():

    """
    Lexicon based sentiment features.

    Calculates four features related to sentiment: average polarity, number of
    positive, negative and neutral words. Counts based on the Duoman and
    Pattern sentiment lexicons.

    Notes
    -----
    Implemented by: Chris Emmery

    Based on code by Cynthia Van Hee, Marjan Van de Kauter, Orphée De Clercq
    """

    def __init__(self):
        """Load the sentiment lexicon."""
        self.name = 'sentiment'
        self.lexiconDict = pickle.load(open('./shed/data/' +
                                            'sentilexicons.cpickle', 'rb'))

    def __str__(self):
        return """
        feature:   %s
        """ % (self.name)

    def fit(self, _, parse):
        """Placeholder for fit."""
        return 'placeholder'

    def calculate_sentiment(self, instance):
        """
        Calculate four features for the input instance.

        Instance is a list of word-pos-lemma tuples that represent a token.
        """
        polarity_score = 0.0
        token_dict = OrderedDict({
            r'SPEC\(vreemd\)': ('f', 'f'),
            r'BW\(\)': ('b', 'b'),
            r'N\(': ('n', 'n'),
            r'TWS\(\)': ('i', 'i'),
            r'ADJ\(': ('a', 'a'),
            r'WW\((od|vd).*(,prenom|,vrij)': ('a', 'v'),
            r'WW\((od|vd).*,nom': ('n', 'v'),
            r'WW\(inf,nom': ('n', 'v'),
            r'WW\(': ('v', 'v')
        })
        for token in instance:
            word, lemma, pos, _ = token
            for regx, param in token_dict.items():
                if re.search(regx, pos):
                    if (word, param[0]) in self.lexiconDict:
                        polarity_score += self.lexiconDict[(word, param[0])]
                    elif (lemma, param[1]) in self.lexiconDict:
                        polarity_score += self.lexiconDict[(lemma, param[1])]
                    break
                    # FIXME: reinclude the token numbers here
        return polarity_score

    def transform(self, _, parse):
        """Get the sentiment belonging to the words in the parse string."""
        return {self.name: self.calculate_sentiment(parse)}


class SimpleStats:

    r"""
    Word and token based features.

    By default, this class returns ALL features. To explicitly exclude these,
    use empty lists in the function.

    Parameters
    ----------
    text : list, ['all' (default), 'flood', 'char', 'emo']
        Text-based features to be extracted, can include:

        'flood':
            Includes flooding properties regarding total amount of flooding,
            and individually punctuation and alphanumeric stats.
        'char':
            Include frequency of punctuation and number sequences.
        'emo':
            Detect and include emoticon frequencies.
        'all':
            Every feature listed above.

    token : list, ['all' (default), 'wlen', 'capw', 'scapw', 'urls', 'photo', \
                   'vid']
        Token-based features to be extracted, can include:

        'wlen':
            Word lengths.
        'capw':
            Number of all CAPITAL words.
        'scapw':
            Number Of Start Capital Words.
        'urls':
            Occurence of URLs.
        'photo':
            Occurence of links to pictures.
        'vid':
            Occurence of links to videos.
        'all':
            Every feature listed above.

    sentence_lenth : integer, optional, default True
        Add the sentence length as a feature.

    regex_punc : pattern
        A pattern that captures all punctuation. Default is provided.

    regex_word : pattern
        A pattern that captures all alphanumerics. Default is provided.

    regex_punc : pattern
        A pattern that captures all capital sequences. Default is provided.

    Examples
    --------
    All features:
    >>> SimpleStats()

    Only sentence length:
    >>> SimpleStats(text=[], token=[])

    Only text features:
    >>> SimpleStats(text=['all'], token=[], sentence_length=False)

    Notes
    -----
    Code by: Janneke van de Loo
    Implemented by: Chris Emmery
    """

    def __init__(self, text=['all'], token=['all'], sentence_length=True,
                 regex_punc=None, regex_word=None, regex_caps=None):
        """Initialize all parameters to extract simple stats."""
        self.name = 'simple_stats'

        self.regex_punc = r'[\!\?\.\,\:\;\(\)\"\'\-]' if not \
                          regex_punc else regex_punc
        self.regex_word = r'^[a-zA-Z\-0-9]*[a-zA-Z][a-zA-Z\-0-9]*$' if not \
                          regex_word else regex_word
        self.regex_caps = r'^[A-Z\-0-9]*[A-Z][A-Z\-0-9]*$' if not \
                          regex_caps else regex_caps

        self.text = set(text)
        self.token = set(token)
        self.sentence_length = sentence_length

    def fit(self, _, parse):
        """Placeholder for fit."""
        return 'placeholder'

    def floodings(text):
        '''
        Returns a list of tuples (complete_flooding, flooded_item),
        e.g.('iii', 'i')
        '''
        floodings = re.findall(r"((.)\2{2,})", text)
        floodings = [tup for tup in floodings if tup[0] != '...']
        return floodings

    def only_alph(self, floodings):
        """Include only alphanumeric flooding stats."""
        return [fl for fl in floodings if re.search(r'^[a-zA-Z]+$', fl[1])]

    def only_punc(self, floodings):
        """Include only punctuation related floodings."""
        return [fl for fl in floodings if re.search(self.regex_punc, fl[1])]

    def avg_fl_len(self, floodings):
        """Average length of flooding."""
        if floodings:
            avg_len = np.mean([len(fl) for fl, _ in floodings])
        else:
            avg_len = 0
        return avg_len

    def flooding_stats(self, text):
        """Some stats related to arbitrary repetion of keystrokes."""
        vector = []
        fl = pnet.floodings(text)
        fl_alph = self.only_alph(fl)
        fl_punc = self.only_punc(fl)
        vector.append(len(fl))
        vector.append(len(fl_alph))
        vector.append(len(fl_punc))
        vector.append(self.avg_fl_len(fl))
        vector.append(self.avg_fl_len(fl_alph))
        vector.append(self.avg_fl_len(fl_punc))
        return vector

    def num_punc_seqs(self, text):
        """Punctuation sequences such as ..,,,!!!."""
        regex_punc_seq = self.regex_punc+'+'
        return len(re.findall(regex_punc_seq, text))

    def num_num_seqs(self, text):
        """Number sequences such as 9782189421."""
        regex_num_seq = r'[0-9]+'
        return len(re.findall(regex_num_seq, text))

    def char_type_stats(self, text):
        """Number of punctuation and number sequences."""
        vector = []
        vector.append(self.num_punc_seqs(text))
        vector.append(self.num_num_seqs(text))
        return vector

    def num_emoticons(self, text):
        """Number of _EMOTICON_ tags found."""
        return len(re.findall(r'_EMOTICON_', text))

    def get_words(self, tokens):
        """Retrieve what is declared to be a word."""
        return [tok for tok in tokens if re.search(self.regex_word, tok)]

    def avg_word_len(self, words):
        """Average word length of input string."""
        avg = np.mean([len(w) for w in words])
        return avg if str(avg) != 'nan' else 0.0

    def num_allcaps_words(self, words):
        """Number of words that are all CAPITALIZED."""
        return sum([1 for w in words if re.search(self.regex_caps, w)])

    def num_startcap_words(self, words):
        """Number Of Words That Start With A Capital."""
        return sum([1 for w in words if re.search(r'^[A-Z]', w)])

    def num_urls(self, tokens):
        """Number of URLs in given string."""
        return sum([1 for tok in tokens if tok == '_URL_'])

    def num_photos(self, tokens):
        """Number of photos in given string."""
        return sum([1 for tok in tokens if tok == '_PHOTO_'])

    def num_videos(self, tokens):
        """Number of videos in given string."""
        return sum([1 for tok in tokens if tok == '_VIDEO_'])

    def text_based_feats(self, text):
        """Include features that are based on the raw text."""
        vector = []
        if self.text.intersection(set(['flood', 'all'])):
            vector.extend(self.flooding_stats(text))
        if self.text.intersection(set(['char', 'all'])):
            vector.extend(self.char_type_stats(text))
        if self.text.intersection(set(['emo', 'all'])):
            vector.append(self.num_emoticons(text))
        return vector

    def token_based_feats(self, tokens):
        """Include features that are based on certain tokens."""
        vector = []
        words = self.get_words(tokens)
        if self.token.intersection(set(['wlen', 'all'])):
            vector.append(self.avg_word_len(words))
        if self.token.intersection(set(['capw', 'all'])):
            vector.append(self.num_allcaps_words(words))
        if self.token.intersection(set(['scapw', 'all'])):
            vector.append(self.num_startcap_words(words))
        if self.token.intersection(set(['urls', 'all'])):
            vector.append(self.num_urls(tokens))
        if self.token.intersection(set(['photo', 'all'])):
            vector.append(self.num_photos(tokens))
        if self.token.intersection(set(['vid', 'all'])):
            vector.append(self.num_videos(tokens))
        return vector

    def avg_sent_length(self, sent_nums):
        """Calculate average sentence length."""
        sent_len_dict = Counter(sent_nums)
        sent_lengths = [val for _, val in sent_len_dict.items()]
        avg_len = np.mean(sent_lengths)
        return avg_len

    def transform(self, raw, parse):
        """Transform given instance into simple text features."""
        fts = self.text_based_feats(raw) + \
            self.token_based_feats([f[0] for f in parse])
        if self.sentence_length:
            fts += [self.avg_sent_length(
                [f[3] for f in parse if len(parse) > 3])]
        self.instances.append(fts)


class Readability:

    """
    Get readability-related features.

    Notes
    -----
    Implemented by: Chris Emmery
    Attributes by: Tom De Smedt
    """

    def __init__(self):
        """Initialize empty class variables."""
        self.name = 'readability'
        self.diacritics = \
            u"àáâãäåąāæçćčςďèéêëēěęģìíîïīłįķļľņñňńйðòóôõöøþřšťùúûüůųýÿўžż"
        self.punctuation = ".,;:!?()[]{}`''\"@#$^&*+-|=~_"
        self.flooding = re.compile(r"((.)\2{2,})", re.I) # ooo, xxx, !!!, ...
        self.emoticons = set((
            '*)', '*-)', '8)', '8-)', '8-D', ":'''(", ":'(", ':(', ':)',
            ':-(', ':-)', ':-.', ':-/', ':-<', ':-D', ':-O', ':-P', ':-S',
            ':-[', ':-b', ':-c', ':-o', ':-p', ':-s', ':-|', ':/', ':3', ':>',
            ':D', ':O', ':P', ':S', ':[', ':\\', ':]', ':^)', ':b', ':c',
            ':c)', ':o', ':o)', ':p', ':s', ':{', ':|', ':}', ";'(", ';)',
            ';-)', ';-]', ';D', ';]', ';^)', '<3', '=(', '=)', '=-D', '=/',
            '=D', '=]', '>.>', '>:)', '>:/', '>:D', '>:P', '>:[', '>:\\',
            '>:o', '>;]', 'X-D', 'XD', 'o.O', 'o_O', 'x-D', 'xD', u'\xb0O\xb0',
            u'\xb0o\xb0', u'\u2665', u'\u2764', '^_^', '-_-'
        ))
        self.emoji = set((
            u'\U0001f44c', u'\U0001f44d', u'\U0001f47f', u'\U0001f495',
            u'\U0001f499', u'\U0001f49a', u'\U0001f49b', u'\U0001f49c',
            u'\U0001f600', u'\U0001f601', u'\U0001f602', u'\U0001f603',
            u'\U0001f604', u'\U0001f605', u'\U0001f606', u'\U0001f607',
            u'\U0001f608', u'\U0001f60a', u'\U0001f60b', u'\U0001f60c',
            u'\U0001f60d', u'\U0001f60e', u'\U0001f60f', u'\U0001f610',
            u'\U0001f612', u'\U0001f613', u'\U0001f614', u'\U0001f615',
            u'\U0001f61b', u'\U0001f61c', u'\U0001f61d', u'\U0001f61e',
            u'\U0001f61f', u'\U0001f620', u'\U0001f621', u'\U0001f622',
            u'\U0001f625', u'\U0001f626', u'\U0001f627', u'\U0001f629',
            u'\U0001f62a', u'\U0001f62b', u'\U0001f62c', u'\U0001f62d',
            u'\U0001f62e', u'\U0001f62f', u'\U0001f633', u'\U0001f636',
            u'\U0001f63b', u'\U0001f63f', u'\U0001f640', u'\u2764\ufe0f',
            u'\u263a', u'\ud83d', u'\ude09'
        ))
        self.url = re.compile(r"https?://[^\s]+")           # http://www.textgain.com
        self.ref = re.compile(r"@[a-z0-9_./]+", flags=re.I) # @tom_de_smedt

    def fit(self, raw, _):
        return 'placeholder'

    def transform(self, raw, _):
        """Add each metric to the feature vector."""
        # TODO: add stuff here
        pass
