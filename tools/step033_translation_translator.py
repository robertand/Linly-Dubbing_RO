# -*- coding: utf-8 -*-
import json
import os
import translators as ts
from dotenv import load_dotenv
from loguru import logger
load_dotenv()

def translator_response(messages, to_language = 'zh-CN', translator_server = 'bing'):
    if '中文' in to_language or 'Chinese' in to_language:
        to_language = 'zh-CN'
    elif 'English' in to_language:
        to_language = 'en'
    elif 'Romanian' in to_language:
        to_language = 'ro'
    translation = ''
    for retry in range(3):
        try:
            translation = ts.translate_text(query_text=messages, translator=translator_server, from_language='auto', to_language=to_language)
            break
        except Exception as e:
            logger.info(f'translate failed! {e}')
            print('tranlate failed!')
    return translation

if __name__ == '__main__':
    # Test Bing translation to Chinese
    response = translator_response('Hello, how are you?', 'Chinese', 'bing')
    print(f"Bing (to Chinese): {response}")

    # Test Google translation to English
    response = translator_response('Hello, how are things lately? ', 'en', 'google')
    print(f"Google (to English): {response}")