# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import time
import os
import sys
from datetime import datetime
import logging
from sys import stdout
import requests


# 计算签名摘要函数
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


# 获取Authorization
def get_authorization(payload, timestamp, host='dnspod.tencentcloudapi.com', service='dnspod'):
    algorithm = 'TC3-HMAC-SHA256'
    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    # ************* 步骤 1：拼接规范请求串 *************
    logger.info('************* 1 create canonical_request *************')
    http_request_method = 'POST'
    canonical_uri = '/'
    canonical_querystring = ''
    ct = 'application/json; charset=utf-8'

    canonical_headers = 'content-type:%s\nhost:%s\n' % (ct, host)
    signed_headers = 'content-type;host'
    hashed_request_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = (http_request_method + '\n' +
                         canonical_uri + '\n' +
                         canonical_querystring + '\n' +
                         canonical_headers + '\n' +
                         signed_headers + '\n' +
                         hashed_request_payload)

    # ************* 步骤 2：拼接待签名字符串 *************
    logger.info('************* 2 create string_to_sign *************')
    credential_scope = date + '/' + service + '/' + 'tc3_request'
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    string_to_sign = (algorithm + '\n' +
                      str(timestamp) + '\n' +
                      credential_scope + '\n' +
                      hashed_canonical_request)

    # ************* 步骤 3：计算签名 *************
    logger.info('************* 3 create signature *************')

    secret_date = sign(('TC3' + secret_key).encode('utf-8'), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, 'tc3_request')
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # ************* 步骤 4：拼接 Authorization *************
    logger.info('************* 4 create authorization *************')
    authorization = (algorithm + ' ' +
                     'Credential=' + secret_id + '/' + credential_scope + ', ' +
                     'SignedHeaders=' + signed_headers + ', ' +
                     'Signature=' + signature)
    return authorization


# 运行api方法
def get_proxies():
    # 设置网络环境
    proxies = {}
    if enable_proxy:
        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }
    return proxies


def execute_api_method(action, params, host='dnspod.tencentcloudapi.com', service='dnspod', version='2021-03-23'):
    payload = json.dumps(params)
    # 获取Authorization
    timestamp = int(time.time())
    authorization = get_authorization(payload, timestamp, host=host, service=service)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json; charset=utf-8',
        'Host': host,
        'X-TC-Action': action,
        'X-TC-Timestamp': str(timestamp),
        'X-TC-Version': version,
    }
    proxies = get_proxies()
    endpoint = 'https://' + host
    return requests.post(endpoint, headers=headers, data=payload, proxies=proxies)


def get_real_public_ip():
    #ip_url = 'https://api.ipify.org'
    ip_url = 'https://ipinfo.io/ip'
    return requests.get(ip_url, proxies=get_proxies())


def get_record_id(record_list, sub_domain):
    sub_domain_list = record_list.get('Response').get('RecordList')
    for e in sub_domain_list:
        if sub_domain.__eq__(e.get('Name')):
            return e.get('RecordId')
    return None


def add_sub_domain():
    action = 'CreateRecord'
    params = {
        'Domain': domain,
        'SubDomain': sub_domain,
        'RecordType': 'A',
        'RecordLine': '默认',
        'Value': get_real_public_ip().text
    }
    execute_api_method(action, params).text


def get_sub_domain_record_id():
    action = 'DescribeRecordList'
    params = {
        'Domain': domain
    }
    record_list = json.loads(execute_api_method(action, params).text)
    get_record_id(record_list, sub_domain)
    sub_domain_list = record_list.get('Response').get('RecordList')
    for e in sub_domain_list:
        if sub_domain.__eq__(e.get('Name')):
            logger.info('Name is ' + e.get('Name'))
            logger.info('RecordId is ' + str(e.get('RecordId')))
            logger.info('Value is ' + e.get('Value'))
            return e.get('RecordId')
    # if configured auto create sub_domain then add a new record
    if auto_add_sub_domain:
        add_sub_domain()
        # get_sub_domain_record_id()


def update_sub_domain_dns(sub_domain_record_id):
    action = 'ModifyDynamicDNS'
    params = {
        'Domain': domain,
        'SubDomain': sub_domain,
        'RecordId': sub_domain_record_id,
        'RecordLine': '默认',
        'Value': get_real_public_ip().text
    }
    logger.info('domain is ' + domain + ' , sub_domain is ' + sub_domain)
    logger.info('public ip is ' + get_real_public_ip().text)
    execute_api_method(action, params)
    logger.info('Updated subdomain successfully!')


if __name__ == '__main__':
    # 定义logger
    logger = logging.getLogger('auto-ddns-logger')
    logger.setLevel(logging.DEBUG)
    logFormatter = logging.Formatter \
        ("%(name)-12s %(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s")
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    # 获取环境变量
    env_dist = os.environ
    secret_id = env_dist.get('TC3_SECRET_ID')
    secret_key = env_dist.get('TC3_SECRET_KEY')
    domain = env_dist.get('TC3_DNSPOD_DOMAIN')
    sub_domain = env_dist.get('TC3_DNSPOD_SUB_DOMAIN')

    # 检查必须的环境变量
    if secret_id is None:
        logger.error('secret_id not exists')
        sys.exit()
    if secret_key is None:
        logger.error('secret_key not exists')
        sys.exit()
    if domain is None:
        logger.error('domain not exists')
        sys.exit()
    if sub_domain is None:
        logger.error('sub_domain not exists')
        sys.exit()

    # 设置网络环境代理，默认为False
    enable_proxy = env_dist.get('ENABLE_PROXY') if env_dist.get('ENABLE_PROXY') else False
    if enable_proxy:
        http_proxy = env_dist.get('HTTP_PROXY')
        https_proxy = env_dist.get('HTTPS_PROXY')

    # 是否自动注册不存在的subdomain，默认为True
    auto_add_sub_domain = env_dist.get('AUTO_ADD_SUB_DOMAIN') if env_dist.get('AUTO_ADD_SUB_DOMAIN') else True

    # 设置定时调度间隔，单位为秒，默认为60
    sleep_secs = env_dist.get('SLEEP_SECS') if env_dist.get('SLEEP_SECS') else 60

    while True:
        # 获取域名的解析记录并获得sub_domain对应的record_id
        sub_domain_record_id = get_sub_domain_record_id()
        # 更新动态DNS记录
        update_sub_domain_dns(sub_domain_record_id)
        # 休眠60s
        time.sleep(int(sleep_secs))
