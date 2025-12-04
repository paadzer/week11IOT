import network
import time
import machine
from umqtt.simple import MQTTClient
import sensor_upb2   # this is your *_upb2.py file from protoc
from uprotobuf import *

# ================= WIFI SETTINGS =================
SSID = "patricks Iphone"
PASSWORD = "patrick03"

# ============ REQUIRED GLOBAL VARIABLES ==========
# Change ONLY OUTPUT_PIN and PUB_IDENT when swapping modes.
BROKER_IP  = "172.20.10.8"
TOPIC      = "temp/pico"

# --- DEFAULT: SUBSCRIBER SETTINGS ---
# For SUBSCRIBER: OUTPUT_PIN = None, PUB_IDENT = "anything"
# For PUBLISHER:  OUTPUT_PIN = 0 (or another pin), PUB_IDENT = None
OUTPUT_PIN = None      # <-- change to 0 for publisher
PUB_IDENT  = "Sub1"    # <-- change to None for publisher
# =================================================


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Connected:", wlan.ifconfig())
    return wlan


# ---- Decide mode based on globals ----
def determine_mode():
    mode = None

    if BROKER_IP is not None and TOPIC is not None:
        # Subscriber: BROKER_IP, TOPIC, PUB_IDENT all non-None AND OUTPUT_PIN is None
        if PUB_IDENT is not None and OUTPUT_PIN is None:
            mode = "subscriber"
        # Publisher: BROKER_IP, TOPIC, OUTPUT_PIN all non-None AND PUB_IDENT is None
        elif OUTPUT_PIN is not None and PUB_IDENT is None:
            mode = "publisher"

    if mode is None:
        print("Configuration error: set either:")
        print("  SUBSCRIBER -> OUTPUT_PIN = None, PUB_IDENT = 'something'")
        print("  PUBLISHER  -> OUTPUT_PIN = <pin number>, PUB_IDENT = None")
        # Fail gracefully: do nothing but don't crash
        while True:
            time.sleep(1)

    print("Running in", mode, "mode")
    return mode


# ===== SUBSCRIBER SETUP =====
temps = {}  # {publisher_id: (temp, last_seen_timestamp)}

def sub_cb(topic, data):
    # Decode protobuf
    msg = sensor_upb2.SensordataMessage()
    msg.parse(data)

    pub_id = msg.publisher_id._value
    temp = msg.temprature._value
    now = time.time()

    print("Received from {}: {}°C".format(pub_id, temp))

    # Store latest reading from each publisher
    temps[pub_id] = (temp, now)

    # Drop entries older than 10 minutes
    cutoff = now - 600
    to_keep = {k: v for k, v in temps.items() if v[1] > cutoff}
    temps.clear()
    temps.update(to_keep)

    # Compute average and drive LED
    if temps:
        avg_temp = sum(v[0] for v in temps.values()) / len(temps)
        print("Average temperature: {:.2f}°C".format(avg_temp))

        if avg_temp > 25:
            led.value(1)
            print("LED ON (Avg Temp > 25°C)")
        else:
            led.value(0)
            print("LED OFF")


# ===== PUBLISHER SETUP =====
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

def read_temp():
    reading = sensor_temp.read_u16() * conversion_factor
    return 27 - (reading - 0.706) / 0.001721


# =================== MAIN ===================

connect_wifi()
mode = determine_mode()

# Common MQTT client
client_id = "pico_" + mode
client = MQTTClient(client_id, BROKER_IP)

if mode == "subscriber":
    # Use onboard LED pin 0 (or change if needed)
    led = machine.Pin(0, machine.Pin.OUT)

    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(TOPIC)
    print("Subscribed to topic:", TOPIC)

    while True:
        client.check_msg()   # handle incoming messages
        time.sleep(0.1)

elif mode == "publisher":
    client.connect()
    print("Publishing to topic:", TOPIC)

    while True:
        temp = round(read_temp(), 2)
        print("Publishing temperature:", temp)

        # Build protobuf message
        msg = sensor_upb2.SensordataMessage()
        msg.temprature._value = temp

        # Hard-coded publisher ID (change if you like)
        msg.publisher_id._value = "Pico1"

        t = time.localtime()
        time_msg = sensor_upb2.TimeMessage()
        time_msg.hour._value = t[3]
        time_msg.minute._value = t[4]
        time_msg.second._value = t[5]

        msg.timestamp._value = time_msg

        data = msg.serialize()
        client.publish(TOPIC, data)

        time.sleep(2)

