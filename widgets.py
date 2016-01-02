__author__ = 'Florian'


import pygame
from pygame import Rect
from pygame.font import Font
from config import *
from constants import *
import sys
from collections import deque
from copy import deepcopy
from math import floor

dirty_rects = []
widgets = {}
pages = []

def getit(key, h):
    """Return h[key]. If key has '.' in it like static.max_fuel, return h[static][max_fuel]
    getit('physics.tyre_wear', h') will get you h['physics']['tyre_wear'].
    It's just syntactic sugar, but easier to read.

    Exceptions are not catched
    """
    if '.' in key:
        keys = key.split('.')
        return h.get(keys[0]).get(keys[1])
    else:
        return h.get(key)

def millisToString(millis):
    """Taken from Rivalis OV1Info"""
    hours, x = divmod(int(millis), 3600000)
    mins, x = divmod(x, 60000)
    secs, x = divmod(x, 1000)
    x, y = divmod(x, 10)
    #return "%d.%02d" % (secs, x) if mins == 0 else "%d:%02d.%03d" % (mins, secs, x
    if mins==0:
        return "   %02d:%02d" % (secs, x)
    else:
        return "%02d:%02d:%02d" % (mins, secs, x)


def clear_dirty_rects():
    global dirty_rects
    del dirty_rects[:]

class Widget(object):
    def __init__(self, surface, x, y, w, h, fill_background=False, borders=True):
        self.surface = surface
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = Rect(self.x, self.y, self.w, self.h)
        self.background_color = BACKGROUND_COLOR
        self.border_color = FOREGROUND_COLOR
        self.fill_background = fill_background
        self.borders = borders
        self.border_thickness = 1

    def draw(self):
        if self.fill_background:
            pygame.draw.rect(self.surface, self.background_color, self.rect, 0) # Fill with Background color as width is 0
        if self.draw_borders:
            pygame.draw.rect(self.surface, self.border_color, self.rect, self.border_thickness)     # Draw border as, but not fill as width is 1
        else:
            if self.border_left:
                pygame.draw.line(self.surface, self.border_color, (self.x, self.y), (self.x, self.yy))
            if  self.border_right:
                pygame.draw.line(self.surface, self.border_color, (self.xx, self.y), (self.xx, self.yy))
            if self.border_top:
                pygame.draw.line(self.surface, self.border_color, (self.x, self.y), (self.xx, self.y))
            if self.border_bottom:
                pygame.draw.line(self.surface, self.border_color, (self.x, self.yy), (self.xx, self.yy))

    @property
    def borders(self):
        return self._borders

    @borders.setter
    def borders(self, borders):
        self._borders = borders
        if isinstance(borders, bool):
            if borders:
                self.border_top = self.border_bottom = self.border_left = self.border_right = True
            else:
                self.border_top = self.border_bottom = self.border_left = self.border_right = False
        else:
            self.border_top = 't' in self.borders
            self.border_bottom = 'b' in self.borders
            self.border_left = 'l' in self.borders
            self.border_right = 'r' in self.borders
        self.draw_borders = self.border_top and self.border_bottom and self.border_left and self.border_right


    @property
    def xx(self):
        return self.x + self.w - 1

    @property
    def yy(self):
        return self.y + self.h - 1

    def add_to_dirty_rects(self):
        global dirty_rects
        dirty_rects.append(self.rect)

class TextWidget(Widget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(TextWidget, self).__init__(surface, x, y, w, h, borders=borders)
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

    def update(self, packet):
        if isinstance(packet, dict):
            if self.listen is not None:     # listen == GEAR -> value = d[GEAR]
                value = getit(self.listen, packet)
        else:
            value = packet
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
    def __init__(self, surface, x, y, w, h, value, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(LabelWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.value = value

class GearNumberWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(GearNumberWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'physics.gear'

    def update(self, packet):
        value = getit(self.listen, packet) - 1
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
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(RPMWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'physics.rpms'

class SpeedWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(SpeedWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'physics.speed_kmh'

    def update(self, packet):
        value = getit(self.listen, packet)
        value = int(round(value))
        if value != self.value:
            self.value = value
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class FuelWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(FuelWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'physics.fuel'
        self.laps_completed     = -3
        self.fuel_per_lap       = []    # Array mit verbrauchten Fuel per Lap
        self.fuel_start_of_lap  = -1    # The fuel at the start of the lap
        self.avg_fuel_per_lap   = -1    # The average fuel needed per lap
        self.fuel_laps_left     = -1
        self.laps_left          = -1

    def newlap(self, packet):
        #print "Yeah, newlap"
        fuel = getit(self.listen, packet)
        #print "fuel: %s" % str(fuel)
        self.fuel_used_this_lap = self.fuel_start_of_lap - fuel
        #print "fuel start of lap: %s" % self.fuel_start_of_lap
        #print "self.fuel_used: %s" % self.fuel_used_this_lap
        if self.fuel_used_this_lap > 0.0:
            self.fuel_per_lap.append(self.fuel_used_this_lap)
        else:
            return
        if len(self.fuel_per_lap) > 10:
            self.avg_fuel_per_lap = sum(self.fuel_per_lap[-10:]) / float(len(self.fuel_per_lap[-10:]))
        else:
            self.avg_fuel_per_lap = sum(self.fuel_per_lap) / float(len(self.fuel_per_lap))
        self.fuel_start_of_lap = fuel
        self.fuel_laps_left = int(floor(fuel / self.avg_fuel_per_lap))
        #print self.info

    @property
    def info(self):
        return "\n".join([
            "Laps Completed: %d" % self.laps_completed,
            "Fuel Start oL : %.02f" % self.fuel_start_of_lap,
            "Fuel used thsL: %.02f" % self.fuel_used_this_lap,
            "Fuel per Lap  : %s" % str(self.fuel_per_lap),
            "Avg Fuel p. L.: %.02f" % self.avg_fuel_per_lap,
            "Laps Left     : %d" % self.laps_left,
            "Fuel Laps Left: %s" % self.fuel_laps_left,
            ""
        ])

    def update(self, packet):
        value = getit(self.listen, packet)
        if self.fuel_start_of_lap == -1:
            self.fuel_start_of_lap = value
        laps_completed = getit('graphics.completed_laps', packet)
        #print "laps_completed: %d, self.laps_completed: %d" % (laps_completed, self.laps_completed)
        if laps_completed != self.laps_completed:
            #print "Updating everything"
            self.laps_completed = laps_completed
            self.newlap(packet)
            #print "Fueld Laps left: %d" % self.fuel_laps_left

            if self.fuel_laps_left == -1:
                self.value = 'WAIT'
            else:
                if self.fuel_laps_left > 5:   # 5
                    self.font_color = FOREGROUND_COLOR
                elif 5 >= self.fuel_laps_left >= 2:
                    self.font_color = YELLOW
                else:
                    self.font_color = RED
                self.value = "%02d" % self.fuel_laps_left
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class PosWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(PosWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = POS
        self._num_cars = 0
        self._pos = 0

    def update(self, packet):
        num_cars = getit('static.num_cars', packet)
        pos = getit('graphics.position', packet)
        if num_cars != self._num_cars or pos != self._pos:
            self.value = "   %02d/%02d" % (pos, num_cars)
            self._num_cars = num_cars
            self._pos = pos
            self.add_to_dirty_rects()
            self.draw()
            return True
        return

class LapsWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(LapsWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = LAPS_COMPLETED
        self.laps_completed = -2

    def update(self, packet):
        num_laps = getit('graphics.number_of_laps', packet)
        laps_completed = getit('graphics.completed_laps', packet)
        if laps_completed != self.laps_completed:
            self.value = "   %02d/%02d" % (laps_completed+1, num_laps)
            self.laps_completed = laps_completed
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class LaptimeWidget(TextWidget):
    pass

class RPMPercentWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(RPMPercentWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'physics.rpms'
        self.value = 0

    def update(self, packet):
        rpm = getit('physics.rpm', packet)
        max_rpm = getit('static.max_rpm', packet)
        percent = int(round(float(rpm) / max_rpm, 2) * 100)
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
                           #GREEEN                                          #YELLOW                      #RED
                           #0    1    2     3    4     5    6     7    8     9    10    11    12    13    14    15    16    17    18    19
        self.percent_map = [0.0, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.00]
        self.max_rpm = 1

    def get_color(self, i):
        if i <= 9:
            return GREEN
        elif i <= 14:
            return YELLOW
        return RED

    def get_tiles_shown(self, percent):
        return sum(percent >= map_value for map_value in self.percent_map)

    def update(self, packet):
        rpm = getit('physics.rpms', packet)
        max_rpm = getit('static.max_rpm', packet)
        if max_rpm == 0 and rpm > self.max_rpm:
            self.max_rpm = rpm
        else:
            self.max_rpm = max_rpm
        percent = round(float(rpm) / self.max_rpm, 2)
        num_tiles_shown = self.get_tiles_shown(percent)
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

class TimeWidget(TextWidget):
    def update(self, packet):
        value = getit(self.listen, packet)[:-1]
        if value != self.value:
            self.value = value
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class CurrentTimeWidget(TimeWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(CurrentTimeWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'graphics.i_current_time'
        self.i_value = None

    def update(self, packet):
        i_value = getit(self.listen, packet)
        if i_value != self.i_value:
            self.i_value = i_value
            self.value = millisToString(i_value)
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False

class BestTimeWidget(TimeWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(BestTimeWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'graphics.i_best_time'
        self.value = None
        self.i_value = None

    def update(self, packet):
        i_value = getit(self.listen, packet)
        if i_value != self.i_value:
            self.i_value = i_value
            self.value = millisToString(i_value)
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False


class LastTimeWidget(TimeWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(LastTimeWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'graphics.i_last_time'
        self.value = "--:--:--"
        self.i_value = "--:--:--"
        self.color = FOREGROUND_COLOR

    def update(self, packet):
        i_value = getit(self.listen, packet)
        if i_value == self.i_value:
            return False
        self.i_value = i_value
        self.value = millisToString(i_value)
        i_best_time = getit('graphics.i_best_time', packet)
        i_last_time = getit('graphics.i_last_time', packet)
        if i_last_time == i_best_time:
            self.font_color = GREEN
        elif (i_best_time - i_last_time) > 1000:
            self.font_color = FOREGROUND_COLOR
        else:
            self.font_color = YELLOW
        self.add_to_dirty_rects()
        self.draw()
        return True


class DeltaTimeWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(DeltaTimeWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'delta'
        self.i_value = 0.0

    def update(self, packet):
        i_value = float(getit(self.listen, packet))
        if i_value != self.i_value:
            self.value = millisToString(abs(i_value)*1000)
            if i_value < 0:
                self.font_color = GREEN
            elif i_value > 0:
                self.font_color = RED
            else:
                self.font_color = FOREGROUND_COLOR
            self.add_to_dirty_rects()
            self.draw()
            return True
        return False


class FlagWidget(TextWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(FlagWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'flag'
        self.font_color = FOREGROUND_COLOR
        self.value = 'Flag'
        self.value_enabled = 'flag_enabled'
        self.value_active = 'flag_active'

    def update(self, packet):
        self.is_enabled = getit(self.value_enabled, packet)

        if not self.is_enabled:
            if self.font_color == DARK_GREY:
                return False
            else:
                self.font_color = DARK_GREY
                self.border_color = DARK_GREY
        else:
            self.is_active = getit(self.value_active, packet)
            if self.is_active:
                if self.font_color == YELLOW:
                    return False
                else:
                    self.font_color = YELLOW
                    self.font.set_bold(True)
                    self.border_color = YELLOW
            else:
                if self.font_color == FOREGROUND_COLOR:
                    return False
                else:
                    self.font_color = FOREGROUND_COLOR
                    self.border_color = FOREGROUND_COLOR
                    self.font.set_bold(False)
        self.add_to_dirty_rects()
        self.draw()
        return True

class TCFlagWidget(FlagWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(TCFlagWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'rt_car_info.is_tc_in_action'
        self.font_color = FOREGROUND_COLOR
        self.value = 'TC'
        self.value_enabled = 'rt_car_info.is_tc_enabled'
        self.value_active = 'rt_car_info.is_tc_in_action'

class ABSFlagWidget(FlagWidget):
    def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
        super(ABSFlagWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
        self.listen = 'rt_car_info.is_abs_in_action'
        self.font_color = FOREGROUND_COLOR
        self.value = 'ABS'
        self.value_enabled = 'rt_car_info.is_abs_enabled'
        self.value_active = 'rt_car_info.is_abs_in_action'

# class ObsoleteDeltaTimeWidget(TextWidget):
#     def __init__(self, surface, x, y, w, h, fontsize=None, align=ALIGN_CENTER, valign=VALIGN_CENTER, borders=True):
#         super(DeltaTimeWidget, self).__init__(surface, x, y, w, h, fontsize, align, valign, borders=borders)
#         self.listen = 'graphics.i_current_time'
#         self.last_i_current_time = sys.maxint
#         self.lap_distances = []
#         self.require_initialization = True
#         self.value = 0
#         self.log_current_lap = {}
#         self.log_best_lap = {}
#         self.distances_best_lap = None
#         self.last_distance_compared = -1
#         self.delta = None
#
#     def new_lap(self, packet):
#         distance_traveled = getit('graphics.distance_traveled', packet)
#         distance_traveled_this_lap = distance_traveled - sum(self.lap_distances)
#         self.lap_distances.append(distance_traveled_this_lap)
#         self.last_distance_compared = -1
#
#         i_last_lap = getit('graphics.i_last_time', packet)
#         i_best_lap = getit('graphics.i_best_time', packet)
#         if len(self.log_best_lap) == 0 or i_best_lap == i_last_lap:
#             self.log_best_lap = deepcopy(self.log_current_lap)
#             self.distances_best_lap = deque(sorted(self.log_best_lap.keys()))
#
#         self.log_current_lap = {}
#
#     def update(self, packet):
#         if self.require_initialization:
#             self.lap_distances.append(getit('graphics.distance_traveled', packet))
#             self.require_initialization = False
#             self.value = "n/a"
#             self.add_to_dirty_rects()
#             self.draw()
#             return True
#
#         i_current_time = getit('graphics.i_current_time', packet)
#         if i_current_time < self.last_i_current_time:
#             self.new_lap(packet)
#         self.last_i_current_time = i_current_time                       # remember i_current_time
#
#         lap = getit('graphics.completed_laps', packet) + 1
#         distance_traveled = getit('graphics.distance_traveled', packet)
#         distance_traveled_this_lap = distance_traveled - sum(self.lap_distances)
#         self.log_current_lap[distance_traveled_this_lap] = i_current_time
#         #print "%s - %s - %s" % (lap, self.lap_distances, distance_traveled_this_lap)
#
#         if self.distances_best_lap is not None:
#             try:
#                 while self.last_distance_compared < distance_traveled_this_lap:
#                     self.last_distance_compared = self.distances_best_lap.popleft()
#                 i_compare_time = self.log_best_lap[self.last_distance_compared]
#             except IndexError:
#                 i_compare_time = getit('graphics.i_best_time', packet)
#
#             delta = i_current_time - i_compare_time
#             delta = round(delta / 1000.0, 3)
#
#             if delta != self.delta:
#                 self.value = self.delta = delta
#                 if self.delta < 0:
#                     self.font_color = GREEN
#                 elif self.delta > 0:
#                     self.font_color = RED
#                 self.add_to_dirty_rects()
#                 self.draw()
#                 return True
#         return False


def fill_background(surface):
    _widgets = {}

    i = 1
    for x in (0, 40, 80, 120, 160, 200, 240, 280):
        for y in (0, 40, 80, 120, 160, 200):
            key = "%s%s" % (x, y)
            if i % 4 == 0:
                widget = Widget(surface, x, y, 39, 39, fill_background=False, borders=True)
            elif i % 4 == 1:
                widget = Widget(surface, x, y, 39, 39, fill_background=True, borders=True)
                widget.background_color = GREEN
                widget.border_color = RED
            elif i % 4 == 2:
                widget = Widget(surface, x, y, 39, 39, fill_background=True, borders=False)
                widget.background_color = BLUE
            elif i % 4 == 3:
                widget = Widget(surface, x, y, 39, 390, fill_background=False, borders=False)
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

def create_page_1(surface):
    page = Page('Base1', surface)
    LABEL_HEIGHT=20
    DEFAULT_HEIGHT=50

    # RPM BAR Widget
    bar = RPMBarWidget(surface, 0, 0, SCREEN_WIDTH ,20)
    page.add(bar)

    # Speed Widget
    w_speed = SpeedWidget(surface, x=0, y=26, w=90, h=DEFAULT_HEIGHT, fontsize=35, borders=BORDER_TLR)
    page.add(w_speed)
    l_speed = LabelWidget(surface, x=w_speed.x, y=w_speed.yy, w=w_speed.w, h=LABEL_HEIGHT, value="km/h", fontsize=16, borders=BORDER_BLR)
    page.add(l_speed)

    # Fuel
    w_fuel = FuelWidget(surface, x=l_speed.x, y=l_speed.yy+4, w=l_speed.w, h=DEFAULT_HEIGHT, fontsize=25, borders=BORDER_TLR)
    page.add(w_fuel)
    l_fuel = LabelWidget(surface, x=w_fuel.x, y=w_fuel.yy, w=w_fuel.w, h=LABEL_HEIGHT, value="FuelLaps", fontsize=16, borders=BORDER_BLR)
    page.add(l_fuel)

    # TC
    tc = TCFlagWidget(surface, x=l_fuel.x, y=l_fuel.yy+4, w=int(round(l_fuel.w/2)-2), h=int(round(w_fuel.h/2)), fontsize=16, borders=BORDER_ALL)
    page.add(tc)

    # ABS
    abs = ABSFlagWidget(surface, x=tc.xx+4, y=tc.y, w=int(round(l_fuel.w/2)-1), h=int(round(w_fuel.h/2)), fontsize=16, borders=BORDER_ALL)
    page.add(abs)


    # Gear Number
    w_gear  = GearNumberWidget(surface, x=w_speed.xx+4, y=w_speed.y, w=80, h=122, fontsize=135, borders=BORDER_TLR)
    page.add(w_gear)
    l_gear = LabelWidget(surface, x=w_gear.x, y=w_gear.yy, w=w_gear.w, h=LABEL_HEIGHT, value="Gear", fontsize=16, borders=BORDER_BLR)
    page.add(l_gear)

    # Current Time Widget
    l_current_time = LabelWidget(surface, x=w_gear.xx+4, y=w_gear.y, w=TIME_LABEL_WIDTH, h=33, fontsize=16, value="Cur", borders='tlb')
    page.add(l_current_time)
    w_current_time = CurrentTimeWidget(surface, x=l_current_time.xx, y=l_current_time.y, w=TIME_WIDGET_WIDTH, h=l_current_time.h, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(w_current_time)

    # Delta Time Widget
    l_delta_time = LabelWidget(surface, x=l_current_time.x, y=l_current_time.yy+4, w=TIME_LABEL_WIDTH, h=33, fontsize=16, value=u"d/t", borders='tlb')
    page.add(l_delta_time)
    w_delta_time = DeltaTimeWidget(surface, x=l_delta_time.xx, y=l_delta_time.y, w=TIME_WIDGET_WIDTH, h=l_delta_time.h, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(w_delta_time)

    # Last Time Widget
    l_last_time = LabelWidget(surface, x=l_current_time.x, y=l_delta_time.yy+4, w=TIME_LABEL_WIDTH, h=33, fontsize=16, value=u"Lst", borders='tlb')
    page.add(l_last_time)
    w_last_time = LastTimeWidget(surface, x=l_last_time.xx, y=l_last_time.y, w=TIME_WIDGET_WIDTH, h=l_last_time.h, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(w_last_time)

    # best Time Widget
    l_best_time = LabelWidget(surface, x=l_current_time.x, y=l_last_time.yy+4, w=TIME_LABEL_WIDTH, h=33, fontsize=16, value=u"Bst", borders='tlb')
    page.add(l_best_time)
    w_best_time = BestTimeWidget(surface, x=l_best_time.xx, y=l_best_time.y, w=TIME_WIDGET_WIDTH, h=l_best_time.h, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(w_best_time)

    # Pos Widget
    l_pos = LabelWidget(surface, x=l_best_time.x, y=l_best_time.yy+4, w=TIME_LABEL_WIDTH, h=30, fontsize=16, value=u"Pos", borders='tlb')
    page.add(l_pos)
    pos = PosWidget(surface, x=l_pos.xx, y=l_pos.y, w=TIME_WIDGET_WIDTH, h=30, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(pos)

    # Laps Widget
    l_laps = LabelWidget(surface, x=l_pos.x, y=l_pos.yy+4, w=TIME_LABEL_WIDTH, h=30, fontsize=16, value=u"Lap", borders='tlb')
    page.add(l_laps)
    laps = LapsWidget(surface, x=l_laps.xx, y=l_laps.y, w=TIME_WIDGET_WIDTH, h=30, fontsize=20, align=ALIGN_CENTER, borders='tbr')
    page.add(laps)


    return page

def create_pages(surface):
    global pages
    pages.append(create_page_1(surface))

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

