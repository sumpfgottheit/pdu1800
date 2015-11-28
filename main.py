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
from datastream import SimDataPacket


pygame.init()

# set up the window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, SCREEN_DEEP)

# Fill surface
surface = pygame.Surface(screen.get_size())
surface = surface.convert()
surface.fill(BLACK)

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

d = SimDataPacket
while running:
    #
    # Read from Network
    #
    if datastream.has_data_available:
        d = datastream.packet
        clear_dirty_rects()

        for widget in page.dynamic_widgets:
            widget.update(d)

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
#            print("Pos: %sx%s\n" % pygame.mouse.get_pos())
#            if textpos.collidepoint(pygame.mouse.get_pos()):
            running = False
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False

    screen.blit(surface, (0, 0))
    #print dirty_rects
    pygame.display.update(dirty_rects)

pygame.quit()
