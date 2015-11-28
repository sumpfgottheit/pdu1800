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

d = SimDataPacket
while running:
    #
    # Read from Network
    #
    if datastream.has_data_available:
        d = datastream.packet   # type: SimDataPacket
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
            if show_overlay:
                if overlay.quit_pressed(pygame.mouse.get_pos()):
                    running = False
                show_overlay = False
                page.draw_all()
            else:
                show_overlay = True
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False

    screen.blit(surface, (0, 0))
    pygame.display.update(dirty_rects)

pygame.quit()
