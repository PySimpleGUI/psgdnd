import PySimpleGUI as sg
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_TEXT, DND_ALL, CF_UNICODETEXT, CF_HDROP, CF_TEXT
import re



version = '6.0.2'
__version__ = version.split()[0]

"""
Changelog 

6.0         17-Jun-2026 Release to PyPI
6.0.2       19-Jun-2026 Added support for Linux. Needed to handle different drop events from tkinterdnd2
"""



#                            __              __
#                           /\ \            /\ \
#  _____     ____     __    \_\ \    ___    \_\ \
# /\ '__`\  /',__\  /'_ `\  /'_` \ /' _ `\  /'_` \
# \ \ \L\ \/\__, `\/\ \L\ \/\ \L\ \/\ \/\ \/\ \L\ \
#  \ \ ,__/\/\____/\ \____ \ \___,_\ \_\ \_\ \___,_\
#   \ \ \/  \/___/  \/___L\ \/__,_ /\/_/\/_/\/__,_ /
#    \ \_\            /\____/
#     \/_/            \_/__/


"""
    psgdnd module - Drag and Drop support for PySimpleGUI using tkinterdnd2

    Experimental / Prototype

    Drag and drop demo using tkinterdnd2 (installed as part of psgdnd)
        python -m pip install tkinterdnd2
    Routes drop event through the window.read.

    pip install psgdnd
    Then import into your project to extend PySimpleGUI to support drag and drop

    Copyright 2018-2026 PySimpleGUI. All rights reserved.
"""


class DropEvent(object):
    def __init__(self, window, key, element, drop_type, tkdnd_type):
        """
        The object that carries drag and drop events to the PySimpleGUI event loop. The event will be one of these objects
        when a drag and drop event happens
        :param window:                  The window receiving the drop
        :type window:                   (sg.Window)
        :param key:                     The key of the element dropped onto
        :type key:                      (str)
        :param element:                 The element object dropped onto
        :type element:                  (sg.Element)
        :param drop_type:               Type of drop. Values are constants DROP_TYPE_TEXT, DROP_TYPE_FILES, DROP_TYPE_ALL, DROP_TYPE_DROP_TYPE_UNKNOWN
        :type drop_type:                (str)
        :param tkdnd_type:              Type of drop reported by tkinterdnd2 (for debugging or perhaps hacking until a bug gets fixed)
        :type tkdnd_type:               (str)
        """
        self.key = key
        self.element = element
        self.drop_type = drop_type
        self.window = window
        self.tkdnd_type = tkdnd_type

# PySimpleGUI drop type constants
DROP_TYPE_TEXT = 'TEXT'
DROP_TYPE_FILES = 'FILES'
DROP_TYPE_ALL = 'ALL'
DROP_TYPE_UNKNOWN = 'UNKNOWN'

#  Additional drop types that can come through tkinterdnd2.  These were seen on Zorin Linux
TK_DROP_TYPE_URI_LIST = 'text/uri-list'
TK_DROP_TYPE_UTF8_STRING = 'UTF8_STRING'


def is_drop_event(event):
    """
    Returns True if the passed in event is a drop event.  A drop event is always a DropEvent object

    :param event:               Event to check
    :type event:                (Any)
    :return:                    Trye if the event is a drop event
    :rtype:                     (bool)
    """

    return isinstance(event, DropEvent)


def _enable_logging():
    """
    Turns on logging

    """
    global logging_enabled

    logging_enabled = True

def register_element_dnd(element: sg.Element, window: sg.Window, drop_type=DROP_TYPE_ALL):
    """
    Register a window element to accept Drag and Drop.
    Pass in your elmenent object, the window that contains it, the type of drops it can receive.
    Valid drop types: DROP_TYPE_TEXT, DROP_TYPE_FILES, DROP_TYPE_ALL

    :param element:            Element to register
    :type element:             (sg.Element)
    :param window:             Window that contains the element
    :type window:              (sg.Window)
    :param drop_type:          Type of drops it should accept. DROP_TYPE_TEXT, DROP_TYPE_FILES, DROP_TYPE_ALL
    :type drop_type:           (str)
    """
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
    # Bind drop event to the widget.  Set callback function on_drop
    element.widget.dnd_bind("<<Drop>>", lambda event, element=element, window=window: on_drop(event, element, window))


def on_drop(event, element: sg.Element, window: sg.Window):
    """
    The function that is called when a drop happens.  This function reformats and puts the data
    into a DropEvent object and sends it to the window's event queue.

    :param event:           Data about the drop event
    :type event:            (tkinterdnd2.TkinterDnD.DnDEvent)
    :param element:         Element that received the drop
    :type element:          (sg.Element)
    :param window:          Window that contains the element
    :type window:           (sg.Window)
    """

    # When drop event happens, send event to event loop.
    # Event generated will be a DropEvent object

    if event.type in (CF_TEXT, CF_UNICODETEXT, DND_TEXT, TK_DROP_TYPE_UTF8_STRING):
        drop_type = DROP_TYPE_TEXT
        value_data = event.data
    elif event.type in (CF_HDROP, DND_FILES, TK_DROP_TYPE_URI_LIST):
        drop_type = DROP_TYPE_FILES
        value_data = _reformat_filenames(event.data)
    else:
        drop_type = DROP_TYPE_UNKNOWN
        value_data = event.data

    drop_event = DropEvent(window=window, key=element.key, element=element, drop_type=drop_type, tkdnd_type=event.type)       # Fill in a DropEvent object
    window.write_event_value(drop_event, value_data)                                                   # Send the DropEvent object as event to the window


def _reformat_filenames(filenames: str) -> str:
    """
    Reformats the string of filesname provided by tkinterdnd2 into a string with filenames
    separated by commas.

    :param filenames:           Filenames string to convert
    :type filenames:            (str)
    :return:                    The converted string
    :rtype:                     (str)
    """

    # reformat the string of filenames so that each filename is separated with a ","
    # input string has filenames separated with a space AND if a filename contains spaces it is surrounded by { }
    # I'm not good at Regex and asked for help from a CheatBot
    files = re.findall(r'\{([^}]*)\}|(\S+)', filenames)
    return ','.join(a or b for a, b in files)


