import socket
import pickle
from math import sin, cos, pi, radians
from time import sleep
from random import randint

from gyroscope import Gyroscope

import board
import neopixel

g = Gyroscope()

FML = 59
FMR = FML + 1
BMR = 133
BML = BMR + 1
''' LONGBOARD
BACK. X is where setup is located

     BMR BML
       ___
      |   |
     _| x |_
    |       |
    |       |
    |       |
    |       |
    |       |
    |       |
    |_     _|
      |   |
      |___|
     FMR FML
'''

shift = 0
ftime = 0
def turning(w, color=(0,150,0)):
    # w is width 
    global pixels, shift
    pixels.fill((0, 0, 0))
    for i in range(w):
        for j in range((i+shift)%(4*w), num_pixels, 4*w):
            pixels[j] = color


def rainbow(t, maxb=180):
    ''' returns (r,g,b) at time t. 
        t goes from 0 to 360
        maxb is max brightness. set to 120 for power reasons'''
    t = (t % 360)
    rt = radians(t) * 3/2
    if t <= 120: 
        r = (cos(rt)+1) / 2
    elif t <= 240:
        r = 0
    else:
        r = (-cos(rt) + 1)/2
    r = int(maxb * r)

    g = int(maxb * (-cos(rt)+1)/2) if (t <= 240) else 0
    b = 0 if (t <= 120) else int(maxb * (cos(rt)+1)/2)
    return (r, g, b)

def forward(w):
    global pixels,T 
    pixels.fill((0, 0, 20))
    for i in range(w):
        pixels[(FML+i+T)%num_pixels] = (0, 50, 0)
        pixels[(FMR-i-T)%num_pixels] = (0, 50, 0)


yhist = [0, 0, 0, 0, 0]

# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18
num_pixels = 142
ORDER = neopixel.GRB

T = 0
action = 'idle'

with neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, 
        auto_write=False, pixel_order=ORDER) as pixels:
    while True:
        data = g.get_xyz_rotation_radians()
        yhist = yhist[1:] + [data['y']]
        avey = sum(yhist) / len(yhist)
        if avey > 0.15:
            if action != 'turn':
                action = 'turn'
                color = (randint(0, 255), randint(0, 255), randint(0, 255))
            turning(3, color)
            shift += 2
        elif avey < -0.05:
            if action != 'turn':
                action = 'turn'
                color = (randint(100, 255), randint(100, 255), randint(100, 255))
            turning(3, color)
            shift -= 2
        else:
            if T < 400:
                forward(10)
                action = 'idle'
            elif T < 500:
                pixels.fill((255, 0, 0))
            elif T < 540:
                pixels.fill((255, 255, 0))
            elif T < 565:
                pixels.fill((0, 255, 0))
            else:
                action = 'forward'
                pixels.fill((0,0,0))
                for i in range(FMR+(T%5), BMR,5):
                    pixels[i] = rainbow(T)
                    pixels[FML-(i-FMR)%num_pixels] = rainbow(T)
        pixels.show()
        T += 1 



