import configparser

from lib.HTMLStripper import HTMLStripper

class Article:
    def color_pair(self):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError

    def strip_tags(self, html):
        s = HTMLStripper()
        s.feed(html)
        return s.get_data()

