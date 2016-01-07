#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on touchv6, Texy 5/12/13

import pygame, sys, os, time
import pickle
from util import get_lan_ip, update_dict, find_updated_keys
import socket
import select
from pygame.locals import *
from widgets import *
from config import *
import sys
from telemetry_reader import ACTelemetryReader
from datastream import PDU1800DataStream, PDU1800DatasStreamRepeater
from copy import copy
import platform

#pygame.init()
pygame.font.init()
pygame.display.init()

# set up the window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, SCREEN_DEEP)

# Fill surface
surface = pygame.Surface(screen.get_size())
surface = surface.convert()
surface.fill(BACKGROUND_COLOR)

#fill_background(surface)

#
# Create Pages
#
create_pages(surface)
current_page_index = 0
page = pages[current_page_index]
for widget in page.widgets:
    widget.draw()


screen.blit(surface, (0, 0))
pygame.display.flip()
running = True
show_overlay = False
overlay = Overlay(surface)
telemetry_reader = None

if platform.machine() == 'armv7l' and platform.dist()[0] == 'debian':
    datastream = PDU1800DataStream(ip=IP, port=UDP_PORT)
else:
    #datastream = PDU1800DataStream(ip=IP, port=UDP_PORT)
    datastream = PDU1800DatasStreamRepeater()

try:
    while running:
        #
        # Read from Network
        #
        if datastream.has_data_available:
            d = datastream.packet
            clear_dirty_rects()
    
            for widget in page.dynamic_widgets:
                widget.update(d)
    
        if show_overlay:
            overlay.display()
    
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                pygame.mouse.get_rel()
                if show_overlay:
                    if overlay.quit_pressed(pos):
                        running = False
                    elif overlay.shutdown_pressed(pos):
                        if platform.machine() == 'armv7l' and platform.dist()[0] == 'debian':
                            os.system('/sbin/shutdown -h now')
                    elif overlay.restart_pressed(pos):
                        datastream.quit()
                        datastream = PDU1800DataStream(ip=IP, port=UDP_PORT)
                        for widget in page.dynamic_widgets:
                            try:
                                widget.initialize()
                            except AttributeError:
                                pass
                    show_overlay = False
                    page.draw_all()
                else:
                    show_overlay = True
                pygame.event.clear()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False
    
        screen.blit(surface, (0, 0))
        pygame.display.update(dirty_rects)
except KeyboardInterrupt:
    pass
datastream.quit()
pygame.quit()
