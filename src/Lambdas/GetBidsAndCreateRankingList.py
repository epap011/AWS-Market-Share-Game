import json
import boto3

def lambda_handler(event, context):
    records = event['Records'][0]
    sns_message = records['Sns']['Message']
    sns_message_dict = json.loads(sns_message)    
    running_round = sns_message_dict['Running_Round']
    
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.scan(
        TableName='Bids'
    )
    
    items = response['Items']
    ranking_list = []
    bids   = []
    ad_ids = []
    for i in range(len(items)):
        item = json.loads(json.dumps(items[i]))
        if int(item['Round']['N']) != running_round:
            continue
        bids.append(item['Bid']['S'])
        ad_ids.append(item['Ad_ID']['S'])
    
    ranking_list = list(zip(ad_ids, bids))
    ranking_list.sort(key=lambda y: y[1],reverse=True)
    
    ranking_list_dict = dict(ranking_list)
    
    for ad in ranking_list_dict:
        ranking_list_dict[ad] = {}
    
    sns_client = boto3.client('sns')
    response = sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:766412973585:Ads',
        Message=json.dumps(ranking_list_dict)
    )
    
    return {
        'statusCode': 200
    }
