import yaml
from pathlib import Path
import boto3
import json
from boto3.dynamodb.conditions import Key
import requests
import base64
import traceback
import logging
from ..logs import log

logger = logging.getLogger('robot')
path = Path('lib/config/config.yaml')
line_token = '3QBqP6iA8I2hxVhLPdt7WlRKb8sBSAmeJv8mTFvBeEF'
# 讀取yaml
def load_setting():
    with path.open('r', encoding='utf-8') as f:
        data = yaml.load(f.read(), yaml.SafeLoader)
    return data

# 寫入yaml
def save_setting(data):
    with path.open('w', encoding='utf-8') as w:
        yaml.dump(data, w, allow_unicode=True, encoding='utf-8', sort_keys=False)
    return

# 讀取dynamodb
def query_aws_db():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('config')
    resp = table.query(KeyConditionExpression=Key('Features').eq('support'))
    return resp

# 更新dynamodb
def update_aws_db(support):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('config')
    resp = table.update_item(
        Key={"Features":"support"},
        UpdateExpression="set content=:c",
        ExpressionAttributeValues={":c":json.dumps(support)},
        ReturnValues="UPDATED_NEW"
    )
    return resp

# 發送LINE訊息
def line(message:str ='', line_token:str = line_token, **kwarg):
    url = 'https://notify-api.line.me/api/notify'
    headers = {
        'Authorization': 'Bearer ' + line_token,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    payload = {'message':message}
    if kwarg.get('stickerPackageId') and kwarg.get('stickerId'):
        payload['stickerPackageId'] = kwarg['stickerPackageId']
        payload['stickerId'] = kwarg['stickerId']
    resp = requests.post(url, headers=headers,data=payload)
    if resp.status_code != 200:
        return {"status":resp.status_code,"message":"發送失敗"}
    return resp.json()