import os
print("running 'sudo pigpiod'...", end='')
os.system("sudo pigpiod")
print("successful")

import time
from datetime import datetime
from random import randint
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

def turning(w=4, delta=3, color=(200, 40, 0)):
    'right -> postivie delta, left -> negative delta'
    try:
        pixels.fill((128, 0, 128))
        for i in range(w):
            for j in range((i + turning.state) % (4 * w), num_pixels, 4 * w):
                pixels[j] = color
        turning.state += delta
    except AttributeError:
        turning.state = 0

def disco(w=7):
    try:
        if disco.counter % FPS > FPS // 2:
            #pixels.fill(disco.colors[disco.counter % 4])
            pixels.fill(disco.color)
        else:
            pixels.fill(disco.bgcolor)
            disco.color = disco.colors[randint(0, 2)]

        disco.counter += 1
    except AttributeError:
        disco.colors = [(128, 0, 128), (128, 128, 0), (80, 100, 115)]
        disco.bgcolor =  (1, 2, 3)
        disco.counter = 0

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
    global boardfunc, funckwargs, tripfile, recording, EXITSYSTEM
    if hash not in hash2key:
        print(f'Unrecognized hash: {hash}')
    else:
        key = hash2key[hash]
        print(f'{hash2key[hash]} was pressed')
        
        # Data Recording
        if (key in ['LEFT', 'UP', 'RIGHT']) and recording:
            tripfile.write(f'{key}\n')
        if key == 'KEY_STAR':
            recording = True
        if key == 'KEY_HASHTAG':
            recording = False
        # Run Key Associated Function
        if key in key_functionality:
            boardfunc, funckwargs = key_functionality[key]
        # Exit mode
        if key == 'KEY_0':
            EXITSYSTEM = True



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

        'KEY_1':    (rainbow, {}),
        'KEY_2':    (disco, {}),
        'KEY_3':    (forward_beat, {}),

        'KEY_7':    (turning, {'delta': -1}),
        'KEY_8':    (turning, {'delta':  0}),
        'KEY_9':    (turning, {'delta': +1})
}

boardfunc = forward_pulse
funckwargs = {}

FPS = 30 # Approximately 30 cycles per second
RPS = FPS // 10 # Record data 10 times per second
recording = True
EXITSYSTEM = False

# WHEN GOING OUTSIDE INCREASE BRIGHTNESS FOR COOLER EFFECT
with neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER) as pixels:

    #now = datetime.now()
    #dt_string = now.strftime("%d-%b-%y_%H-%M-%S")
    dt_string="May16"
    tripfile = open(f'trip_{dt_string}.txt', 'a')

    try:
        t = 0
        c = 0
        stime = time.time()
        while True:

            if EXITSYSTEM: # if KEY_0
                raise KeyboardInterrupt

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
    except Exception as e:
        print(e)
        with open("ERRORLOG.txt", "w") as errorfile:
            errorfile.write(f'{type(e)}\n')
            errorfile.write(f'{e.args}\n')
            errorfile.write(e)
    finally:
        seconds = time.time() - stime
        print(f'recorded {c} times in {seconds} seconds')
        tripfile.close()

