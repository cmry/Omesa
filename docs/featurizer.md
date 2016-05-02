# Text feature extraction module


This module contains several helper classes for extracting textual features
used in Text Mining applications, partly based on instances parsed with parse.
It also includes a wrapper class to cleverly handle this within the Omesa
framework.



# Featurizer

``` python
 class Featurizer(features)
```

Wrapper for looping feature extractors in fit and transform operations.

Calls helper classes which extract different features from text data. Given
a list of initialized feature extractor classes, correctly streams or dumps
instances along these classes. Also provides an interface to fit and
transform methods.

| Parameters    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | features | list | List of initialized feature extractor classes. The classes can befound within this module. |


| Attributes    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | helper | list of classes |         Store for the provided features. |
        | Y | list of labels | Store for the provided features.Labels for X. |


-------

##Examples

Note: this is just for local use only.

During training with a full space and a generator:

``` python

>>> loader = reader.load  # assumes that this is a generator
>>> features = [Ngrams(level='char', n_list=[1,2])]
>>> ftr = _Featurizer(features)
>>> ftr.fit(loader())
>>> X, Y = ftr.transform(loader()), ftr.labels

```


During testing with only one instance:


``` python

>>> new_data = 'this is some string to test'
>>> tex, tey = ftr.transform(new_data), ftr.labels

```



---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | transform | Call all the helpers to extract features. |



### transform

``` python
    transform(stream)
```


Call all the helpers to extract features.

| Parameters    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | stream | generator |             Yields an instance with (label, raw, parse, meta). |


| Returns    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | X | numpy array of shape [n_samples, n_features] | Training data returns when applying the transform function. |



# Ngrams

``` python
 class Ngrams(object)
```

Calculate n-gram frequencies.

Can either be applied on token, POS or character level. The transform
method dumps a feature dictionary that can be used for feature hashing.

| Parameters    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | n_list | list of integers |         Amount of grams that have to be extracted, can be multiple. Say that        uni and bigrams have to be extracted, n_list has to be [1, 2]. |


-------

##Examples

Token-level uni and bigrams with a maximum of 2000 feats per n:


``` python

>>> ng = Ngrams(level='token', n_list=[1, 2], max_feats=2000)
>>> ng.transform('this is text')
... {'this': 1, 'is': 1, 'text': 1, 'this is': 1, 'is text': 1}

```



---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | __str__ | Report on feature settings. |
        | _find_ngrams | Magic n-gram function. |
        | transform | Given a document, return level-grams as Counter dict. |



### __str__

``` python
    __str__()
```


Report on feature settings.

### _find_ngrams

``` python
    _find_ngrams(input_list, n)
```


Magic n-gram function.

Calculate n-grams from a list of tokens/characters with added begin and
end items. Based on the implementation by Scott Triglia.

### transform

``` python
    transform(raw, parse=None)
```


Given a document, return level-grams as Counter dict.


# FuncWords

``` python
 class FuncWords(object)
```

Extract function word frequencies.

Computes relative frequencies of function words according to parse data,
and adds the respective frequencies as a feature.

---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | transform | Extract frequencies for fitted function word possibilites. |



### transform

``` python
    transform(_, parse)
```


Extract frequencies for fitted function word possibilites.


# SentimentFeatures

``` python
 class SentimentFeatures()
```

Lexicon based sentiment features.

Calculates four features related to sentiment: average polarity, number of
positive, negative and neutral words. Counts based on the Duoman and
Pattern sentiment lexicons.

---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | __str__ | Calculate four features for the input instance. |
        | transform | Get the sentiment belonging to the words in the parse string. |



### __str__

``` python
    __str__()
```


Calculate four features for the input instance.

Instance is a list of word-pos-lemma tuples that represent a token.

### transform

``` python
    transform(_, parse)
```


Get the sentiment belonging to the words in the parse string.


# SimpleStats

``` python
 class SimpleStats
```



| Parameters    | Type             | Doc             |
|:-------|:-----------------|:----------------|
        | text | boolean, optional, default True |  |
        | token | boolean, optional, default True |  |
        | sentence_lenth | boolean, optional, default True | Add the sentence length as a feature. |


-------

##Examples

All features:

``` python

>>> SimpleStats()

```


Only text features:


``` python

>>> SimpleStats(token=False, sentence_length=False)

```



---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | avg | Average length of iter. |
        | text_based_feats | Include features that are based on the raw text. |
        | token_based_feats | Include features that are based on certain tokens. |
        | avg_sent_length | Calculate average sentence length. |
        | transform | Transform given instance into simple text features. |



### avg

``` python
    avg(iterb)
```


Average length of iter.

### text_based_feats

``` python
    text_based_feats(raw)
```


Include features that are based on the raw text.

### token_based_feats

``` python
    token_based_feats(tokens)
```


Include features that are based on certain tokens.

### avg_sent_length

``` python
    avg_sent_length(sentence_indices)
```


Calculate average sentence length.

### transform

``` python
    transform(raw, parse)
```


Transform given instance into simple text features.


# Readability

``` python
 class Readability
```

Get readability-related features.

---------

## Methods



| Function    | Doc             |
|:-------|:----------------|
        | transform | Add each metric to the feature vector. |



### transform

``` python
    transform(raw, _)
```


Add each metric to the feature vector.