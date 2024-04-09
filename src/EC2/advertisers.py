#################
#  Advertisers  #
#################

from flask import Flask
from flask import request
from threading import Thread
from threading import Lock
import json
import boto3
import random
import requests
from colorama import Fore, Back, Style

app = Flask(__name__)

EC2_IPV4_DNS = 'ec2-34-205-73-108.compute-1.amazonaws.com'

AWS_REGION = 'us-east-1'
TOPIC_ARN  = 'arn:aws:sns:us-east-1:766412973585:Stats'
ENDPOINT   = 'http://'+EC2_IPV4_DNS+':5000/stats'
NUMBER_OF_ADVERTISERS = 3
sns_client = boto3.client('sns', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
bids_queue_url = 'https://sqs.us-east-1.amazonaws.com/766412973585/Bids'

shared_bids_counter = 0
lock = Lock()
MAX_ROUNDS = 9
curr_round = 0
PRODUCT_PRICE = 299.99

PLAYER_LIST  = ['Intel', 'AMD', 'Nvidia']
player_stats = {}
for player in PLAYER_LIST:
    player_stats[player] = {}
    player_stats[player]['Stats'] = {}
    player_stats[player]['Stats']['Clicks']   = []
    player_stats[player]['Stats']['Sales']    = []
    player_stats[player]['Stats']['Revenues'] = []
    player_stats[player]['Stats']['Cost']     = []
    player_stats[player]['Stats']['Bid']      = []
    player_stats[player]['Stats']['Profit']   = []

@app.route('/start_game', methods=['GET'])
def start_game():
    thread_players = []
    for player in PLAYER_LIST:
        bid = random.randint(1, 15)
        message = {}
        message['Player'] = player
        message['Bid']    = str(bid)
        message['Round']  = str(curr_round)
        thread_player = Thread(target=send_bid_to_sqs, args=(message,))
        thread_player.start()
        thread_players.append(thread_player)

    for t in thread_players:
        t.join()

    return 'Game Started'

@app.route('/stats', methods=['POST'])
def get_stats_notification():
    global curr_round
    data = json.loads(request.data)
    if data['Type'] == 'SubscriptionConfirmation':
        print(Fore.BLUE, 'Subscription to Stats has been Confirmed', Fore.RESET)
        token = data['Token']
        response = sns_client.confirm_subscription(
            TopicArn=TOPIC_ARN,
            Token=token
        )
    elif data['Type'] == 'Notification':
        message = json.loads(data['Message'])
        thread_players = []
        curr_round = curr_round + 1
        for player in message:
            update_stats(player, message[player])
            thread_player = Thread(target=calculate_new_bid, args=(player,))
            thread_player.start()
            thread_players.append(thread_player)

        for t in thread_players:
            t.join()

        if(curr_round-1 == MAX_ROUNDS):
            print(Fore.BLUE, 'Game Finished', Fore.RESET)
            curr_rounds = 0
            exit()
    
    return "[Get Stats Notification]"

@app.route('/bid_counter', methods=['GET'])
def count_bid():
    global shared_bids_counter
    with lock:
        shared_bids_counter = shared_bids_counter + 1
        if shared_bids_counter == NUMBER_OF_ADVERTISERS:
            shared_bids_counter = 0
            message = {}
            message['Running_Round'] = curr_round
            response = sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:766412973585:AllBidsAreReady',
                Message=json.dumps(message)
            )
            
    return "bid_counter"

def update_stats(player, stats):
    bid      = float(stats['Bid'])
    clicks   = int(stats['Clicks'])
    sales    = int(stats['Sales'])
    cost     = clicks*bid
    revenues = sales*PRODUCT_PRICE
    profit   = revenues - cost
    
    player_stats[player]['Stats']['Bid'].append(bid)
    player_stats[player]['Stats']['Clicks'].append(clicks)
    player_stats[player]['Stats']['Sales'].append(sales)
    player_stats[player]['Stats']['Revenues'].append(revenues)
    player_stats[player]['Stats']['Cost'].append(cost)
    player_stats[player]['Stats']['Profit'].append(profit)

def send_bid_to_sqs(message):
    sqs_client.send_message(QueueUrl=bids_queue_url, MessageBody=json.dumps(message))

def calculate_new_bid(player):
    bid      = player_stats[player]['Stats']['Bid'][curr_round-1]
    clicks   = player_stats[player]['Stats']['Clicks'][curr_round-1]
    sales    = player_stats[player]['Stats']['Sales'][curr_round-1]
    profit   = player_stats[player]['Stats']['Profit'][curr_round-1]
    revenues = player_stats[player]['Stats']['Revenues'][curr_round-1]
    cost     = player_stats[player]['Stats']['Cost'][curr_round-1]
     
    if sales >= clicks/2:
        new_bid = bid * 0.75
    else:
        new_bid = bid * 1.50

    print(Fore.GREEN,'#Round ', curr_round-1)
    print(Fore.YELLOW, 'PLayer: ', player, ' Revenues: ', round(revenues,2), ' Cost: ', round(cost,2), ' Profit: ', round(profit,2), ' Bid: ', round(bid,2), Fore.RESET)
    
    message = {}
    message['Player'] = player
    message['Bid']    = str(new_bid)
    message['Round']  = str(curr_round)
    if(curr_round-1 < MAX_ROUNDS):
        send_bid_to_sqs(message)
    
if __name__ == "__main__":
    response = sns_client.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol='http',
        Endpoint=ENDPOINT
    )

    app.run(host='0.0.0.0')
