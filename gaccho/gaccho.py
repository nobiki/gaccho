#!/usr/bin/python
# -*- coding:utf-8 -*-

import curses
import os
import time
import datetime
import pytz
import sys
import re
import pkg_resources
import importlib
import configparser

# import locale
import unicodedata
# locale.setlocale(locale.LC_ALL, "")

import Article

EDGE_TOP = 1
EDGE_BOTTOM = 1
EDGE_LEFT = 2
EDGE_RIGHT = 2
EDGE_HEIGHT = EDGE_TOP + EDGE_BOTTOM
EDGE_WIDTH = EDGE_LEFT + EDGE_RIGHT

CATEGORY_WIDTH = 8

ARTICLE_CATEGORY    = 0
ARTICLE_FEEDTITLE   = 1
ARTICLE_TIMESTAMP   = 2
ARTICLE_AUTHOR      = 3
ARTICLE_TITLE       = 4
ARTICLE_URL         = 5
ARTICLE_BODY        = 6

class Gaccho:
    focus       = ""

    plugins     = []
    tl          = []
    color       = {}

    key_repeat  = 0
    key_pair    = ""
    key_trigger = ""

    lastupdate = ""

    def __init__(self, stdscr):

        curses.endwin()

        ## load config
        self.config = configparser.ConfigParser()
        self.config.read("gaccho.ini")

        ## load plugins
        for dist in pkg_resources.working_set:
            if re.compile("^gaccho").search(dist.project_name):
                tmp = dist.project_name.split("-")
                ClassName = str(tmp[1][0].upper() + tmp[1][1:])
                module = importlib.import_module(dist.project_name.replace("-","_")+"."+ClassName)
                Klass = getattr(module, ClassName)
                self.plugins.append(Klass())

        ## curses initialize
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.curs_set(0)

        ## window initialize
        self.position = 0
        self.offset_y = 0
        self.mainscr = stdscr

        # get plugins color pair
        self.color_pair()

        # set color setting
        curses.init_pair(70, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        self.color.update({"url": 70})

        # get plugins timeline
        self.timeline(self.mainscr)

        # entry point
        try:
            self.setup()
            self.loop()

        finally:
            self.final()

    ## mainscr: loop
    def loop(self):
        while 1:
            self.focus = "main"
            self.main_y, self.main_x = self.mainscr.getmaxyx()

            setsumei = [
                    "[Last Update] "+self.lastupdate,
                    "[o] Open",
                    "[q] Close",
                    "[r] Refresh",
                    ]

            #-----> debug
            setsumei_debug = [
                    "x: "+str(self.main_x),
                    "y: "+str(self.main_y),
                    "pos: "+str(self.position),
                    "offset: "+str(self.offset_y),
                    "repeat: "+str(self.key_repeat),
                    "pair: "+str(self.key_pair),
                    "trigger: "+str(self.key_trigger),
                    ]
            setsumei = setsumei + setsumei_debug
            #<----- debug

            self.mainscr.addstr(0, 0, "  ".join(setsumei))

            for index, item in enumerate(self.tl[self.offset_y:]):
                if index < self.main_y-EDGE_HEIGHT:
                    category = '%s' % (item[ARTICLE_CATEGORY])

                    # message
                    if item[ARTICLE_TITLE] != "":
                        message = item[ARTICLE_TITLE]
                    else:
                        message = item[ARTICLE_BODY]
                    message = message.split("\n")
                    message = message[0]

                    if index == self.position-self.offset_y:
                        message_color = curses.A_REVERSE
                    else:
                        message_color = curses.A_NORMAL

                    # category
                    if category in self.color.keys():
                        category_color = curses.color_pair(self.color[category])
                    else:
                        category_color = curses.A_NORMAL

                    # render tl
                    self.mainscr.addstr(EDGE_TOP+index,     1, self.truncate(category.ljust(CATEGORY_WIDTH), CATEGORY_WIDTH, False), category_color)
                    self.mainscr.addstr(EDGE_BOTTOM+index, CATEGORY_WIDTH+1, self.truncate(message, self.main_x-EDGE_WIDTH-CATEGORY_WIDTH-EDGE_RIGHT-1), message_color)

            # input
            c = self.mainscr.getch()
            self.mainscr.refresh()
            if c == ord('q'): break # Exit the while()
            elif self.controll(c, self.mainscr) == False:
                break

    ## subscr: loop
    def detail(self, article):
        self.subscr = curses.newwin(self.main_y-4, self.main_x-4, 2, 2)
        self.subscr.clear()
        self.setup(self.subscr)
        self.detail_y, self.detail_x = self.subscr.getmaxyx()

        line_height = 0

        # timestamp, author
        height_timestamp = EDGE_TOP

        tdatetime = datetime.datetime.strptime(article[ARTICLE_TIMESTAMP], '%Y-%m-%d %H:%M:%S')
        _zone = pytz.timezone('Asia/Tokyo')
        published = _zone.fromutc(tdatetime).strftime("%Y/%m/%d %H:%M:%S")

        self.subscr.addstr(height_timestamp, 1, str("["+published+"] author: "+article[ARTICLE_AUTHOR]))

        # line
        line_height += 1
        self.subscr.hline(height_timestamp+1, 1, curses.ACS_HLINE, self.detail_x-EDGE_RIGHT)

        # category
        if article[ARTICLE_CATEGORY] in self.color.keys():
            category_color = curses.color_pair(self.color[article[ARTICLE_CATEGORY]])
        else:
            category_color = curses.A_NORMAL

        self.subscr.addstr(EDGE_TOP,self.detail_x-1-self.strlen(str(article[ARTICLE_CATEGORY]))-3,"["+str(article[ARTICLE_CATEGORY])+"]",category_color)

        # title
        height_title = height_timestamp + line_height
        if article[ARTICLE_TITLE] != "":
            article_title = self.carriage(article[ARTICLE_TITLE]+" ["+article[ARTICLE_FEEDTITLE]+"]", self.detail_x-EDGE_WIDTH-2)
            for line in article_title:
                if height_title > 1:
                    self.subscr.addstr(EDGE_TOP+height_title,1,article_title[line])
                else:
                    self.subscr.addstr(EDGE_TOP+height_title,1,self.truncate(article_title[line], self.detail_x-EDGE_WIDTH-CATEGORY_WIDTH-1))
                height_title += 1

        # url
        height_url   = height_title
        article_url = self.carriage(article[ARTICLE_URL], self.detail_x-EDGE_WIDTH-3)
        for line in article_url:
            self.subscr.addstr(EDGE_TOP+height_url,1,article_url[line], curses.color_pair(self.color["url"]))
            height_url += 1

        # line
        line_height += 1
        self.subscr.hline(height_url+1, 1, curses.ACS_HLINE, self.detail_x-EDGE_RIGHT)

        # body
        i = 0
        j = height_url+line_height
        message = str(article[ARTICLE_BODY]).split("\n")
        for line in message:
            inner = self.carriage(message[i], self.detail_x-EDGE_WIDTH-3)
            for line2 in inner:
                self.subscr.addstr(j,1,inner[line2])
                j += 1
                if i+j > self.detail_y-EDGE_BOTTOM:
                    break
            i += 1
            if i+j >  self.detail_y-EDGE_BOTTOM:
                self.subscr.addstr(j,1,"...")
                break

        while 1:
            self.focus = "detail"

            # input
            c = self.subscr.getch()
            if c == ord('q'):
                self.subscr.clear()
                self.subscr.refresh()
                break # Exit the while()
            elif self.controll(c, self.subscr) == False:
                break # Exit the while()

    ## screen setup
    def setup(self, win=False):
        try:
            if win == self.subscr:
                self.detail_y, self.detail_x = self.subscr.getmaxyx()
        except:
            win = self.mainscr
            self.main_y, self.main_x = self.mainscr.getmaxyx()

        win.keypad(True)
        win.border(0)
        win.refresh()

    ## key operation
    def controll(self, key, win):

        ## r
        if self.key_pair == "" and key == ord("r"):
            win.clear()
            self.setup(win)

            if win == self.mainscr:
                self.timeline(win, False)
            elif win == self.subscr:
                self.detail(self.tl[self.position])
                return False

        ## resize window
        elif key == curses.KEY_RESIZE:
            win.clear()
            self.setup(win)

            if self.focus == "detail":
                self.main_y, self.main_x = self.mainscr.getmaxyx()
                self.detail(self.tl[self.position])
                return False

        ## up, k
        elif self.key_pair == "" and (key == curses.KEY_UP or key == ord("k")):
            if self.key_repeat > 0:
                self.navigate(self.key_repeat * -1, win)
                self.key_repeat = 0
            else:
                self.navigate(-1, win)

        ## down, j
        elif self.key_pair == "" and (key == curses.KEY_DOWN or key == ord("j")):
            if self.key_repeat > 0:
                self.navigate(self.key_repeat, win)
                self.key_repeat = 0
            else:
                self.navigate(1, win)

        ## left, PageUp, h
        elif self.key_pair == "" and (key == curses.KEY_LEFT or key == curses.KEY_PPAGE or key == ord("h") or key == ord("u")):
            self.navigate((self.main_y-EDGE_TOP+(self.position-self.offset_y)) * -1, win)
            self.offset_y = self.position

        ## right, PageDown, l
        elif self.key_pair == "" and (key == curses.KEY_RIGHT or key == curses.KEY_NPAGE or key == ord("l") or key == ord("d")):
            self.navigate(self.main_y-EDGE_BOTTOM-(self.position-self.offset_y), win)
            self.offset_y = self.position

        ## enter, o
        elif self.key_pair == "" and (key == 10 or key == ord("o")):
            if self.focus == "main":
                self.detail(self.tl[self.position])

        ## repeat[0-9]
        elif 48 <= key <= 57:
            input_num = str(key - 48)
            exist_num = str(self.key_repeat)

            if self.key_repeat > 0:
                self.key_repeat = int(exist_num + input_num)
            else:
                self.key_repeat = int(input_num)

        ## gg
        elif self.key_pair == ord("g") and key == ord("g"):
            self.position = 0
            self.offset_y = 0
            self.key_pair = ""

        ## G
        elif key == ord("G"):
            win.clear()
            self.setup(win)
            self.position = len(self.tl)-1
            self.offset_y = len(self.tl)-1

        ## mark all ma
        elif self.key_pair == ord("m") and key == ord("a"):
            self.key_trigger = "mark all"
            self.key_pair = ""

        ## mark one mm
        elif self.key_pair == ord("m") and key == ord("m"):
            if self.key_repeat > 0:
                self.key_trigger = "mark ("+str(self.key_repeat)+")"
                self.key_repeat = 0
            else:
                self.key_trigger = "mark one"
            self.key_pair = ""

        ## input stack
        else:
            ret = {"key_trigger":"", "key_pair":""}
            for p in self.plugins:
                ret = p.controll(key_pair=self.key_pair, key_trigger=self.key_trigger, key=key)
                if ret["key_trigger"] != "" or ret["key_pair"] != "":
                    break

            if self.key_pair == "" and ret["key_pair"] != "":
                self.key_pair = ret["key_pair"]
            elif self.key_pair != "" and ret["key_trigger"] != "":
                self.key_trigger = ret["key_trigger"]
                self.key_pair = ""
            elif self.key_pair == "":
                self.key_pair = key
            else:
                self.key_trigger = "out of pair"
                self.key_pair = ""

        if win == self.mainscr:
            pass
        elif win == self.subscr:
            self.detail(self.tl[self.position])
            return False

        return True

    ## move cursor
    def navigate(self, n, win):
        self.position += n

        ## 画面上下
        if n < 0:
            # top
            if self.position <= self.offset_y:
                self.mainscr.clear()

            if self.position <= 0:
                self.offset_y = 0
            elif self.position < self.offset_y:
                self.mainscr.clear()
                self.offset_y = self.offset_y - (n * -1)

        elif self.position+EDGE_HEIGHT >= self.main_y+self.offset_y:
            # bottom
            self.mainscr.clear()

            self.offset_y = self.position+EDGE_HEIGHT+EDGE_BOTTOM - self.main_y
            if self.position >= len(self.tl):
                self.offset_y = len(self.tl)-1

        ## 可動範囲制御
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.tl):
            self.position = len(self.tl)-1
        if self.offset_y < 0:
            self.offset_y = 0
        elif self.offset_y >= len(self.tl):
            self.offset_y = len(self.tl)-1

        self.setup(win)

    ## color setting
    def color_pair(self):
        i=0
        for p in self.plugins:
            category = p.__class__.__name__

            # plugin default color setting load.
            i += 1
            color_pair = p.color_pair()
            self.color.update({category: i})
            curses.init_pair(i, eval("curses.COLOR_"+color_pair["color_text"]), eval("curses.COLOR_"+color_pair["color_back"]))

            # type color setting load.
            for c in enumerate(self.config):
                i += 1
                item = c[1]

                if "type" in self.config[c[1]]:
                    ptype = self.config[c[1]]["type"]
                    if category == ptype:
                        self.color.update({item: i})
                #     else:
                #         self.color.update({category: i})
                # else:
                #     self.color.update({category: i})

                if item in self.config and self.config[item].get("color_text") and self.config[item].get("color_back"):
                    color_pair = dict(self.config[item])
                elif category in self.config and self.config[category].get("color_text") and self.config[category].get("color_back"):
                    color_pair = dict(self.config[category])
                else:
                    color_pair = p.color_pair()
                curses.init_pair(i, eval("curses.COLOR_"+color_pair["color_text"]), eval("curses.COLOR_"+color_pair["color_back"]))

    ## get timeline
    def timeline(self, win, cache = True):
        self.tl = []
        self.lastupdate = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        for p in self.plugins:
            category = p.__class__.__name__
            cachefile = "cache/"+category

            interval = 60
            if category in self.config:
                if self.config[category].get("interval"):
                    interval = self.config[category].get("interval")

            win.clear()
            win.addstr(0, 0, category+": Loading...")
            win.refresh()

            if os.path.exists(cachefile) and cache == True:
                dt  = datetime.datetime.fromtimestamp(os.stat(cachefile).st_mtime)
                diff = (datetime.datetime.now() - dt).total_seconds() / 60

                if int(diff) < int(interval) or int(interval) == 0:
                    f = open(cachefile)
                    self.tl = self.tl + eval(f.read())
                    f.close()

                    self.lastupdate = dt.strftime('%Y/%m/%d %H:%M:%S')
                else:
                    self.tl = self.tl + p.get()
            else:
                if os.path.exists("cache") == False:
                    os.mkdir("cache")

                self.tl = self.tl + p.get()

        ## sort by timestamp
        self.tl = sorted(self.tl, key=lambda x:x[ARTICLE_TIMESTAMP], reverse=True)

    ## final
    def final(self):
        curses.echo()
        curses.nocbreak()
        self.mainscr.keypad(False)
        curses.endwin()

    ## get length
    def strlen(self, text):
        length = 0

        for char in list(text):
            if unicodedata.east_asian_width(char) == "W":
                length += 2
            else:
                length += 1

        return length

    ## truncate long text
    def truncate(self, message, num_bytes, suffix=True, encoding='utf-8'):
        length = 0
        ret = ""
        for char in list(message):
            if unicodedata.east_asian_width(char) == "W":
                length += 2
            else:
                length += 1

            if length < num_bytes:
                ret += char
            else:
                if length >= num_bytes:
                    if suffix == True:
                        ret = ret[:-2] + ".."
                break

        return ret

    ## carriage return long text
    def carriage(self, message, num_bytes):
        ret = {}

        length = 0
        i = 0
        ret[i] = ""

        for char in list(message):
            if unicodedata.east_asian_width(char) == "W":
                length += 2
            else:
                length += 1

            if length >= num_bytes:
               ret[i] = ret[i] + char

               length = 0
               i += 1
               ret[i] = ""
            else:
               ret[i] = ret[i] + char

        return ret



if __name__=='__main__':
    curses.wrapper(Gaccho)
