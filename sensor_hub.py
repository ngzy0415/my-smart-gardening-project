import os
import time
import board
import digitalio
import analogio
import wifi
import socketpool
import adafruit_requests
import pyRTOS
from adafruit_motor import servo
import rfid_522
import servo_motor
import busio
import ssl
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
import adafruit_dht
import microcontroller
import simpleio
import stepper_motor

# UART setup for communication with sensor hub
uart = busio.UART(board.GP0, board.GP1, baudrate=9600)

# Constants
MOISTURE_THRESHOLD = 4
WATER_TEMP_THRESHOLD = 26
R = 10000  # ohm resistance value for LDR

# Get wifi and blynk token details from a settings.toml file
ssid = os.getenv("WIFI_SSID")
password = os.getenv("WIFI_PASSWORD")
blynkToken = os.getenv("blynk_auth_token")
telegrambot = os.getenv("botToken")

# Telegram API url.
API_URL = "https://api.telegram.org/bot" + telegrambot

# Wi-Fi Connection
print(f"Initializing...")
wifi.radio.connect(ssid, password)
print("connected!\n")
pool = socketpool.SocketPool(wifi.radio)
print("IP Address: {}".format(wifi.radio.ipv4_address))
print("Connecting to WiFi '{}' ...\n".format(ssid), end="")
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Blynk API Functions
def write(token, pin, value):
    api_url = f"https://blynk.cloud/external/api/update?token={token}&{pin}={value}"
    response = requests.get(api_url)
    if "200" in str(response):
        print("Value successfully updated")
    else:
        print("Could not find the device token or wrong pin format")

def read(token, pin):
    api_url = f"https://blynk.cloud/external/api/get?token={token}&{pin}"
    response = requests.get(api_url)
    return response.content.decode()

# Telegram Bot Functions
def init_bot():
    get_url = API_URL
    get_url += "/getMe"
    r = requests.get(get_url)
    return r.json()['ok']

first_read = True
update_id = 0

def read_message():
    global first_read
    global update_id
    
    get_url = API_URL
    get_url += "/getUpdates?limit=1&allowed_updates=[\"message\",\"callback_query\"]"
    if first_read == False:
        get_url += "&offset={}".format(update_id)

    r = requests.get(get_url)
    #print(r.json())
    
    try:
        update_id = r.json()['result'][0]['update_id']
        message = r.json()['result'][0]['message']['text']
        chat_id = r.json()['result'][0]['message']['chat']['id']

        #print("Update ID: {}".format(update_id))
        print("Chat ID: {}\tMessage: {}".format(chat_id, message))

        first_read = False
        update_id += 1
       
        return chat_id, message

    except (IndexError) as e:
        #print("No new message")
        return False, False

def send_message(chat_id, message):
    get_url = API_URL
    get_url += "/sendMessage?chat_id={}&text={}".format(chat_id, message)
    r = requests.get(get_url)
    #print(r.json())

# Initialize devices
rfid = rfid_522.RFID(board.GP18, board.GP19, board.GP20, board.GP21, board.GP22)
servo = servo_motor.ServoMotor(board.GP10)
led1 = digitalio.DigitalInOut(board.GP11)
led1.direction = digitalio.Direction.OUTPUT
stepper2 = stepper_motor.StepperMotor([board.GP12, board.GP13, board.GP14, board.GP15], 0.001)

# Initialize sensors
ldr1 = analogio.AnalogIn(board.GP28)
ldr2 = analogio.AnalogIn(board.GP27)
rain_sensor = digitalio.DigitalInOut(board.GP5)
rain_sensor.direction = digitalio.Direction.INPUT
moisture_sensor = analogio.AnalogIn(board.GP26)
ow_bus = OneWireBus(board.GP6)
water_temp_sensor = DS18X20(ow_bus, ow_bus.scan()[0])
dht22 = adafruit_dht.DHT22(board.GP16)

access_granted = False

# Functions to convert LDR reading to voltage and lux
def get_voltage(raw):
    return (raw * 3.3) / 65536

def rtolux(rawval):
    vout = get_voltage(rawval)
    if vout == 0 or (3.3 - vout) == 0:  # Avoid division by zero
        return float('inf')
    RLDR = (vout * R) / (3.3 - vout)
    lux = 500 / (RLDR / 1000)  # Conversion resistance to lumen
    return lux

# Function to convert moisture sensor reading to percentage
def get_moisture_percentage(raw):
    # Adjust these calibration values based on your sensor's actual readings in dry and wet conditions
    DRY_VALUE = 65535  # Raw value in dry condition (air)
    WET_VALUE = 20000  # Raw value in wet condition (water)
    if raw > DRY_VALUE:
        raw = DRY_VALUE
    elif raw < WET_VALUE:
        raw = WET_VALUE
    return 100 * (DRY_VALUE - raw) / (DRY_VALUE - WET_VALUE)

# pyRTOS Tasks
def rfid_task(self):
    global access_granted
    while True:
        if rfid.check_access():
            access_granted = not access_granted
            if access_granted:
                uart.write(b'GRANT\n')
                servo.move_to(0)
                led1.value = True
                print("Access granted: Servo to 0, LED1 on")
                
                
                
            else:
                uart.write(b'REVOKE\n')
                servo.move_to(180)
                led1.value = False
                print("Access revoked: Servo to 180, LED1 off")
                
        yield [pyRTOS.timeout(0.01)]
                
                
    

def display_sensor_values_task(self):
    while True:
        rooftop_status = read(blynkToken, "V4")
        ldr1_lux = rtolux(ldr1.value)
        print(f"LDR1 Lux: {ldr1_lux:.2f} lux")
        if ldr1_lux > 700 and rooftop_status == "0":
            uart.write(b'L_1_A\n')
            write(blynkToken, "V4", "1")
            stepper2.step_motor(1000, 'backward')
            
        ldr2_lux = rtolux(ldr2.value)
        print(f"LDR2 Lux: {ldr2_lux:.2f} lux")
        if ldr2_lux < 40 and rooftop_status == "1":
            uart.write(b'L_2_A\n')
            write(blynkToken, "V4", "0")
            stepper2.step_motor(1000, 'forward')

        rain_status = 'RAIN' if not rain_sensor.value else 'NO_RAIN'
        print(f"Rain Sensor Value: {rain_status}")
        if rain_status == 'RAIN' and rooftop_status == "1":
            uart.write(b'R_A\n')
            stepper2.step_motor(1000, 'forward')
            write(blynkToken, "V4", "0")

        moisture_value = get_moisture_percentage(moisture_sensor.value)
        print(f"Moisture Sensor Value: {moisture_value:.2f}%")
        if moisture_value < MOISTURE_THRESHOLD:
            uart.write(b'M_A\n')

        water_temp_value = water_temp_sensor.temperature
        print(f"Waterproof Temperature Sensor Value: {water_temp_value:.2f}C")
        if water_temp_value > WATER_TEMP_THRESHOLD:
            uart.write(b'W_T_A\n')

        try:
            dht_temp = dht22.temperature
            dht_humidity = dht22.humidity
            print(f"DHT22 Temperature: {dht_temp:.2f}C, Humidity: {dht_humidity:.2f}%")
            if dht_temp > 26 and access_granted:
                uart.write(b'D_M_F\n')
                
            elif dht_temp < 23 and access_granted:
                uart.write(b'D_M_S\n')
                
        except RuntimeError as e:
            print(e)

        yield [pyRTOS.timeout(2)]

def blynk_task(self):
    global stepper_position  # Ensure this variable is accessible in the function
    while True:
        # Upload data to Blynk
        moisture_value = get_moisture_percentage(moisture_sensor.value)
        write(blynkToken, "V1", moisture_value)

        water_temp_value = water_temp_sensor.temperature
        write(blynkToken, "V2", water_temp_value)
        
        if access_granted:
            dht_temp = dht22.temperature
            write(blynkToken, "V0", dht_temp)

            dht_humidity = dht22.humidity
            write(blynkToken, "V3", dht_humidity)

        yield [pyRTOS.timeout(3)]

def telegram_bot_task(self):
    while True:
        rooftop_status = read(blynkToken, "V4")
        chat_id, message_in = read_message()
        if message_in == "/start":
            send_message(chat_id,"Welcome to SMART GARDEN!")
            send_message(chat_id,"Choose from one of the following options:")
            send_message(chat_id,"1) Condition:  /STATUS")
            send_message(chat_id,"2) Pump water: /WATER_PUMP")
            send_message(chat_id,"3) Open roof:  /ROOF_OPEN")
            send_message(chat_id,"4) Close roof: /ROOF_CLOSE")
            send_message(chat_id,"5) Open door:  /DOOR_OPEN")
            send_message(chat_id,"6) Close door: /DOOR_CLOSE")
           
        
    
        elif message_in == "/STATUS":
            rain_status = 'RAIN' if not rain_sensor.value else 'NO_RAIN'
            if rain_status == 'RAIN':
                send_message(chat_id, "Rainy Day!!!")
            else:
                send_message(chat_id, "Sunny Day!")

            moisture_value = get_moisture_percentage(moisture_sensor.value)
            if moisture_value > 5:
                send_message(chat_id, "The soil is in a good moisture")
            elif moisture_value <5:
                send_message(chat_id, "The soil is dry!!!!")
                
        elif message_in == "/WATER_PUMP":
            uart.write(b'W_P_A\n')
        
        elif message_in == "/ROOF_OPEN" and rooftop_status == "0":
            uart.write(b'R_O\n')
            stepper2.step_motor(1000, 'backward')
            write(blynkToken, "V4", "1")
        
        elif message_in == "/ROOF_CLOSE" and rooftop_status == "1":
            uart.write(b'R_C\n')
            stepper2.step_motor(1000, 'forward')
            write(blynkToken, "V4", "0")
        
        elif message_in == "/DOOR_OPEN":
            servo.move_to(0)
        
        elif message_in == "/DOOR_CLOSE":
            servo.move_to(180)
                     
        yield [pyRTOS.timeout(5)]  # Check messages every 2 seconds

# Adding tasks to pyRTOS
pyRTOS.add_task(pyRTOS.Task(rfid_task, name="RFID Task"))
pyRTOS.add_task(pyRTOS.Task(display_sensor_values_task, name="Display Sensor Values Task"))
pyRTOS.add_task(pyRTOS.Task(blynk_task, name="Blynk Task"))
pyRTOS.add_task(pyRTOS.Task(telegram_bot_task, name="Telegram Bot Task"))


pyRTOS.start()

print("Starting Smart Gardening System...")

# Note: The main loop and task executions are handled by pyRTOS