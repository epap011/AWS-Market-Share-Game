import json
import boto3
import requests

clients_ec2_ipv4_dns = 'ec2-44-201-238-13.compute-1.amazonaws.com'

def lambda_handler(event, context):
    dynamodb_client = boto3.client("dynamodb")
    
    records = event['Records'][0]
    body = json.loads(records['body'])
    
    for ad_id in body:
        stats  = body[ad_id]
        is_clicked    = stats['Click']
        is_parchased  = stats['Purchase']
        try:
            if is_clicked == True:
                response = dynamodb_client.update_item(
                    TableName='Bids',
                    Key={'Ad_ID': {
                            'S': ad_id
                        }
                    },
                    UpdateExpression = 'ADD #Clicks :increase',
                    ExpressionAttributeNames = {
                        '#Clicks': 'Clicks'
                    },
                    ExpressionAttributeValues = {
                        ':increase': {
                            'N': '1',
                        },  
                    },
                    ReturnValues = 'UPDATED_NEW'
                )
                if is_parchased == True:
                    response = dynamodb_client.update_item(
                        TableName='Bids',
                        Key={'Ad_ID': {
                                'S': ad_id
                            }
                        },
                        UpdateExpression = 'ADD #Sales :increase',
                        ExpressionAttributeNames = {
                            '#Sales': 'Sales'
                        },
                        ExpressionAttributeValues = {
                            ':increase': {
                                'N': '1',
                            },
                        },
                        ReturnValues = 'UPDATED_NEW'
                    )
        except:
            print('Unexpected Error')
            
            
    requests.get('http://'+clients_ec2_ipv4_dns+':5000/stat_counter')
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

