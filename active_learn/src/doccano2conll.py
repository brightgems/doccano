# -*- coding: utf-8 -*-
from tokenizer import Tokenizer
import re
from consts import NEW_LINE_CHAR
import shutil
import codecs
import glob
import json
import os
from typing import List, Tuple, Dict
from django.db.models import Count
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

try:
    from api.models import SequenceLabelingProject
except ImportError:
    import os.path
    from sys import path as sys_path
    # Guessing that we might be in the brat tools/ directory ...

    sys_path.append(os.path.join(ROOT_DIR, 'app'))
    from app.api.models import SequenceLabelingProject


def ensure_project_work_dir(project_name):
    al_dir = os.path.dirname(os.path.dirname(__file__))
    prj_dir = os.path.join(al_dir, 'workdir', project_name)
    if not os.path.exists(prj_dir):
        os.makedirs(prj_dir)
    return prj_dir


def get_tokens_from_tokenizer(text, tokenizer, split_sentences=False):
    sentence_tokens_list = []

    if split_sentences:
        sentences = []
        sent_offsets = []
        offset_pre = 0
        mls = re.finditer('[\r\n]+', text)
        for m in mls:
            offset_cur = m.span()[0]
            sent = text[offset_pre:offset_cur]
            sentences.append(sent)
            sent_offsets.append(offset_pre)
            offset_pre = offset_cur + len(m.group())
    else:
        text = re.sub('[\r\n]', NEW_LINE_CHAR, text)
    if len(sentences) == 0:
        sentences = [text]
        sent_offsets = [0]
    for sent, sent_offset in zip(sentences, sent_offsets):
        seg_result = tokenizer.seg(sent)
        sentence_tokens = []
        for token, offsets in zip(seg_result['tokens'], seg_result['offsets']):
            token_dict = {}
            token_dict['start'], token_dict['end'] = sent_offset+offsets[0], sent_offset+offsets[1]
            token_dict['text'] = token

            # Make sure that the token text does not contain any space
            if len(token_dict['text'].split(' ')) != 1:
                print("WARNING: the text of the token contains space character, replaced with hyphen\n\t{0}\n\t{1}".format(token_dict['text'],
                                                                                                                           token_dict['text'].replace(' ', '-')))
                token_dict['text'] = token_dict['text'].replace(' ', '-')
            sentence_tokens.append(token_dict)
        sentence_tokens_list.append(sentence_tokens)
    return sentence_tokens_list


def doccano_to_conll(project_name: str, tokenizer: Tokenizer, split_sentences: bool = False):
    '''
    Assumes '.txt' and '.ann' files are in the input_folder.
    Checks for the compatibility between .txt and .ann at the same time.

    Args:
    ================================================================
    split_sentences: where split sentences by newline character. if yes, preserve \n character using token NEWLINE
    '''
    def write_conll(documents, output_file):
        for document in documents:
            text, entities = document.text, document.seq_annotations.all()
            entities = sorted(entities, key=lambda entity: entity.start_offset)
            entities = list(map(lambda entity: {'type': entity.label.text,
                                                'start': entity.start_offset, 'end': entity.end_offset}, entities))
            sentences = get_tokens_from_tokenizer(text, tokenizer, split_sentences)
            if len(sentences) == 0:
                assert len(text) == 0, text
                continue
            print('-DOCSTART- -X- -X- O', file=output_file)
            for sentence in sentences:
                inside = False
                previous_token_label = 'O'
                for token in sentence:
                    token['label'] = 'O'
                    for entity in entities:
                        if entity['start'] <= token['start'] < entity['end'] or \
                                entity['start'] < token['end'] <= entity['end'] or \
                                token['start'] < entity['start'] < entity['end'] < token['end']:

                            # Because the ANN doesn't support tag with '-' in it
                            token['label'] = entity['type'].replace('-', '_')

                            break
                        elif token['end'] < entity['start']:
                            break

                    if len(entities) == 0:
                        entity = {'end': 0}
                    if token['label'] == 'O':
                        gold_label = 'O'
                        inside = False
                    elif inside and token['label'] == previous_token_label:
                        gold_label = 'I-{0}'.format(token['label'])
                    else:
                        inside = True
                        gold_label = 'B-{0}'.format(token['label'])
                    if token['end'] == entity['end']:
                        inside = False
                    previous_token_label = token['label']
                    output_file.write('{0} {1} {2} {3} {4}\n'.format(
                        token['text'], project_name, token['start'], token['end'], gold_label))
                output_file.write('\n')

    # find project ins
    project_ins = SequenceLabelingProject.objects.filter(name=project_name).first()
    assert project_ins is not None, "project (%s)` doesn't exist" % project_name
    project_name = project_name.replace(' ', '_')
    prjdir = ensure_project_work_dir(project_name)
    train_filepath = os.path.join(prjdir, 'train.conll')
    test_filepath = os.path.join(prjdir, 'test.conll')
    print("Formatting {0} set from DOCCANO to CONLL... ".format(project_name), end='')
    train_file = codecs.open(train_filepath, 'w', 'utf-8')
    test_file = codecs.open(test_filepath, 'w', 'utf-8')
    try:
        train_data = project_ins.documents.filter(annotations_approved_by__isnull=False)
        test_data = project_ins.documents.annotate(num_anns=Count(
            "seq_annotations")).filter(annotations_approved_by__isnull=True, num_anns__gt=0)
        write_conll(train_data, train_file)
        write_conll(test_data, test_file)
    finally:
        train_file.close()
        test_file.close()
    print('Done.')
