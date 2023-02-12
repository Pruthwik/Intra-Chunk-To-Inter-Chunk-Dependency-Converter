"""Convert the intra-chunk dependency data into inter-chunk dependency form."""
from argparse import ArgumentParser
import os
from re import search
from re import findall
from re import DOTALL
from re import sub
from collections import OrderedDict


def read_text_from_file(file_path):
    """Read text from a file."""
    with open(file_path, 'r', encoding='utf-8') as file_read:
        return file_read.read().strip()


def write_lines_to_file(lines, file_path):
    """Write lines to a file."""
    with open(file_path, 'w', encoding='utf-8') as file_write:
        file_write.write('\n'.join(lines))


def find_ssf_sentences_from_text(text):
    """Find SSF sentences from text."""
    pattern = "(<Sentence id=.*?>)\n(.*?)\n(</Sentence>)"
    return findall(pattern, text, DOTALL)


def create_morph_dict_for_token(morph_text):
    """Create morph dictionary for a token."""
    morph_dict = {}
    morph_text = sub('\s{2,}', ' ', morph_text)
    morph_features = morph_text.split()
    for feature in morph_features:
        feat, val = feature.split('=')
        morph_dict[feat] = val[1: -1]
    return morph_dict


def find_chunks_and_other_info_from_morph_info(sentence_all_info):
    """Find chunk and other info from morph and other info at sentence level."""
    # wx_utf_dict = {}
    head_to_chunk_map = {}
    chunks_all_info = OrderedDict()
    for token_all_info in sentence_all_info:
        token, pos, morph_dict = token_all_info
        if 'name' in morph_dict:
            token_in_wx = morph_dict['name']
        else:
            morph_dict['name'] = token
            token_in_wx = token
        # wx_utf_dict[token_in_wx] = token
        chunk_type_with_tag = morph_dict['chunkType']
        chunk_type, chunk_tag = chunk_type_with_tag.split(':')
        if chunk_type == 'child':
            morph_dict['head'] = 0
        else:
            morph_dict['head'] = 1
            head_to_chunk_map[token_in_wx] = chunk_tag
        chunks_all_info.setdefault(chunk_tag, []).append((token, pos, morph_dict))
    return chunks_all_info, head_to_chunk_map


def convert_into_interchunk_ssf_from_chunk_info_and_other_dicts_for_sentence(chunks_all_info, head_to_chunk_map):
    """Convert into an SSF sentence from chunk info and other dictionaries."""
    ssf_sentence = []
    for index_chunk, chunk_tag in enumerate(chunks_all_info):
        chunk_addr = str(index_chunk + 1)
        chunk_all_info = chunks_all_info[chunk_tag]
        tokens_info = []
        chunk_drel = ''
        for index_token, (token, pos, morph_dict) in enumerate(chunk_all_info):
            token_addr = chunk_addr + '.' + str(index_token + 1)
            morph_text = "<fs af='" + morph_dict['af'] + "' name='" + token + "'>"
            token_info = '\t'.join([token_addr, token, pos, morph_text])
            tokens_info.append(token_info)
            if morph_dict['head'] == 1:
                if 'drel' in morph_dict:
                    drel_token, parent_token = morph_dict['drel'].split(':')
                    token_in_wx = morph_dict['name']
                    chunk_drel = drel_token + ':' + head_to_chunk_map[parent_token]
        if chunk_drel:
            chunk_features = "<fs drel='" + chunk_drel + "' name='" + chunk_tag + "'>"
        else:
            chunk_features = "<fs name='" + chunk_tag + "'>"
        chunk_tag_no_numeral = search('([A-Z]+)\d*', chunk_tag).group(1)
        chunk_all_text = '\t'.join([chunk_addr, '((', chunk_tag_no_numeral, chunk_features])
        ssf_sentence += [chunk_all_text] + tokens_info + ['\t))']
    ssf_sentence_text = '\n'.join(ssf_sentence)
    return ssf_sentence_text


def convert_into_interchunk_ssf_for_sentences(sentences):
    """Convert into interchunk SSF for sentences in a file."""
    inter_chunk_ssf_sentences = []
    for (header, sentence, footer) in sentences:
        tokens_with_features = sentence.split('\n')
        sentence_all_info = []
        for token_with_features in tokens_with_features:
            addr, token, pos, morph = token_with_features.split('\t')
            morph_dict = create_morph_dict_for_token(morph[4: -1])
            sentence_all_info.append((token, pos, morph_dict))
        chunks_all_info, head_to_chunk_map = find_chunks_and_other_info_from_morph_info(sentence_all_info)
        ssf_sentence_text = convert_into_interchunk_ssf_from_chunk_info_and_other_dicts_for_sentence(chunks_all_info, head_to_chunk_map)
        header = header.replace('"', "'")
        ssf_sentence_with_header_and_footer = '\n'.join([header, ssf_sentence_text, footer])
        inter_chunk_ssf_sentences.append(ssf_sentence_with_header_and_footer + '\n')
    return inter_chunk_ssf_sentences


def main():
    """Pass arguments and call functions here."""
    parser = ArgumentParser()
    parser.add_argument('--input', dest='inp', help='Enter the input file path.')
    parser.add_argument('--output', dest='out', help='Enter the output file path.')
    args = parser.parse_args()
    if not os.path.isdir(args.inp):
        text = read_text_from_file(args.inp)
        intra_chunk_ssf_sentences = find_ssf_sentences_from_text(text)
        inter_chunk_ssf_sentences = convert_into_interchunk_ssf_for_sentences(intra_chunk_ssf_sentences)
        write_lines_to_file(inter_chunk_ssf_sentences, args.out)
    else:
        if not os.path.isdir(args.out):
            os.makedirs(args.out)
        for root, dirs, files in os.walk(args.inp):
            for fl in files:
                input_path = os.path.join(root, fl)
                text = read_text_from_file(input_path)
                intra_chunk_ssf_sentences = find_ssf_sentences_from_text(text)
                inter_chunk_ssf_sentences = convert_into_interchunk_ssf_for_sentences(intra_chunk_ssf_sentences)
                output_path = os.path.join(args.out, fl + '.inter-chunk')
                write_lines_to_file(inter_chunk_ssf_sentences, output_path)


if __name__ == '__main__':
    main()
