import json
import requests

advertisers_ec2_ipv4_dns = 'ec2-35-173-122-142.compute-1.amazonaws.com'

def lambda_handler(event, context):
    response = requests.get('http://'+advertisers_ec2_ipv4_dns+':5000/start_game')
    print(response.status_code)
    return {
        'statusCode': 200
    }

