import time

import requests
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache

channel_layer = get_channel_layer()



def prediction(raw_input):
    clean_input = clean_text(raw_input)
    input_tok = [nltk.word_tokenize(clean_input)]
    input_tok = [input_tok[0][::-1]]  #reverseing input seq
    encoder_input = transform(encoding, input_tok, 100)
    decoder_input = np.zeros(shape=(len(encoder_input), OUTPUT_LENGTH))
    decoder_input[:,0] = WORD_CODE_START
    for i in range(1, OUTPUT_LENGTH):
        output = model.predict([encoder_input, decoder_input]).argmax(axis=2)
        decoder_input[:,i] = output[:,i]
    return output

def decode(decoding, vector):
    """
    :param decoding: decoding dict built by word encoding
    :param vector: an encoded vector
    """
    text = ''
    for i in vector:
        if i == 0:
            break
        text += ' '
        text += decoding[i]
    return text

def transform(encoding, data, vector_size=20):
    """
    :param encoding: encoding dict built by build_word_encoding()
    :param data: list of strings
    :param vector_size: size of each encoded vector
    """
    transformed_data = np.zeros(shape=(len(data), vector_size))
    for i in range(len(data)):
        for j in range(min(len(data[i]), vector_size)):
            try:
                transformed_data[i][j] = encoding[data[i][j]]
            except:
                transformed_data[i][j] = encoding['<UNK>']
    return transformed_data

import re
def clean_text(text):
    '''Clean text by removing unnecessary characters and altering the format of words.'''
    text = text.lower()
    text = re.sub(r"i'm", "i am", text)
    text = re.sub(r"he's", "he is", text)
    text = re.sub(r"she's", "she is", text)
    text = re.sub(r"it's", "it is", text)
    text = re.sub(r"that's", "that is", text)
    text = re.sub(r"what's", "that is", text)
    text = re.sub(r"where's", "where is", text)
    text = re.sub(r"how's", "how is", text)
    text = re.sub(r"\'ll", " will", text)
    text = re.sub(r"\'ve", " have", text)
    text = re.sub(r"\'re", " are", text)
    text = re.sub(r"\'d", " would", text)
    text = re.sub(r"\'re", " are", text)
    text = re.sub(r"won't", "will not", text)
    text = re.sub(r"can't", "cannot", text)
    text = re.sub(r"n't", " not", text)
    text = re.sub(r"n'", "ng", text)
    text = re.sub(r"'bout", "about", text)
    text = re.sub(r"'til", "until", text)
    text = re.sub(r"[-()\"#/@;:<>{}`+=~|]", "", text)
    text = " ".join(text.split())
    return text

@shared_task
def add(channel_name, x, y):
    message = '{}+{}={}'.format(x, y, int(x) + int(y))
    async_to_sync(channel_layer.send)(channel_name, {"type": "chat.message", "message": message})

"""
@shared_task
def url_status(channel_name, url):
    if not url.startswith('http'):
        url = f'https://{url}'

    status = cache.get(url)
    if not status:
        try:
            r = requests.get(url, timeout=10)
            status = r.status_code
            cache.set(url, status, 60*60)
        except requests.exceptions.RequestException:
            status = 'Not available'

    message = f'{url} status is {status}'
    async_to_sync(channel_layer.send)(channel_name, {"type": "chat.message", "message": message})
"""

@shared_task
def url_status(channel_name, url):
    import nltk
    import numpy as np
    nltk.download('punkt')
    from keras.models import load_model
    model = load_model('static/model_attention.h5')
    import json

    # Opening JSON file
    with open('static/vocab.json') as json_file:
        vocab = json.load(json_file)
    WORD_CODE_START = 1
    WORD_CODE_PADDING = 0

    threshold = 15
    word_num = 2  # number 1 is left for WORD_CODE_START for model decoder later
    encoding = {}
    decoding = {1: 'START'}
    for word, count in vocab.items():
        if count >= threshold:  # get vocabularies that appear above threshold count
            encoding[word] = word_num
            decoding[word_num] = word
            word_num += 1

    decoding[len(encoding) + 2] = ''
    encoding['<UNK>'] = len(encoding) + 2
    output = prediction(url)

    message = str(output)
    async_to_sync(channel_layer.send)(channel_name, {"type": "chat.message", "message": message})
