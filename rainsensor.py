import time
import board
import digitalio

class RainSensor:
    def __init__(self, pin):
        self.sensor = digitalio.DigitalInOut(pin)
        self.sensor.direction = digitalio.Direction.INPUT

    def is_raining(self):
        return not self.sensor.value