import json
import boto3

def lambda_handler(event, context):
    records = event['Records'][0]
    sns_message = records['Sns']['Message']
    sns_message_dict = json.loads(sns_message)    
    running_round = int(sns_message_dict['Running_Round'])
    
    print(running_round)
    
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.scan(
        TableName='Bids'
    )
    
    items   = response['Items']
    message = {}
    for i in range(len(items)):
        item = json.loads(json.dumps(items[i]))
        if int(item['Round']['N']) != running_round:
            continue
        player = item['Player']['S']
        message[player]={}
        message[player]['Bid']    = item['Bid']['S']
        message[player]['Clicks'] = item['Clicks']['N']
        message[player]['Sales']  = item['Sales']['N']
        
    sns_client = boto3.client('sns')
    response = sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:766412973585:Stats',
        Message=json.dumps(message)
    )
    
    return {
        'statusCode': 200
    }
