#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
#
# BSD 3-Clause License
# Copyright (c) 2020, Thomas Breitbach
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

import math
import time
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
from . import radar_opts

# global constants
LARGE = 20           # size of height indications of aircraft
SMALL = 12      # size of information indications on top and bottom
AIRCRAFT_SIZE = 3        # size of aircraft arrow
MINIMAL_CIRCLE = 10     # minimal size of mode-s circle
# end definitions

# device properties
sizex = 0
sizey = 0
zerox = 0
zeroy = 0
largefont = ""
smallfont = ""
webfont = ""
device = None
image = None
# end device globals


def posn(angle, arm_length):
    dx = round(math.cos(math.radians(angle)) * arm_length)
    dy = round(math.sin(math.radians(angle)) * arm_length)
    return dx, dy


def make_font(name, size):
    font_path = str(Path(__file__).resolve().parent.joinpath('fonts', name))
    return ImageFont.truetype(font_path, size)


def init():
    global sizex
    global sizey
    global zerox
    global zeroy
    global largefont
    global smallfont
    global webfont
    global device
    global image

    config_path = str(Path(__file__).resolve().parent.joinpath('ssd1351.conf'))
    device = radar_opts.get_device(['-f', config_path])
    image = Image.new(device.mode, device.size)
    draw = ImageDraw.Draw(image)
    sizex = device.width
    sizey = device.height
    zerox = sizex / 2
    zeroy = sizey / 2
    device.contrast(255)  # set full contrast
    largefont = make_font("miscfs_.ttf", LARGE)               # font for height indications
    smallfont = make_font("miscfs_.ttf", SMALL)     # font for information indications
    webfont = make_font("fontawesome-webfont.ttf", SMALL)   # font for Bluetooth indications
    display_refresh = 0.3    # oled has no busy flag, so take this as update value
    return draw, sizex, zerox, zeroy, display_refresh


def cleanup():
    device.cleanup()


def centered_text(draw, y, text, font, fill):
    ts = draw.textsize(text, font)
    draw.text((zerox - ts[0] / 2, y), text, font=font, fill=fill)


def display():
    device.display(image)


def is_busy():
    # oled is never busy, no refresh
    return False

def next_arcposition(old_arcposition):
    # defines next position of height indicator on circle. Can be used to exclude several ranges or
    # be used to define the next angle on the circle
    return (old_arcposition + 210) % 360

def clear(draw):
    draw.rectangle((0, 0, sizex - 1, sizey - 1), fill="black")


def startup(draw, target_ip, seconds):
    logopath = str(Path(__file__).resolve().parent.joinpath('stratux-logo-64x64.bmp'))
    logo = Image.open(logopath)
    draw.rectangle(((0, 0), (sizex, 64)), fill="blue")
    draw.bitmap((zerox-32, 0), logo, fill="white")
    centered_text(draw, 64, "Oled-Radar", largefont, fill="white")
    centered_text(draw, 64 + LARGE, "Version 1.0", smallfont, fill="white")
    centered_text(draw, sizey - 2 * SMALL, "Connecting to", smallfont, fill="white")
    centered_text(draw, sizey - SMALL, target_ip, smallfont, fill="white")
    display()
    time.sleep(seconds)


def aircraft(draw, x, y, direction, height):
    p1 = posn(270 + direction, 2 * AIRCRAFT_SIZE)
    p2 = posn(270 + direction + 150, 4 * AIRCRAFT_SIZE)
    p3 = posn(270 + direction + 180, 2 * AIRCRAFT_SIZE)
    p4 = posn(270 + direction + 210, 4 * AIRCRAFT_SIZE)

    draw.polygon(((x + p1[0], y + p1[1]), (x + p2[0], y + p2[1]), (x + p3[0], y + p3[1]), (x + p4[0], y + p4[1])),
                 fill="red", outline="white")
    if height >= 0:
        signchar = "+"
    else:
        signchar = "-"
    t = signchar + str(abs(height))
    tsize = draw.textsize(t, largefont)
    if tsize[0] + x + 4 * AIRCRAFT_SIZE - 2 > sizex:
        # would draw text outside, move to the left
        tposition = (x - 4 * AIRCRAFT_SIZE - tsize[0], int(y - tsize[1] / 2))
    else:
        tposition = (x + 4 * AIRCRAFT_SIZE + 1, int(y - tsize[1] / 2))
    draw.rectangle((tposition, (tposition[0] + tsize[0], tposition[1] + tsize[1])), fill="black")
    draw.text(tposition, t, font=largefont, fill="white")


def modesaircraft(draw, radius, height, arcposition):
    if radius < MINIMAL_CIRCLE:
        radius = MINIMAL_CIRCLE
    draw.ellipse((64-radius, 64-radius, 64+radius, 64+radius), width=1, outline="white")
    arctext = posn(arcposition, radius)
    if height > 0:
        signchar = "+"
    else:
        signchar = "-"
    t = signchar+str(abs(height))
    tsize = draw.textsize(t, largefont)
    tposition = (64+arctext[0]-tsize[0]/2, 64+arctext[1]-tsize[1]/2)
    draw.rectangle((tposition, (tposition[0]+tsize[0], tposition[1]+tsize[1])), fill="black")
    draw.text(tposition, t, font=largefont, fill="white")


def situation(draw, connected, gpsconnected, ownalt, course, range, altdifference, bt_devices=0):
    draw.ellipse((0, 0, sizex-1, sizey-1), outline="blue")
    draw.ellipse((sizex/4, sizey/4, zerox + sizex/4, zeroy + sizey/4), outline="blue")
    draw.ellipse((zerox-2, zeroy-2, zerox+2, zeroy+2), outline="blue")
    draw.text((0, sizey - SMALL), "FL" + str(round(ownalt/100)), font=smallfont, fill="orange")

    draw.text((0, 0), str(range), font=smallfont, fill="orange")
    draw.text((0, SMALL), "nm", font=smallfont, fill="orange")

    if altdifference >= 10000:
        t = str(int(altdifference/1000))+"k"
    else:
        t = str(altdifference)
    textsize = draw.textsize(t, smallfont)
    draw.text((sizex - textsize[0], 0), t, font=smallfont, fill="orange", align="right")

    text = "ft"
    textsize = draw.textsize(text, smallfont)
    draw.text((sizex - textsize[0], SMALL), text, font=smallfont, fill="orange", align="right")

    text = str(course) + '°'
    textsize = draw.textsize(text, smallfont)
    draw.text((sizex - textsize[0], sizey - textsize[1]), text, font=smallfont, fill="orange", align="right")

    if bt_devices > 0:
        text = '\uf293'   # bluetooth symbol + no
        textsize = draw.textsize(text, webfont)
        draw.text((sizex - textsize[0], sizey - 2*SMALL), text, font=webfont, fill="blue", align="right")

    if not gpsconnected:
        centered_text(draw, 0, "No GPS", smallfont, fill="red")
    if not connected:
        centered_text(draw, zeroy, "No Connection!", smallfont, fill="red")