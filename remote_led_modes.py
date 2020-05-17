import time
from random import randint
from math import sin, cos, pi, radians
import colorsys

from gyroscope import Gyroscope

import board
import neopixel     #LEDs
from constants import *    # Colors, FML, FMR, BMR, BML

import pigpio
import ir_hasher    #Remote
from utils import hash2key # Remote Signal Map

g = Gyroscope()

''' LONGBOARD

  130 BMR BML 131
       ___
   []-|   |-[]
     _| x |_
    |  BACK |
    |       |     x  is where setup is located
    |       |
    |       |
    |       |
    |       |
    |_FRONT_|
      |   |
   []-|___|-[]
  60 FMR FML 59
'''

def forward_pulse(w=20, start=FML, delta=4):
    'sends pulses from the given point to opposite'
    try:
        pixels.fill(BLUE)
        for i in range(w):
            pixels[(start+1 + i + forward_pulse.state) % num_pixels] = GREEN
            pixels[(start   - i - forward_pulse.state) % num_pixels] = GREEN
        forward_pulse.state = (forward_pulse.state + delta) % (halfnum_pixels-w//2)
    except AttributeError:
        forward_pulse.state = 0

def forward_beat(w=5, start=FML, delta=1):
    'sends beats from the given point to opposite'
    try:
        pixels.fill((255, 255, 0))
        for k in range(forward_beat.state, halfnum_pixels, 3 * w):
            for i in range(w):
                pixels[(start+1 + i + k) % num_pixels] = (0, 50, 100)
                pixels[(start   - i - k) % num_pixels] = (0, 50, 100) 

        forward_beat.state = (forward_beat.state + delta) % (3 * w)
    except AttributeError:
        forward_beat.state = 0

def turning(w=4, delta=3, color=(128, 0, 128)):
    'right -> postivie delta, left -> negative delta'
    try:
        pixels.fill((200, 40, 0))
        for i in range(w):
            for j in range((i + turning.state) % (4 * w), num_pixels, 4 * w):
                pixels[j] = color
        turning.state += delta
    except AttributeError:
        turning.state = 0

def random_bright_color():
    return (randint(35, 255), randint(35, 255), randint(35, 255))

def disco(w=5):
    try:
        pixels.fill(BLACK)
        for i in range(disco.start, num_pixels, w):
            pixels[i] = disco.color

        disco.color = random_bright_color()
        disco.counter += 1
        disco.start = (disco.start + disco.delta) % w
        if disco.counter == 15:
            disco.counter = 0
            disco.delta = -disco.delta
    except AttributeError:
        disco.color = random_bright_color()
        disco.start = 0
        disco.counter = 0
        disco.delta = 1

def hsv2rgb(h,s,v):
    'return non-normalized hsv to rgb conversion'
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

def rainbow():
    'Smart people use HSV for ranbow'
    try:
        color = hsv2rgb(rainbow.time/360, 1, 1)
        pixels.fill(color)

        rainbow.time = (rainbow.time + 2) % 360
    except AttributeError:
        rainbow.time = 0


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


pixel_pin = board.D18  # NeoPixels connected to BCM 18 pin
num_pixels = 142       # Total number of pixels around the board
halfnum_pixels = num_pixels // 2
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

# WHEN GOING OUTSIDE INCREASE BRIGHTNESS FOR COOLER EFFECT
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

