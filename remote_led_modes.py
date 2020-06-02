import time
from random import randint
from math import sin, cos, pi, radians
import colorsys

from gyroscope import Gyroscope

import board
import neopixel         # LEDs
from constants import * # Colors, FML, FMR, BMR, BML

import pigpio
import ir_hasher            # Remote Controller
from utils import hash2key  # Remote Signal Map

from visuals import *  # All of the visual patterns


def callback(hash):
    'This function is called when IR remote sends a signal'
    global boardfunc, funckwargs, tripfile, recording
    if hash not in hash2key:
        print(f'Unrecognized hash: {hash}')
    else:
        key = hash2key[hash]
        print(f'{hash2key[hash]} was pressed')
        if (key in ['LEFT', 'UP', 'RIGHT']) and recording:
            tripfile.write(f'{key}\n')
        if key == 'KEY_STAR':
            recording = True
        if key == 'KEY_HASHTAG':
            recording = False
        if key in key_functionality:
            boardfunc, funckwargs = key_functionality[key]


g = Gyroscope()

num_pixels = 142       # Total number of pixels around the board
halfnum_pixels = num_pixels // 2
pixel_pin = board.D18  # NeoPixels connected to BCM 18 pin
ORDER = neopixel.GRB

# Instantiate Remote controller
pi = pigpio.pi()
ir = ir_hasher.hasher(pi, 17, callback, 5)

key_functionality = {
        'UP':       (forward_pulse, {}),
        'DOWN':     (forward_pulse, {'start': BML}),
        'LEFT':     (forward_pulse, {'start': 24}),
        'RIGHT':    (forward_pulse, {'start': 95}),
        'KEY_7':    (turning, {'delta': -3}),
        'KEY_9':    (turning, {'delta': +3}),
        'KEY_1':    (rainbow, {}),
        'KEY_2':    (disco, {}),
        'KEY_3':    (forward_beat, {})
}

boardfunc = forward_pulse
funckwargs = {}

FPS = 30 # Approximately 30 cycles per second
RPS = FPS // 10 # Record data 10 times per second
recording = False


# WHEN GOING OUTSIDE INCREASE brightness FOR COOLER EFFECT
with neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER) as pixels:

    tripfile = open('trip.txt', 'a')

    try:
        t = 0
        c = 0
        stime = time.time()
        while True:
            gyro_data = g.get_xyz_rotation_radians()

            if recording:   
                t += 1
                if t > RPS: # 10 times per second
                    tripfile.write(f"{gyro_data['x']} {gyro_data['y']} {gyro_data['z']}\n")
                    t = 0
                    c += 1
            
            if funckwargs: # makes sure kwargs list isn't empty
                boardfunc(**funckwargs)
            else:
                boardfunc()

            pixels.show()

    except KeyboardInterrupt:
        print('Keyboard Interrupted. Cleaning Up')
        pi.stop()
    finally:
        seconds = time.time() - stime
        print(f'recorded {c} times in {seconds} seconds')
        tripfile.close()

