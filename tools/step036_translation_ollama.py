# -*- coding: utf-8 -*-
import json
import os
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def ollama_response(messages, model_name=None):
    """
    Process translation using Ollama API

    Args:
        messages: List of messages compatible with OpenAI format
        model_name: Ollama model name, if None, get from environment variables

    Returns:
        Translated text result
    """
    model_name = os.getenv('OLLAMA_MODEL', 'qwen2.5:14b')

    # 获取Ollama API的URL
    base_url = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api')
    url = f"{base_url}/chat"

    # 准备请求数据
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }

    try:
        logger.info(f"Translating using Ollama model {model_name}...")
        response = requests.post(url, json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()
            return result.get('message', {}).get('content', '')
        else:
            logger.error(f"Ollama API request failed, status code: {response.status_code}")
            logger.error(f"Error details: {response.text}")
            raise Exception(f"Ollama API request failed, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {str(e)}")
        raise


def ollama_stream_response(messages, model_name=None):
    """
    Process streaming translation using Ollama API (suitable for long texts)

    Args:
        messages: List of messages compatible with OpenAI format
        model_name: Ollama model name, if None, get from environment variables

    Returns:
        Full translated text result
    """
    if model_name is None:
        model_name = os.getenv('OLLAMA_MODEL', 'qwen2.5:14b')

    # 获取Ollama API的URL
    base_url = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api')
    url = f"{base_url}/chat"

    # 准备请求数据
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }

    try:
        logger.info(f"Streaming translation using Ollama model {model_name}...")
        response = requests.post(url, json=payload, timeout=300, stream=True)

        if response.status_code == 200:
            # Collect all results from the streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_data = json.loads(line.decode('utf-8'))
                    if 'message' in line_data and 'content' in line_data['message']:
                        content = line_data['message']['content']
                        full_response += content

            return full_response
        else:
            logger.error(f"Ollama streaming API request failed, status code: {response.status_code}")
            logger.error(f"Error details: {response.text}")
            raise Exception(f"Ollama streaming API request failed, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error during Ollama streaming communication: {str(e)}")
        raise


if __name__ == '__main__':
    # Test basic translation function
    test_message = [{"role": "user", "content": "Hello, please introduce yourself"}]
    response = ollama_response(test_message)
    print(f"Basic response:\n{response}\n")

    # Test translation function
    translate_message = [
        {"role": "system", "content": "You are a professional translator. You need to translate English text into fluent and natural Chinese."},
        {"role": "user",
         "content": "Translate this sentence to Chinese: 'The quick brown fox jumps over the lazy dog.'"}
    ]
    translation = ollama_response(translate_message)
    print(f"翻译结果:\n{translation}")

