import time
import board
import digitalio

class StepperMotor:
    def __init__(self, pins, delay=0.01):
        self.pins = [digitalio.DigitalInOut(pin) for pin in pins]
        for pin in self.pins:
            pin.direction = digitalio.Direction.OUTPUT
        self.step_sequence = [
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1]
        ]
        self.step_index = 0
        self.delay = delay

    def step_motor(self, steps, direction):
        step_count = len(self.step_sequence)
        if direction == 'forward':
            for _ in range(steps):
                for step in self.step_sequence:
                    self.set_step(*step)
                    time.sleep(self.delay)
        elif direction == 'backward':
            for _ in range(steps):
                for step in reversed(self.step_sequence):
                    self.set_step(*step)
                    time.sleep(self.delay)
        # Turn off all coils
        self.set_step(0, 0, 0, 0)

    def set_step(self, w1, w2, w3, w4):
        self.pins[0].value = w1
        self.pins[1].value = w2
        self.pins[2].value = w3
        self.pins[3].value = w4
