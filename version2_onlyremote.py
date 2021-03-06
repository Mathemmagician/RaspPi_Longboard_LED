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

def forward_beat(w=5, start=FML, delta=2):
    'sends beats from the given point to opposite'
    try:
        pixels.fill(RED)
        for k in range(forward_beat.state, halfnum_pixels, 3 * w):
            for i in range(w):
                pixels[(start+1 + i + k) % num_pixels] = GREEN
                pixels[(start   - i - k) % num_pixels] = GREEN

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

def random_color_update(color):
    colors = [max(min(component + randint(-5,5), 255), 0) for component in color]
    return tuple(colors)

def solid():
    try:
        pixels.fill(solid.color)
        solid.color = random_color_update(solid.color)
    except AttributeError:
        solid.color = (randint(0, 255), randint(0, 255), randint(0, 255))

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

        rainbow.time = (rainbow.time + 1) % 360
    except AttributeError:
        rainbow.time = 0


def callback(hash):
    'This function is called when IR remote sends a signal'
    global boardfunc, funckwargs
    if hash not in hash2key:
        print(f'Unrecognized hash: {hash}')
    else:
        key = hash2key[hash]
        print(f'{hash2key[hash]} was pressed')
        if key in ['KEY_4', 'KEY_5', 'KEY_6']:
            record_data(key)
        elif key in key_functionality:
            boardfunc, funckwargs = key_functionality[key]

def record_data(key):
    if key == 'KEY_4': direction="left "
    if key == 'KEY_5': direction="straight"
    if key == 'KEY_6': direction='right'

    gyro_data = g.get_xyz_rotation_radians()
    with open("trip.txt", "a") as myfile:
        myfile.write(f"{direction} {gyro_data['x']} {gyro_data['y']} {gyro_data['z']}\n")


pixel_pin = board.D18  # NeoPixels connected to BCM 18 pin
num_pixels = 142       # Total number of pixels around the board
halfnum_pixels = num_pixels // 2
ORDER = neopixel.GRB

# Instantiate Remote controller
pi = pigpio.pi()
ir = ir_hasher.hasher(pi, 17, callback, 5)

key_functionality = {
        'UP':       (forward_beat, {}),
        'DOWN':     (forward_beat, {'start': BML}),
        'LEFT':     (forward_beat, {'start': 24}),
        'RIGHT':    (forward_beat, {'start': 95}),
        'KEY_7':    (turning, {'delta': -3}),
        'KEY_9':    (turning, {'delta': +3}),
        'KEY_1':    (rainbow, {}),
        'KEY_2':    (disco, {}),
        'KEY_3':    (forward_pulse, {})
}

boardfunc = forward_pulse
funckwargs = {}
main_color = (255, 0, 0)

# WHEN GOING OUTSIDE INCREASE BRIGHTNESS FOR COOLER EFFECT
with neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER) as pixels:
    try:
        while True:
            gyro_data = g.get_xyz_rotation_radians()
            
            if funckwargs: # makes sure kwargs list isn't empty
                boardfunc(**funckwargs)
            else:
                boardfunc()

            pixels.show()
            main_color = random_color_update(main_color)

    except KeyboardInterrupt:
        print('Keyboard Interrupted. Cleaning Up')
        pi.stop()

