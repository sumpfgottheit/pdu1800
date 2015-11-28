__author__ = 'Florian'

import pygame
from pygame import Rect
from pygame.font import Font
from config import *
from constants import *
from util import get_lan_ip, get_interface_ip

dirty_rects = []
widgets = {}
pages = []

def clear_dirty_rects():
    global dirty_rects
    del dirty_rects[:]

class Widget(object):
    def __init__(self, surface, x, y, w, h, fill_background=False, draw_borders=True):
        self.surface = surface
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = Rect(self.x, self.y, self.w, self.h)
        self.background_color = BACKGROUND_COLOR
        self.border_color = FOREGROUND_COLOR
        self.fill_background = fill_background
        self.draw_borders = draw_borders

    def draw(self):
        if self.fill_background and not self.draw_borders:
            pygame.draw.rect(self.surface, self.background_color, self.rect, 0)
        elif self.fill_background and self.draw_borders:
            pygame.draw.rect(self.surface, self.background_color, self.rect, 0)
            pygame.draw.rect(self.surface, self.border_color, self.rect, 1)
        elif not self.fill_background and self.draw_borders:
            pygame.draw.rect(self.surface, self.border_color, self.rect, 1)

    @property
    def xx(self):
        return self.x + self.w

    @property
    def yy(self):
        return self.y + self.h

    def add_to_dirty_rects(self):
        global dirty_rects
        dirty_rects.append(self.rect)

class TextWidget(Widget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(TextWidget, self).__init__(surface, x, y, w, h)
        self.value = ""
        self._fontsize = fontsize if fontsize else self.find_font_size()
        self.font = Font(FONT, self._fontsize)
        self.background_color = BACKGROUND_COLOR
        self.font_color = FOREGROUND_COLOR
        self.fill_background = True
        self.align = align
        self.valign = valign
        self.listen = None

    @property
    def fontsize(self):
        return self._fontsize

    @fontsize.setter
    def fontsize(self, value):
        self._fontsize = value
        self.font = Font(FONT, value)

    def update(self, value):
        if self.listen is not None:     # listen == GEAR -> value = d[GEAR]
            value = getattr(value, self.listen)
        if value != self.value:
            self.value = value
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

    def draw(self):
        super(TextWidget, self).draw()
        fontsurface = self.font.render(str(self.value), True, (self.font_color))
        fontrect = fontsurface.get_rect()
        if self.align == ALIGN_CENTER:
            fontrect.centerx = self.rect.centerx
        elif self.align == ALIGN_LEFT:
            fontrect.x = self.rect.x
        elif self.align == ALIGN_RIGHT:
            fontrect.right = self.rect.right
        if self.valign == VALIGN_CENTER:
            fontrect.centery = self.rect.centery
        elif self.valign == VALIGN_TOP:
            fontrect.top = self.rect.top
        elif self.valign == VALIGN_BOTTOM:
            fontrect.bottom = self.rect.bottom

        return self.surface.blit(fontsurface, fontrect)

    def find_font_size(self):
        size = 100
        while size >= 1:
            f = Font(FONT, size)
            w, h = f.size('8')
            if w < self.w and h < self.h:
                return size
            size = size -1
        return size

class LabelWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, value, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(LabelWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign)
        self.value = value

class GearNumberWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(GearNumberWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign)
        self.listen = GEAR

    def update(self, value):
        value = getattr(value, self.listen)
        if value == 0:
            value = 'N'
        elif value == -1:
            value = 'R'
        if value != self.value:
            self.value = value
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False


class RPMWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(RPMWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign)
        self.listen = RPM

class SpeedWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(SpeedWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign)
        self.listen = SPEED

    def update(self, value):
        value = getattr(value, self.listen)
        value = int(round(value))
        if value != self.value:
            self.value = value
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class RPMPercentWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER):
        super(RPMPercentWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign)
        self.listen = RPM
        self.value = 0

    def update(self, value):
        percent = int(round(float(value.rpm) / value.max_rpm, 2) * 100)
        if percent != self.value:
            self.value = percent
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class RPMBarTile(Widget):
    def __init__(self, surface, x, y, w, h, color):
        super(RPMBarTile, self).__init__(surface, x, y, w, h)
        self.draw_borders = False
        self.fill_background = False
        self.color = color
        self.is_shown = False

    def show(self):
        if not self.is_shown:
            self.is_shown = True
            self.draw_borders = True
            self.fill_background = True
            self.background_color = self.color
            self.add_to_dirty_rects()
            self.draw()

    def hide(self):
        if self.is_shown:
            self.is_shown = False
            self.draw_borders = True
            self.fill_background = True
            self.background_color = BACKGROUND_COLOR
            self.add_to_dirty_rects()
            self.draw()


class RPMBarWidget(Widget):
    NUM_TILES = 20

    def __init__(self, surface, x, y, w, h):
        super(RPMBarWidget, self).__init__(surface, x, y, w, h)
        self.listen = True
        self.percent = 0
        self.tiles = [RPMBarTile(surface, x=(SCREEN_WIDTH / self.NUM_TILES) * i + 1, y=self.y, w=(SCREEN_WIDTH/self.NUM_TILES+1), h=self.h, color=self.get_color(i)) for i in range(self.NUM_TILES)]
        self.tiles_shown = [False] * self.NUM_TILES
        self.num_tiles_shown = -1

    def get_color(self, i):
        if i <= self.NUM_TILES-9:
            return GREEN
        elif i <= self.NUM_TILES-5:
            return RPM_YELLOW
        else:
            return RED

    def update(self, value):
        max_rpm = value.max_rpm
        rpm = value.rpm
        percent = round(float(rpm) / max_rpm, 2)
        num_tiles_shown = int(percent * self.NUM_TILES)
        if num_tiles_shown != self.num_tiles_shown:
            for i in range(self.NUM_TILES):
                self.tiles[i].show()
                if i < num_tiles_shown:
                    self.tiles[i].show()
                else:
                    self.tiles[i].hide()
            self.num_tiles_shown = num_tiles_shown
            return True
        return False

    def draw(self):
        for tile in self.tiles:
            tile.draw()

def fill_background(surface):
    _widgets = {}

    i = 1
    for x in (0, 40, 80, 120, 160, 200, 240, 280):
        for y in (0, 40, 80, 120, 160, 200):
            key = "%s%s" % (x, y)
            if i % 4 == 0:
                widget = Widget(surface, x, y, 39, 39, fill_background=False, draw_borders=True)
            elif i % 4 == 1:
                widget = Widget(surface, x, y, 39, 39, fill_background=True, draw_borders=True)
                widget.background_color = GREEN
                widget.border_color = RED
            elif i % 4 == 2:
                widget = Widget(surface, x, y, 39, 39, fill_background=True, draw_borders=False)
                widget.background_color = BLUE
            elif i % 4 == 3:
                widget = Widget(surface, x, y, 39, 390, fill_background=False, draw_borders=False)
            _widgets[key] = widget
            i = i + 1
    for widget in _widgets.values():
        widget.draw()

class Page(object):

    def __init__(self, name, surface):
        self.name = name
        self.widgets = []
        self.dynamic_widgets = []
        self.surface = surface

    def add(self, widget):
        self.widgets.append(widget)
        if hasattr(widget, 'listen') and getattr(widget, 'listen') is not None:
            self.dynamic_widgets.append(widget)
    def draw_all(self):
        self.surface.fill(BACKGROUND_COLOR)
        for widget in self.widgets:
            widget.draw()

def create_page_0(surface):
    page = Page('Base', surface)

    # RPM BAR Widget
    bar = RPMBarWidget(surface, 0, 0, SCREEN_WIDTH ,20)
    page.add(bar)

    # Gear Number
    gear  = GearNumberWidget(surface, x=SCREEN_WIDTH/2-40, y=40, w=80, h=120, fontsize=130)
    page.add(gear)
    lg = LabelWidget(surface, x=gear.x, y=gear.yy, w=gear.w, h=30, value="Gear", fontsize=16)
    page.add(lg)

    # Speed Widget
    speed = SpeedWidget(surface, x=0, y=gear.y, w=gear.x-5, h=50, fontsize=35)
    page.add(speed)
    ls = LabelWidget(surface, x=speed.x, y=speed.yy, w=speed.w, h=20, value="km/h", fontsize=16)
    page.add(ls)

    rpms = RPMWidget(surface, x=gear.xx+5, y=gear.y, w=SCREEN_WIDTH-gear.xx-5, h=speed.h, fontsize=35)
    page.add(rpms)
    ls = LabelWidget(surface, x=rpms.x, y=rpms.yy, w=rpms.w, h=30, value="rpms", fontsize=16)
    page.add(ls)

    return page

def create_pages(surface):
    global pages
    pages.append(create_page_0(surface))

class Overlay(object):
    def __init__(self, surface):
        self.surface = surface
        self.widgets = []
        self.label_ip = LabelWidget(surface, x=10, y=10, w=SCREEN_WIDTH-20, h=50, value="Listen on: %s:%s" % (IP, UDP_PORT), fontsize=14)
        self.label_ip.background_color = GREY
        self.label_ip.font_color = BLACK
        self.widgets.append(self.label_ip)
        self.label_quit = LabelWidget(surface, x=10, y=70, w=SCREEN_WIDTH-20, h=50, value="Quit", fontsize=14)
        self.label_quit.background_color = GREY
        self.label_quit.font_color = BLACK
        self.widgets.append(self.label_quit)

    def display(self):
        for widget in self.widgets:
            widget.draw()
            widget.add_to_dirty_rects()

    def quit_pressed(self, pos):
        if self.label_quit.rect.collidepoint(pos):
            return True
        else:
            return False

