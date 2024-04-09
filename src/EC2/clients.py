#############
#  Clients  #
#############

from flask import Flask
from flask import request
from threading import Thread
from threading import Lock
import json
import boto3
import random
from colorama import Fore, Back, Style

app = Flask(__name__)

EC2_IPV4_DNS = 'ec2-44-204-14-138.compute-1.amazonaws.com'

AWS_REGION = 'us-east-1'
TOPIC_ARN  = 'arn:aws:sns:us-east-1:766412973585:Ads'
ENDPOINT   = 'http://'+EC2_IPV4_DNS+':5000/ads'
sns_client = boto3.client('sns', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
action_queue_url = 'https://sqs.us-east-1.amazonaws.com/766412973585/Action'

DIFFERENT_QUALITY_PRODUCTS = True #False = Scenario A, True = Scenario B
NUMBER_OF_CLIENTS = 10
MAX_ROUNDS = 9
curr_round = 0
shared_stats_counter = 0
lock = Lock()

purchase_probabilities = {}
purchase_probabilities['Intel']  = '0.10'
purchase_probabilities['AMD']    = '0.70'
purchase_probabilities['Nvidia'] = '0.20'

@app.route('/ads', methods=['POST'])
def get_ads_notification():
    global curr_round
    data = json.loads(request.data)
    if data['Type'] == 'SubscriptionConfirmation':
        print(Fore.BLUE, 'Subscription to Ads has been Confirmed', Fore.RESET)
        token = data['Token']
        response = sns_client.confirm_subscription(
            TopicArn=TOPIC_ARN,
            Token=token
        )
    elif data['Type'] == 'Notification':
        message = json.loads(data['Message'])
        curr_round = curr_round + 1
        for i in range(NUMBER_OF_CLIENTS):
            thread_player = Thread(target=show_ads, args=(i, message))
            thread_player.start()

        if(curr_round == MAX_ROUNDS):
            print(Fore.BLUE, 'Game Finished', Fore.RESET)
            curr_rounds = 0

    return "[Get Ads Notification]"

@app.route('/stat_counter', methods=['GET'])
def count_stat():
    global shared_stats_counter
    with lock:
        shared_stats_counter = shared_stats_counter + 1
        if shared_stats_counter == NUMBER_OF_CLIENTS:
            shared_stats_counter = 0
            message  = {}
            message['Running_Round'] = curr_round-1
            response = sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:766412973585:AllStatsAreUpdated',
                Message=json.dumps(message)
            )

    return "update_stats_counter"


def send_action_to_sqs(action):
    message = {}
    message = action
    message_json = json.dumps(message)
    sqs_client.send_message(QueueUrl=action_queue_url, MessageBody=message_json)

def show_ads(client_id, ads):
    click_probabilities    = [0.60, 0.25, 0.15]

    if DIFFERENT_QUALITY_PRODUCTS == False: #same quality products => same purchase prob.
        purchase_probabilities['Intel']  = '0.70'
        purchase_probabilities['AMD']    = '0.70'
        purchase_probabilities['Nvidia'] = '0.70'

    click_tries    = [random.randint(1,100), random.randint(1,100), random.randint(1,100)]
    purchase_tries = [random.randint(1,100), random.randint(1,100), random.randint(1,100)]

    i = 0
    for ad in ads:
        if click_tries[i] <= click_probabilities[i]*100:
            ads[ad]['Click'] = True
            advertiser = ads[ad]['Player']
            if purchase_tries[i] <= float(purchase_probabilities[advertiser])*100:
                ads[ad]['Purchase'] = True
            else:
                ads[ad]['Purchase'] = False
        else:
            ads[ad]['Click']    = False
            ads[ad]['Purchase'] = False

        if ads[ad]['Click'] == True:
            print(Fore.GREEN + '#Round ', curr_round-1)
            print(Fore.YELLOW + 'Client ID: ',client_id, ' Advertiser: ', ads[ad]['Player'],' Ad_ID: ', ad, ' Purchase: ', ads[ad]['Purchase'], Fore.RESET)
        i = i + 1

    send_action_to_sqs(ads)    

if __name__ == "__main__":
    response = sns_client.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol='http',
        Endpoint=ENDPOINT
    )

    app.run(host='0.0.0.0')
