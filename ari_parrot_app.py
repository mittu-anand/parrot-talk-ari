from ari import connect, events
from flask import Flask, request, jsonify

app = Flask(__name__)
client = None

# --- Peer Management ---

peers = {}  # Dictionary to store peer information

def create_peer(username, password):
    peers[username] = {'password': password}

def get_peer(username):
    return peers.get(username)

# --- Call Handling ---

def originate_and_bridge(channel1_id, username2):
    global client
    peer2 = get_peer(username2)
    if peer2:
        # Use SIP endpoint instead of PJSIP
        channel2 = client.channels.originate(endpoint=f'SIP/{username2}', app='parrot_ari_dialers')
        bridge = client.bridges.create(type='mixing')
        client.bridges.addChannel(bridgeId=bridge.id, channel=[channel1_id, channel2.id])
    else:
        print(f"Peer {username2} not found")

# --- IVR Functionality ---

def on_stasis_start(channel, event):
    global client
    extension = event.get('args',)  # Get dialed extension/username from dialplan
    if extension:  # Direct dial
        originate_and_bridge(channel.id, extension)
    else:  # IVR
        channel.answer()
        channel.play(media='sound:ivr-welcome')
        channel.getDigits(numDigits=1, timeout=5000, callbackUrl='http://ari.parrottalk.co.uk/ivr-input')

def on_dtmf_received(channel, event):
    digit = event['digit']
    if digit == '1':
        # Get more input (e.g., account number)
        channel.getDigits(numDigits=5, timeout=5000, callbackUrl='http://ari.parrottalk.co.uk/ivr-account')
    elif digit == '2':
        # Transfer to another extension/peer
        channel.play(media='sound:ivr-transfer')
        channel.getDigits(numDigits=3, timeout=5000, callbackUrl='http://ari.parrottalk.co.uk/ivr-extension')
    else:
        channel.play(media='sound:invalid-input')

# --- Flask API Endpoints ---

@app.route('/ivr-input', methods=['POST'])
def ivr_input():
    data = request.get_json()
    digit = data['digit']
    channel_id = data['channel']['id']
    channel = client.channels.get(channelId=channel_id)
    #... process digit and potentially get more input...
    return jsonify({})

@app.route('/ivr-account', methods=['POST'])
def ivr_account():
    data = request.get_json()
    account_number = data['digits']
    channel_id = data['channel']['id']
    channel = client.channels.get(channelId=channel_id)
    #... process account number and route the call...
    return jsonify({})

@app.route('/ivr-extension', methods=['POST'])
def ivr_extension():
    data = request.get_json()
    extension = data['digits']
    channel_id = data['channel']['id']
    channel = client.channels.get(channelId=channel_id)
    originate_and_bridge(channel_id, extension)
    return jsonify({})

# --- Main ARI Logic ---

def main():
    global client
    client = connect('http://localhost:8088/ari', 'parrot_ari_user', 'parrot-ari-talk-06')
    client.on_channel_event('StasisStart', on_stasis_start)
    client.on_channel_event('ChannelDtmfReceived', on_dtmf_received)

    # Create some initial peers
    create_peer('1001', 'password123')
    create_peer('1002', 'password456')

    client.run(apps='parrot_ari_dialers')

if __name__ == '__main__':
    app.run(debug=True)
