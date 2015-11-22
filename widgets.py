__author__ = 'Florian'

import pygame
from pygame import Rect
from pygame.font import Font
from config import *
from constants import *

dirty_rects = []
widgets = {}
pages = []

def clear_dirty_rects():
    global dirty_rects
    del dirty_rects[:]

class Widget(object):
    def __init__(self, surface, x, y, w, h, fill_background=False, draw_borders=False):
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
    def __init__(self, surface, x, y, w, h):
        super(TextWidget, self).__init__(surface, x, y, w, h)
        self.value = ""
        self.computed_fontsize = self.find_font_size()
        self._fontsize = self.computed_fontsize
        self.font = Font(FONT, self._fontsize)
        self.background_color = BACKGROUND_COLOR
        self.font_color = FOREGROUND_COLOR
        self.fill_background = True
        self.align = ALIGN_CENTER
        self.valign = VALIGN_CENTER
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
    def __init__(self, surface, x, y, w, h, value):
        super(LabelWidget, self).__init__(surface, x, y, w, h)
        self.value = value

class GearNumberWidget(TextWidget):
    def __init__(self, surface, x, y, w, h):
        super(GearNumberWidget, self).__init__(surface, x, y, w, h)
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
    def __init__(self, surface, x, y, w, h):
        super(RPMWidget, self).__init__(surface, x, y, w, h)
        self.listen = RPM

class SpeedWidget(TextWidget):
    def __init__(self, surface, x, y, w, h):
        super(SpeedWidget, self).__init__(surface, x, y, w, h)
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
    def __init__(self, surface, x, y, w, h):
        super(RPMPercentWidget, self).__init__(surface, x, y, w, h)
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

class RPMBarWidget(Widget):
    def __init__(self, surface, x, y, w, h):
        super(RPMBarWidget, self).__init__(surface, x, y, w, h)
        self.listen = True
        self.percent = 0

    def update(self, value):
        max_rpm = value.max_rpm
        rpm = value.rpm
        percent = round(float(rpm) / max_rpm, 2)
        if percent != self.percent:
            self.percent = percent
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

    def draw(self):
        filled_width = int(self.w * self.percent)
        rect_filled = Rect(self.x, self.y, filled_width, self.h)
        rect_empty = Rect(filled_width, self.y, self.w - filled_width,  self.h)
        pygame.draw.rect(self.surface, self.barcolor, rect_filled, 0)
        pygame.draw.rect(self.surface, BACKGROUND_COLOR, rect_empty, 0)

    @property
    def barcolor(self):
        #GREEN =  (  0, 255,   0)
        #YELLOW = (255, 255,   0)
        #RED   =  (255,   0,   0)
        PERCENT_GREEN = 0.45
        PERCENT_YELLOW_LOW=0.6
        PERCENT_YELLOW_HIGH=0.75
        PERCENT_RED=0.95

        if self.percent < PERCENT_GREEN:
            return GREEN
        elif self.percent < PERCENT_YELLOW_LOW:
            d = 1 - (PERCENT_YELLOW_LOW - self.percent) / (PERCENT_YELLOW_LOW - PERCENT_GREEN)
            return (int(round(255 * d)), 255, 0)
        elif self.percent < PERCENT_YELLOW_HIGH:
            return YELLOW
        elif self.percent < PERCENT_RED:
            d = (PERCENT_RED - self.percent) / (PERCENT_RED - PERCENT_YELLOW_HIGH)
            return (255 , int(round(255 * d)), 0)
        else:
            return RED


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

def create_page_0(surface):
    page = Page('Base', surface)

    # RPM BAR Widget
    bar = RPMBarWidget(surface, 0, 0, SCREEN_WIDTH ,39)
    page.add(bar)

    # Speed Widget
    speed = SpeedWidget(surface, 5, 40, 90, 60)
    speed.align = ALIGN_LEFT
    page.add(speed)
    ls = LabelWidget(surface, speed.x, speed.yy, speed.w, 30, "km/h")
    ls.fontsize = 16
    ls.valign = VALIGN_TOP
    page.add(ls)

    # Gear Number
    gear  = GearNumberWidget(surface, speed.xx, 40, 90, 150)
    gear.fontsize = 150
    page.add(gear)
    lg = LabelWidget(surface, gear.x, gear.yy, gear.w, 30, "Gear")
    lg.fontsize = 16
    lg.valign = VALIGN_TOP
    page.add(lg)

    rpms = RPMWidget(surface, gear.yy, 40, SCREEN_WIDTH-gear.yy, speed.h)
    rpms.align = ALIGN_RIGHT
    page.add(rpms)
    ls = LabelWidget(surface, rpms.x, rpms.yy, rpms.w, 30, "rpms")
    ls.fontsize = 16
    ls.valign = VALIGN_TOP
    page.add(ls)

    rpmpercent = RPMPercentWidget(surface, rpms.x, ls.yy, rpms.w, rpms.h)
    rpms.align = ALIGN_RIGHT
    page.add(rpmpercent)
    ls = LabelWidget(surface, rpmpercent.x, rpmpercent.yy, rpmpercent.w, 30, "rpms %")
    ls.fontsize = 16
    ls.valign = VALIGN_TOP
    page.add(ls)

    return page

def create_pages(surface):
    global pages
    pages.append(create_page_0(surface))
