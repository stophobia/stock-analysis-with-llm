import json
import re
import ast
import uuid
import boto3
from botocore.config import Config
import functools
import time

from aws_lambda_powertools import Logger

logger = Logger()

MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
PATTERN = r'\[.*?\]'
ANTHROPIC_VERSION = 'bedrock-2023-05-31'

config = Config(read_timeout=60 * 15)
brt = boto3.client(service_name='bedrock-runtime',
                   config=config)
brt_agent = boto3.client(service_name='bedrock-agent-runtime',
                         config=config)


def parse_response(response):
    regex_result = re.search(PATTERN, response, re.DOTALL)
    regex_result = regex_result.group(0)
    return ast.literal_eval(regex_result)


def invoke_model(messages, system_prompt):
    body = json.dumps(
        {
            "anthropic_version": ANTHROPIC_VERSION,
            "max_tokens": 2500,
            "system": system_prompt,
            "temperature": 0,
            "messages": messages
        }
    )
    response = brt.invoke_model(body=body, modelId=MODEL_ID)
    response_body = json.loads(response.get('body').read())

    try:
        response = json.loads(response_body['content'][0]['text'])
    except Exception as e:
        logger.info(f'Error parse response: {e}')
        try:
            logger.info(f'Error parse response: {e}')
            response = parse_response(response_body['content'][0]['text'])
        except Exception as e:
            logger.info(f'Error parse response: {e}')
            response = response_body['content'][0]['text']

    return response


def invoke_agent(input_text):
    # Note: The execution time depends on the foundation model, complexity of the agent,
    # and the length of the prompt. In some cases, it can take up to a minute or more to
    # generate a response.
    response = brt_agent.invoke_agent(
        # ToDo: Update manually with AgentID and AgentAliasId until AWS CDK support AWS Bedrock Agents
        agentId='VBVCRTAYMV',
        agentAliasId='ECZGMVPR1S',
        sessionId=str(uuid.uuid4()),
        inputText=input_text
    )

    completion = ""

    for event in response.get("completion"):
        chunk = event["chunk"]
        completion = completion + chunk["bytes"].decode()

    return completion


def get_stocks(finance_api):
    stocks = []
    for industry, stocks_list in finance_api.industries.items():
        if len(stocks_list) < 4:
            continue
        stocks.append(stocks_list)
    return [stock for industry_stock in stocks for stock in industry_stock]


def retry(retries=3, delay=60 * 5):
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.info(f"Attempt {attempt + 1} failed: {e}")
                    if 'ThrottlingException' in str(e) or 'AWSHTTPSConnectionPool' in str(e):
                        if attempt < retries - 1:
                            time.sleep(delay)
                        else:
                            logger.info("All attempts failed. Continue...")

        return wrapper_retry

    return decorator_retry
