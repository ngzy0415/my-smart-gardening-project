import board
import digitalio
import time

class DCMotor:
    def __init__(self, in1, in2):
        self.in1 = digitalio.DigitalInOut(in1)
        self.in1.direction = digitalio.Direction.OUTPUT
        self.in2 = digitalio.DigitalInOut(in2)
        self.in2.direction = digitalio.Direction.OUTPUT

    def move_forward(self):
        self.in1.value = True
        self.in2.value = False

    def stop(self):
        self.in1.value = False
        self.in2.value = False
