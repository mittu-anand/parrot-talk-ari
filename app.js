require('dotenv').config();
const ari = require('ari-client');

// Use environment variables
const ARI_URL = process.env.ARI_URL;
const ARI_USERNAME = process.env.ARI_USERNAME;
const ARI_PASSWORD = process.env.ARI_PASSWORD;

ari.connect(ARI_URL, ARI_USERNAME, ARI_PASSWORD, (err, client) => {
  if (err) {
    console.error('Error connecting to ARI:', err);
    return;
  }

  console.log('Connected to ARI');

  // Create peers
  createPeers(client, ['8001', '8002', '8003', '8004', '8005']);
});

const createPeers = (client, peerIds) => {
  peerIds.forEach(peerId => {
    const peerConfig = {
      type: 'SIP',
      name: peerId,
      secret: `password_for_${peerId}`, // Use a strong password for each peer
      context: 'parrot_ari_dialers', // Make sure this context is configured in extensions.conf
      host: 'dynamic',
    };

    client.endpoints.create(peerConfig, (err, peer) => {
      if (err) {
        console.error(`Error creating peer ${peerId}:`, err);
        return;
      }
      console.log(`Peer ${peerId} created successfully!`);
      
      // Optionally, you can make calls between peers after creating them
      if (peerId === '8005') {
        makeCall(client, '8001', '8002'); // Example: make a call between 8001 and 8002
      }
    });
  });
};

const makeCall = (client, fromPeer, toPeer) => {
  client.channels.originate({
    endpoint: `sip:${toPeer}`,
    app: 'parrot_ari_dialers', // The application defined in extensions.conf
    callerId: fromPeer,
  }, (err, channel) => {
    if (err) {
      console.error(`Error making call from ${fromPeer} to ${toPeer}:`, err);
      return;
    }
    console.log(`Call from ${fromPeer} to ${toPeer} initiated successfully!`);
  });
};
