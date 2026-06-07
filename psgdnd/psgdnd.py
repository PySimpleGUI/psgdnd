import PySimpleGUI as sg
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_TEXT, DND_ALL, CF_UNICODETEXT, CF_HDROP, CF_TEXT
import re


version = '6.0'
__version__ = version.split()[0]

class DropEvent(object):
    def __init__(self, window, key, element, drop_type):
        self.key = key
        self.element = element
        self.drop_type = drop_type
        self.window = window


# PySimpleGUI drop type constants
DROP_TYPE_TEXT = 'TEXT'
DROP_TYPE_FILES = 'FILES'
DROP_TYPE_ALL = 'ALL'
DROP_TYPE_UNKNOWN = 'UNKNOWN'


"""
    Drag and Drop support for PySimpleGUI using tkinterdnd2

    Experimental / Prototype

    Drag and drop demo using tkinterdnd2 (installed as part of psgdnd)
        python -m pip install tkinterdnd2
    Routes drop event through the window.read.
       

    Copyright 2018-2026 PySimpleGUI. All rights reserved.
"""



#     ______   ______  _____   _____
#     |     \ |_____/ |     | |_____]
#     |_____/ |    \_ |_____| |
#
#          HELPER FUNCTIONS

def register_element_dnd(element: sg.Element, window: sg.Window, drop_type=DROP_TYPE_ALL):
    TkinterDnD._require(window.TKroot)

    if drop_type == DROP_TYPE_TEXT:
        element.widget.drop_target_register(DND_TEXT)
    elif drop_type == DROP_TYPE_FILES:
        element.widget.drop_target_register(DND_FILES)
    elif drop_type == DROP_TYPE_ALL:
        element.widget.drop_target_register(DND_ALL)
    else:
        print(f'ERROR Bad drop type in register_element_dnd.  {drop_type=}')
        return

    # When get drop event, send an event through the window.read call in the event loop
    # Format of event is a tuple.  event = ('+DROP+', key of element dropped on).  In values dict key = filename that was dropped as a string
    # element.widget.dnd_bind("<<Drop>>", lambda event, element=element, window=window : window.write_event_value(('+DROP+', element.key), reformat_filenames(event.data)))
    element.widget.dnd_bind("<<Drop>>", lambda event, element=element, window=window: on_drop(event, element, window))


def on_drop(event, element: sg.Element, window: sg.Window):
    # When drop event happens, send event to event loop.
    # Event generated will be a DropEvent object
    # print(f'{event.type=}')
    if event.type in (CF_TEXT, CF_UNICODETEXT):
        drop_type = DROP_TYPE_TEXT
        value_data = event.data
    elif event.type == CF_HDROP:
        drop_type = DROP_TYPE_FILES
        value_data = reformat_filenames(event.data)
    else:
        drop_type = DROP_TYPE_UNKNOWN
        value_data = event.data

    drop_event = DropEvent(window=window, key=element.key, element=element, drop_type=drop_type)       # Fill in a DropEvent object
    window.write_event_value(drop_event, value_data)                                                   # Send the DropEvent object as event to the window


def reformat_filenames(filenames: str) -> str:
    # reformat the string of filenames so that each filename is separated with a ","
    # input string has filenames separated with a space AND if a filename contains spaces it is surrounded by { }
    # I'm not good at Regex and asked for help from a CheatBot
    files = re.findall(r'\{([^}]*)\}|(\S+)', filenames)
    return ','.join(a or b for a, b in files)


def is_drop_event(event):
    return isinstance(event, DropEvent)

# just in case module is called
def main():
    return