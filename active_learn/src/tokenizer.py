#!/usr/bin/env python
import copy
import glob
import json
import os
import string
from string import punctuation

import numpy
import regex as re
import requests


class NewLineSegmenter(object):
    """
        split sentence by return line
    """

    def __init__(self):
        pass

    def is_nl_token(self, t):

        # if a token consists of all space, and has at least one newline char, we segment as a sentence.
        if t.is_space and '\n' in t.text:
            return True
        else:
            return False

    def set_sent_starts(self, doc):
        if self.is_nl_token(doc[0]):
            doc[0].is_sent_start = True
        else:
            doc[0].is_sent_start = False
        if len(doc) == 1:
            return doc

        for t in doc[1:]:
            if self.is_nl_token(doc[t.i - 1]) and not self.is_nl_token(t):
                t.is_sent_start = True
            else:
                t.is_sent_start = False

        return doc


spec_char_pattern = re.compile(r'[\u2460-\u24FF\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u3000-\u303f\u3300-\u33FF~]+')
# lookup around zh char after english
comb_numen_zh_pattern = re.compile(
    r'(?<en>[\u0021-\u0079]+)(?=[\u4e00-\u9fa5])|[\u4e00-\u9fa5]+(?<en>=[\u0021-\u0079]+)')


def retokenize(doc):
    def is_eng(text):
        return all([ord(c) >= 65 and ord(c) <= 90 for c in text.upper()])
    with doc.retokenize() as retokenizer:
        i = 0
        while i < len(doc)-1:
            token = doc[i]
            # split by special unicode char
            if len(token.text) > 1:
                m = list(spec_char_pattern.finditer(token.text))
                default_dep = 'punct'
                default_pos = 'PUNCT'
                if not m:
                    m = list(comb_numen_zh_pattern.finditer(token.text))
                    default_dep = 'compound:nn'
                    default_pos = 'PROPN'
                if m:
                    m = m[0]
                    span = m.span()
                    if span[0] == 0:
                        heads = [token.head, token.head]
                        attrs = {"POS": [default_pos, token.pos_], "DEP": [default_dep, token.dep_]}
                        retokenizer.split(token, [m.group(), token.text[span[1]:]], heads=heads, attrs=attrs)
                    elif span[1] == len(token.text):

                        heads = [token.head, token.head]
                        attrs = {"POS": [token.pos_, default_pos], "DEP": [token.dep_, default_dep]}
                        retokenizer.split(token, [token.text[:span[0]], m.group()], heads=heads, attrs=attrs)
                    else:
                        # Attach this token to the second subtoken (index 1) that token will be split into
                        heads = [token.head, (token, 2), (token, 3)]
                        attrs = {"POS": ['NOUN', "PUNCT", 'NOUN'], "DEP": ['compound:nn', default_dep, 'compound:nn']}
                        retokenizer.split(token, [token.text[:span[0]], m.group(),
                                                  token.text[span[1]:]], heads=heads, attrs=attrs)
            i += 1

    i = 0
    while i < len(doc)-1:
        token = doc[i]
        # merge english if have multiple closed token in a sentence
        if token.sent.start == doc[i+1].sent.start and token.whitespace_ == '' \
            and is_eng(token.text) and is_eng(doc[i+1].text) \
                and (doc[i].dep_ not in ('ROOT', 'dep') and doc[i + 1].dep_ not in ('ROOT', 'dep')):
            with doc.retokenize() as retokenizer:
                retokenizer.merge(doc[i:i + 2], attrs={"LEMMA": token.text + doc[i + 1].text, 'POS': 'NOUN'})
        else:
            i += 1
    return doc


def format_sentence(sentence, vocab, tokenizer=None, max_seq_len=50):
    """
        Format token ids to sentence and masks
        Input:
            - sentence: string or list of tokens/token ids,
            - vocab:  instance of nlptools.text.vocab
            - tokenizer:  instance of nlptools.text.tokenizer, default is None
            - max_seq_len: int, default is 50
    """
    import torch
    if tokenizer is None:
        token_ids = sentence
    else:
        if isinstance(sentence, str):
            tokens = tokenizer(sentence)
            if len(tokens) < 1:
                return None
        else:
            tokens = sentence
        if not isinstance(sentence[0], int):
            if len(tokens) > max_seq_len - 2:
                tokens_bak = copy.deepcopy(tokens)
                tokens = list(tokens)
                while len(tokens) > 0 and tokens[-1][-1] in punctuation:
                    tokens.pop()
                if len(tokens) < 1:
                    tokens = tokens_bak
            token_ids = vocab.words2id(tokens)
        token_ids = token_ids[:max_seq_len - 2]
    if isinstance(token_ids, torch.Tensor):
        token_ids = token_ids.cpu().detach().numpy()
        token_ids = token_ids[:max_seq_len - 2]
    seq_len = len(token_ids) + 2
    sentence = numpy.zeros(max_seq_len, 'int')
    sentence_mask = numpy.zeros(max_seq_len, 'int')
    sentence[0] = vocab.BOS_ID
    sentence[1:seq_len - 1] = token_ids
    sentence[seq_len - 1] = vocab.EOS_ID
    sentence_mask[:seq_len] = 1
    return sentence, sentence_mask


class Tokenizer_Base(object):
    '''
        Parent class for other tokenizer classes, please don't use this class directly
        Input:
            - stopwords_path: the path of stopwords, default is None
            - ner_name_replace: dictionary, replace the entity name to the mapped name. Default is None
    '''

    def __init__(self, stopwords_path=None, ner_name_replace=None):
        self.stopwords = {}
        self.ner_name_replace = {} if ner_name_replace is None else ner_name_replace
        self.__loadStopwords(stopwords_path)
        self.config = {"stopwords_path": stopwords_path,
                       "ner_name_replace": ner_name_replace}

    def __loadStopwords(self, stopwords_path):
        if stopwords_path is not None and os.path.exists(stopwords_path):
            with open(stopwords_path, encoding='utf-8') as f:
                for i in f.readlines():
                    self.stopwords[i.strip()] = ''

    def __call__(self, sentence, batch=False):
        if batch:
            return numpy.asarray([self.seg(s)['tokens'] for s in sentence], dtype=numpy.object)
        return self.seg(sentence)['tokens']

    def tokens2sentence(self, tokens):
        return " ".join(tokens)


class Tokenizer_CoreNLP(Tokenizer_Base):
    '''
        Stanford CoreNLP wrapper, Please check `stanford CoreNLP <https://stanfordnlp.github.io/CoreNLP/>`_ for more details
        Input:
            - corenlp_url: corenlp api url
            - stopwords_path: the path of stopwords, default is None
            - ner_name_replace: dictionary, replace the entity name to the mapped name. Default is None
    '''

    def __init__(self, corenlp_url, **args):
        Tokenizer_Base.__init__(self, **args)
        self.server_url = corenlp_url

    def _annotate(self, text, properties=None):
        assert isinstance(text, str)
        if properties is None:
            properties = {}
        else:
            assert isinstance(properties, dict)

        r = requests.post(self.server_url, params={'properties': str(properties)}, data=text.encode('utf-8'),
                          headers={'Connection': 'close'})
        output = r.text
        if ('outputFormat' in properties
                and properties['outputFormat'] == 'json'):
            try:
                output = json.loads(output, encoding='utf-8', strict=True)
            except:
                pass
        return output

    def tokensregex(self, text, pattern, filter):
        return self.regex('/tokensregex', text, pattern, filter)

    def semgrex(self, text, pattern, filter):
        return self.regex('/semgrex', text, pattern, filter)

    def regex(self, endpoint, text, pattern, filter):
        r = requests.get(
            self.server_url + endpoint, params={
                'pattern': pattern,
                'filter': filter
            }, data=text)
        output = r.text
        try:
            output = json.loads(r.text)
        except:
            pass
        return output

    def seg(self, sentence, remove_stopwords=True, entities_filter=None, pos_filter=None):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
                - entities_filter: string list, will only remain the entity tokens, default is None
                - pos_filter: string list, will only remain special pos tokens, default is None
            Output: dictionary with keys:
                - tokens: list of tokens
                - texts: list of raw texts
                - entities: list of entities from NER
                - pos: list of pos tags
        '''
        txts, tokens, entities, pos = [], [], [], []
        for idx, sentence in enumerate(self._annotate(sentence, properties={'annotators': 'tokenize, pos, lemma, ner',
                                                                            'outputFormat': 'json'})['sentences']):
            for token in sentence['tokens']:
                if remove_stopwords and token['word'] in self.stopwords:
                    continue
                if pos_filter is not None and token['pos'] not in pos_filter:
                    continue
                if token['ner'] in self.ner_name_replace:
                    token['ner'] = self.ner_name_replace[token['ner']]
                if entities_filter is not None and token['ner'] not in entities_filter:
                    continue
                if len(token['lemma']) < 1:
                    continue
                txts.append(token['word'])
                tokens.append(token['lemma'])
                pos.append(token['pos'])
                entities.append(token['ner'])

        return {"tokens": tokens, "texts": txts, "entities": entities, 'pos': pos}


class Tokenizer_Spacy(Tokenizer_Base):
    '''
        Spacy wrapper, Please check `Spacy <https://spacy.io/>`_ for more details
        Input:
            - spacy_model: model name, default is "en"
            - spacy_pipes: list like ["tagger", "parser", "ner"], default is None
            - model_path: string, path of spacy model, default is None
            - custom_pips: list of custom pipline functions, default is None
            - stopwords_path: the path of stopwords, default is None
            - ner_name_replace: dictionary, replace the entity name to the mapped name. Default is None
    '''

    def __init__(self, spacy_model='en', spacy_pipes=None, model_path=None, **args):
        import spacy
        super().__init__(**args)
        disabled_pipelines = ['tagger', 'parser', 'ner', 'textcat', 'entity_ruler', 'sentencizer']
        if spacy_pipes is not None:
            disabled_pipelines = list(set(disabled_pipelines) - set(spacy_pipes))
        self.nlp = spacy.load(spacy_model, disable=disabled_pipelines)

    def add_pipe(self, custom_pipe, **args):
        '''
            add custom pipe
            Input:
                - custom_pipe: pip function
                - **args: any argumets for spacy add_pipe
        '''
        self.nlp.add_pipe(custom_pipe, **args)

    def entities(self, sentence):
        entities = []
        for ent in self.nlp(sentence).ents:
            label = ent.label_
            if label in self.ner_name_replace:
                label = self.ner_name_replace[label]
            entities.append((label, ent.text))
        return entities

    def seg(self, sentence, remove_stopwords=True, tags_filter=None, entities_filter=None, pos_filter=None,
            dep_filter=None):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
                - tags_filter: string list, will only main special tag tokens, default is None
                - entities_filter: string list, will only remain the entity tokens, default is None
                - pos_filter: string list, will only remain special pos tokens, default is None
                - dep_filter: string list, will only remain special dep tokens, default is None
            Output: dictionary with keys:
                - tokens: list of tokens
                - tags: list of detailed part-of-speech tags
                - texts: list of raw texts
                - entities: list of entities from NER
                - pos: list of simple part-of-speech tags
                - dep: list of syntactic dependency
        '''
        infos = {"tokens": [], "tags": [], "offsets": [], "lemma": [], "entities": [], "pos": [], "dep": []}

        for token in self.nlp(sentence):
            if remove_stopwords and token.text in self.stopwords:
                continue
            if tags_filter is not None and token.tag_ not in tags_filter:
                continue
            if pos_filter is not None and token.pos_ not in pos_filter:
                continue
            if dep_filter is not None and token.dep_ not in dep_filter:
                continue
            entity = token.ent_type_
            if entity in self.ner_name_replace:
                entity = self.ner_name_replace[entity]
            if entities_filter is not None and entity not in entities_filter:
                continue
            if len(token.lemma_) < 1:
                continue
            infos["lemma"].append(token.lemma_)
            infos["tokens"].append(txt)
            infos["offsets"].append((token.idx, token.idx + len(txt)))
            infos["tags"].append(token.tag_)
            infos["entities"].append(entity)
            infos["pos"].append(token.pos_)
            infos["dep"].append(token.dep_)
            infos["is_sent_end"].append(token.is_sent_end)
            offset += len(txt)
        return infos


class Tokenizer_Jieba(Tokenizer_Base):
    '''
        Jieba wrapper, Please check `Jieba <https://github.com/fxsjy/jieba>`_ for more details
        Input:
            - seg_dict_path: if the key existed, will load the user definded dict. Default is None
            - stopwords_path: the path of stopwords, default is None
    '''

    def __init__(self, seg_dict_path=None, **args):
        from jieba import posseg
        Tokenizer_Base.__init__(self, **args)
        if seg_dict_path is not None:
            jieba.load_userdict(seg_dict_path)
        self.nlp = posseg

    def seg(self, sentence, remove_stopwords=True):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
            Output: dictionary with keys:
                - tokens: list of tokens
        '''
        infos = {"tokens": [], "tags": [], "offsets": []}
        offset = 0
        for token in self.nlp.cut(sentence):
            x = token.word.strip()
            if remove_stopwords and x in self.stopwords:
                continue
            if len(x) < 1:
                offset += len(token.word)
                continue
            infos["tokens"].append(x)
            infos["tags"].append(token.flag)
            infos["offsets"].append((offset, offset+len(x)))
            offset += len(x)
        return infos


class Tokenizer_LTP(Tokenizer_Base):
    '''
        HIT-SCIR pyltp wrapper, Please check `pyltp <https://github.com/HIT-SCIR/pyltp>`_ for more details
        Input:
            - cws_model_path: path of cws model
            - pos_model_path: path of pos model
            - ner_model_path: path of ner model
            - parser_model_path: path of parser model, default is None
            - stopwords_path: the path of stopwords, default is None
            - ner_name_replace: dictionary, replace the entity name to the mapped name. Default is None
    '''

    def __init__(self, cws_model_path, pos_model_path, ner_model_path, parser_model_path, **args):
        Tokenizer_Base.__init__(self, **args)
        from pyltp import NamedEntityRecognizer, Parser, Postagger, Segmentor
        self.seg_ins = Segmentor()
        self.seg_ins.load(cws_model_path)
        self.pos_ins = Postagger()
        self.pos_ins.load(pos_model_path)
        if parser_model_path is not None and os.path.exists(parser_model_path):
            self.parser_ins = Parser()
            self.parser_ins.load(parser_model_path)
        else:
            self.parser_ins = None
        self.ner_ins = []

        for path in sorted(glob.glob(ner_model_path)):
            try:
                if os.path.getsize(path) > 1024:
                    self.ner_ins.append(NamedEntityRecognizer())
                    self.ner_ins[-1].load(path)
            except Exception as err:
                print(err)

    def __del__(self):
        self.seg_ins.release()
        self.pos_ins.release()
        for n in self.ner_ins:
            n.release()

    def seg(self, sentence, remove_stopwords=True, tags_filter=None, entities_filter=None):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
                - tags_filter: string list, will only main special tag tokens, default is None
                - entities_filter: string list, will only remain the entity tokens, default is None
            Output: dictionary with keys:
                - tokens: list of tokens
                - tags: list of detailed part-of-speech tags
                - entities: list of entities from NER
        '''
        words_ = self.seg_ins.segment(sentence)
        postags_ = self.pos_ins.postag(words_)
        if self.parser_ins is not None:
            arcs_ = self.parser_ins.parse(words_, postags_)
        entities__ = []

        for n in self.ner_ins:
            entities__.append(list(n.recognize(words_, postags_)))
        # mix entities
        entities_ = entities__[0]
        for ee in entities__:
            for i, e in enumerate(ee):
                if e != 'O':
                    entities_[i] = e

        words_, postags_ = list(words_), list(postags_)
        words, postags, entities, offsets = [], [], [], []
        offset = 0
        word_tmp, postag_tmp, entity_tmp = '', [], []
        for i, w in enumerate(words_):
            if remove_stopwords and w in self.stopwords:
                continue
            entity = re.split('-', entities_[i])
            if len(entity) > 1:
                entity_loc, entity = entity[0], entity[1]
            else:
                entity_loc, entity = 'O', 'O'
            if entity in self.ner_name_replace:
                entity = self.ner_name_replace[entity]
            if tags_filter is not None and postags_[i] not in tags_filter:
                continue
            if entities_filter is not None and entity not in entities_filter:
                continue

            words.append(w)
            postags.append(postags_[i])
            offsets.append((offset, len(w)))
            if entity_loc == 'O':
                entities.append('O')
            else:
                entities.append(entity_loc + '-' + entity)
            offset += len(w)
        return {'tokens': words, 'tags': postags, 'entities': entities}


class Tokenizer_Mecab(Tokenizer_Base):
    '''
        Mecab wrapper, Please check `Mecab <https://taku910.github.io/mecab/>`_ for more details
        Input:
            - seg_dict_path: mecab model path
            - stopwords_path: the path of stopwords, default is None
    '''

    def __init__(self, seg_dict_path, **args):
        import MeCab
        self.mecab_ins = MeCab.Tagger('-d %s ' % seg_dict_path)
        Tokenizer_Base.__init__(self, **args)

    def seg(self, sentence, remove_stopwords=True, tags_filter=None):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
                - tags_filter: string list, will only main special tag tokens, default is None. Some available tags are "名詞", "動詞", "助動詞", "形容詞", "助詞", "係助詞"...
            Output: dictionary with keys:
                - tokens: list of tokens
                - tags: list of detailed part-of-speech tags
        '''
        sentence = re.sub(r"[^\w\d]+", " ", sentence)
        tokens, tags, offsets = [], [], []
        offset = 0
        m = self.mecab_ins.parseToNode(sentence)
        while m:
            word_type = m.feature.split(',')[0]
            try:
                m.surface
            except:
                m = m.next
                continue
            if len(m.surface) < 1:
                m = m.next
                continue
            if remove_stopwords and m.surface in self.stopwords:
                m = m.next
                continue
            if tags_filter is not None and word_type not in tags_filter:
                m = m.next
                continue
            tokens.append(m.surface)
            tags.append(word_type)
            offsets.append((offset, len(m.surface)))
            offset += len(m.surface)
            m = m.next
        return {"tokens": tokens, "tags": tags}


# natural segment
class Tokenizer_Simple(Tokenizer_Base):
    '''
        Tokenizer use regex
        Input:
            - tokenizer_regex: regex string, default is [\s\.\:\;\&\'\"\/\\\(\)\[\]\{\}\%\$\#\!\?\^\&\+\`\~（）《》【】「」；：‘“’”？／。、，]
            - stopwords_path: the path of stopwords, default is None
            - ner_name_replace: dictionary, replace the entity name to the mapped name. Default is None
    '''

    def __init__(self, tokenizer_regex=None, **args):
        Tokenizer_Base.__init__(self, **args)
        if tokenizer_regex is None:
            tokenizer_regex = '''[\s\.\:\;\&\'\"\/\\\(\)\[\]\{\}\%\$\#\!\?\^\&\+\`\~（）《》【】「」；：‘“’”？／。、，]'''
        self.re_punc = re.compile(tokenizer_regex)

    def seg(self, sentence, remove_stopwords=True):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
            Output: dictionary with keys:
                - tokens: list of tokens
        '''
        tokens__ = [s.lower() for s in self.re_punc.split(sentence) if len(s) > 0]
        tokens, offsets = [], []
        offset = 0
        if remove_stopwords:
            for s in tokens__:
                if s not in self.stopwords:
                    tokens.append(s)
                    offsets.append((offset, len(s)))
                    offset += len(s)
        return {'tokens': tokens, 'offsets': offsets}


class Tokenizer_BERT(Tokenizer_Base):
    '''
        use BERT tokenizer, with wordpiece
        Input:
            - bert_model_name: vocab file location or one of the supported model name:
                - bert-base-uncased
                - bert-large-uncased
                - bert-base-cased
                - bert-base-multilingual
                - bert-base-chinese
            - do_lower_case: default True
    '''

    def __init__(self, bert_model_name, do_lower_case=True, **args):
        from transformers import BertTokenizer
        Tokenizer_Base.__init__(self, **args)
        config = {"bert_model_name": bert_model_name, "do_lower_case": do_lower_case}
        self.config = {**config, **self.config}
        self.tokenizer = BertTokenizer.from_pretrained(bert_model_name, do_lower_case=do_lower_case)

    def seg(self, sentence, remove_stopwords=True):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
            Output: dictionary with keys:
                - tokens: list of tokens
        '''
        tokens = self.tokenizer.tokenize(sentence)
        if remove_stopwords:
            tokens = [t for t in tokens if not t in self.stopwords]
        return {'tokens': tokens}

    @property
    def vocab(self):
        '''
            return a nlptools.text.vocab instance, converted from BERT pretrained model
        '''
        from .vocab import Vocab
        vocab = Vocab.load_from_dict(self.tokenizer.vocab)
        vocab.UNK, vocab.BOS, vocab.EOS, vocab.PAD = '[UNK]', '[CLS]', '[SEP]', '[MASK]'
        vocab.UNK_ID, vocab.BOS_ID, vocab.EOS_ID, vocab.PAD_ID = 100, 101, 102, 103
        vocab.addBE()
        return vocab

    def tokens2sentence(self, tokens):
        '''
            Join token list to sentence
        '''
        new_tokens = []
        for i, t in enumerate(tokens):
            if i > 0 and t[:2] == "##":
                new_tokens[-1] += t[2:]
            else:
                new_tokens.append(t)
        return " ".join(new_tokens)


class Tokenizer_GPT2(Tokenizer_Base):
    '''
        use GPT2 tokenizer, with byte-level BPE
        Input:
            - model_name: vocab file location or one of the supported model name:
    '''

    def __init__(self, model_name, **args):
        from transformers import GPT2LMHeadModel, GPT2Tokenizer
        Tokenizer_Base.__init__(self, **args)
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)

    def seg(self, sentence, remove_stopwords=True):
        ''' segment sentence to words

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
            Output: dictionary with keys:
                - tokens: list of tokens
        '''
        tokens = self.tokenizer.encode(sentence)
        if remove_stopwords:
            tokens = [t for t in tokens if not t in self.stopwords]
        return {'tokens': tokens, 'entities': []}

    @property
    def vocab(self):
        '''
            return a nlptools.text.vocab instance, converted from BERT pretrained model
        '''
        from .vocab import Vocab
        vocab = Vocab.load_from_dict(self.tokenizer.encoder)
        return vocab


# character level segment
class Tokenizer_Char(Tokenizer_Base):
    '''
        Split sentence to character list
        Input:
            - stopwords_path: the path of stopwords, default is None
    '''

    def __init__(self, **args):
        Tokenizer_Base.__init__(self, **args)

    def seg(self, sentence, remove_stopwords=True):
        ''' segment sentence to characters

            Input:
                - sentence: string
                - remove_stopwords: bool, default is True
            Output: dictionary with keys:
                - tokens: list of characters
        '''
        tokens, offsets = [], []
        for offset, s in enumerate(sentence):
            s = s.strip()
            if remove_stopwords and s in self.stopwords:
                continue
            tokens.append(s)
            offsets.append((offset, offset+1))
        return {'tokens': tokens, 'offsets': offsets}


class Tokenizer(object):
    '''
        Tokenizer tool, integrate with several tools 
        Input:
            - tokenizer: string, choose for tokenizer tool:
                1. *corenlp*: stanford CoreNLP
                2. *spacy*: spacy
                3. *jieba*: jieba
                4. *ltp*: HIT-SCIR pyltp
                5. *mecab*: mecab
                6. *simple*: regex
                7. *char*: will split to char level
                8. *http://**: will use restapi
    '''

    def __new__(cls, tokenizer='simple', **args):
        tokenizers = {'corenlp': Tokenizer_CoreNLP,
                      'spacy': Tokenizer_Spacy,
                      'jieba': Tokenizer_Jieba,
                      'ltp': Tokenizer_LTP,
                      'mecab': Tokenizer_Mecab,
                      'simple': Tokenizer_Simple,
                      'bert': Tokenizer_BERT,
                      'gpt2': Tokenizer_GPT2,
                      'char': Tokenizer_Char}
        if tokenizer in tokenizers:
            return tokenizers[tokenizer](**args)
        elif 'http' in tokenizer:
            return Tokenizer_Rest(**args)
        return Tokenizer_Simple(**args)
