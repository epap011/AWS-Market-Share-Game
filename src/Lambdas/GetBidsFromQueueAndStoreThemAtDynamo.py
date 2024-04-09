import json
import boto3
import uuid
import requests

advertisers_ec2_ipv4_dns = 'ec2-35-173-122-142.compute-1.amazonaws.com'

def lambda_handler(event, context):
    records = event['Records'][0]
    body = records['body']
    body_dic = json.loads(body)
    
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.put_item(
        TableName='Bids',
        Item={
            'Ad_ID': {
                'S': str(uuid.uuid4()),
            },
            'Bid': {
                'S': body_dic['Bid'],
            },
            'Clicks': {
                'N': '0',
            },
            'Sales': {
                'N': '0',
            },
            'Round': {
                'N': body_dic['Round']
            },
            'Player': {
                'S' : body_dic['Player']
            }
        }
    )
    
    response = requests.get('http://'+advertisers_ec2_ipv4_dns+':5000/bid_counter')
    
    return {
        'statusCode': 200
    }

