"""
MQTT Topic Bridging Script for Meshtastic

This script bridges MQTT topics from a local MQTT broker to a remote MQTT broker with topic transformation.
It subscribes to a specified topic on the local broker, processes incoming messages, and republishes them on the remote broker with a different topic prefix. 

Features:
- Connects to a local MQTT broker and subscribes to a specified topic.
- Connects to a remote MQTT broker and republishes messages with a transformed topic.
- Uses logging to output connection status and message forwarding details, which can be viewed in systemd logs when run as a service.
- Configured to handle username and password authentication for both brokers.
- (Optional) Integrates with systemd to run as a managed service with automatic restarts on failure.

Configuration:
- Update the local and remote broker details including addresses, ports, topics, and credentials.
- (Optional) Ensure the script is set up as a systemd service for persistent and managed running.

To use:
1. Install the required Python library `paho-mqtt` using pip.  (pip3 install paho-mqtt)
2. Update the script below with your specific MQTT broker details and credentials.
3. (Optional) Update the path and enable the provided systemd service file to run the script as a service, auto-restarting on failure and reboot.

Example: 
In the default setup below, incoming message from LOCAL_TOPIC msh/US/2/e/LongFast/ are republished on the remote server with REMOTE_TOPIC egr/home/2/e/LongFast/

"""

import paho.mqtt.client as mqtt
import logging
import sys
import time

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()


#####      EDIT THE DETAILS BELOW HERE      #####
#-----------------------------------------------#
# Local MQTT broker details 
LOCAL_BROKER = "local-mqtt-ip-or-hostname-here"
LOCAL_PORT = 1883
LOCAL_TOPIC = "msh/US/2/e/LongFast/#" #do not remove the # at the end of the local topic
LOCAL_USERNAME = "local-username-goes-here"
LOCAL_PASSWORD = "local-password-goes-here"

# Remote MQTT broker details
REMOTE_BROKER = "remote-mqtt-ip-or-hostname-here"
REMOTE_PORT = 1883
REMOTE_TOPIC_PREFIX = "egr/home/2/e/LongFast/"
REMOTE_USERNAME = "remote-username-goes-here"
REMOTE_PASSWORD = "remote-password-goes-here"
#-----------------------------------------------#
#####          STOP EDITING HERE            #####



# Callback when a message is received from the local broker
def on_local_message(client, userdata, message):
    # Construct the new topic
    local_topic_suffix = message.topic[len("msh/US/2/e/LongFast/"):]
    remote_topic = REMOTE_TOPIC_PREFIX + local_topic_suffix

    # Publish the message to the remote broker
    result = remote_client.publish(remote_topic, message.payload)
    status = result.rc
    if status == mqtt.MQTT_ERR_SUCCESS:
        logger.info(f"Message sent to topic {remote_topic}")
    else:
        logger.error(f"Failed to send message to topic {remote_topic}")


# Callback for successful connection to the broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected successfully to {client._host}")
        client.subscribe(LOCAL_TOPIC)
    else:
        logger.error(f"Connection failed with code {rc}")


# Callback when disconnected from a broker
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"Unexpected disconnection from {client._host}, attempting to reconnect...")
        try:
            client.reconnect()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")



# Create a client for the local broker
local_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="", protocol=mqtt.MQTTv5, transport="tcp")
local_client.username_pw_set(LOCAL_USERNAME, LOCAL_PASSWORD)
local_client.on_message = on_local_message
local_client.on_connect = on_connect
local_client.on_disconnect = on_disconnect  # Handle disconnects

# Create a client for the remote broker
remote_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="", protocol=mqtt.MQTTv5, transport="tcp")
remote_client.username_pw_set(REMOTE_USERNAME, REMOTE_PASSWORD)
remote_client.on_connect = on_connect
remote_client.on_disconnect = on_disconnect  # Handle disconnects

# Connect to the local broker
def connect_local():
    try:
        local_client.connect(LOCAL_BROKER, LOCAL_PORT, 60)
    except Exception as e:
        logger.error(f"Failed to connect to local broker: {e}")

# Connect to the remote broker
def connect_remote():
    try:
        remote_client.connect(REMOTE_BROKER, REMOTE_PORT, 60)
    except Exception as e:
        logger.error(f"Failed to connect to remote broker: {e}")

# Attempt to connect both brokers
connect_local()
connect_remote()

# Start the loop to process messages
local_client.loop_start()
remote_client.loop_start()

# Keep the script running
try:
    while True:
        time.sleep(0.1)  # Add a small delay to reduce CPU usage
except KeyboardInterrupt:
    pass

# Stop the loop and disconnect
local_client.loop_stop()
remote_client.loop_stop()
local_client.disconnect()
remote_client.disconnect()