import PySimpleGUI as sg
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_TEXT, DND_ALL, CF_UNICODETEXT, CF_HDROP, CF_TEXT, COPY, REFUSE_DROP
import re
import os



version = '6.0.6'
__version__ = version.split()[0]

"""
Changelog 

6.0         17-Jun-2026 Release to PyPI
6.0.2       19-Jun-2026 Added support for Linux. Needed to handle different drop events from tkinterdnd2
6.0.4       21-Jun-2026 Release Linux fixes to PyPI
*******************************************
19-Sep-2026 This is the first PySimpleGUI project file checked in with Claude changes.  
6.0.5       12-Sep-2026 Claude: Added enable(window, rules, skip) that registers every input-type element with a per-type default
                        behaviour (Rule / DEFAULT_RULES): the drop is applied to the element (path into Input/Combo, lines into
                        Multiline, items into Listbox, picture into Image, Browse buttons forward to their target) and the usual
                        DropEvent is still sent. Hover tint + accept/refuse cursor, ext/folder/multiple filtering, window-background
                        target, DropEvent.files/.text/.file/.applied, target()/untarget(), main() demo so "python -m psgdnd" works.
6.0.6       20-Sep-2026 Changed the color of multiline element.  Changed the text colors printed in Multiline to be more readable                        
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
    def __init__(self, window, key, element, drop_type, tkdnd_type, files=None, text=None, rule=None):
        """
        The object that carries drag and drop events to the PySimpleGUI event loop. The event will be one of these objects
        when a drag and drop event happens.  When the element was registered with a Rule (see enable()), files / text / rule
        are filled in and applied tells whether the default action was performed on the element.
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
        self.files = files if files is not None else []       # list of normalised paths (rule path only; [] for text drops)
        self.text = text                                       # dropped text (rule path only; None for file drops)
        self.rule = rule                                       # the Rule in force, None when registered the classic way
        self.applied = False                                   # True once the default action changed the element

    @property
    def file(self):
        return self.files[0] if self.files else None

    def __repr__(self):
        what = f'{len(self.files)} file(s) {self.files}' if self.files else f'text {self.text!r:.60}'
        return f'DropEvent(key={self.key!r}, {self.drop_type}, {what}, applied={self.applied})'

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

def register_element_dnd(element: sg.Element, window: sg.Window, drop_type=DROP_TYPE_ALL, rule=None, on_drop_callback=None):
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
    :param rule:               Optional Rule. When given, the drop is applied to the element (default action), hover feedback is shown,
                               ext/folder/multiple filtering happens and the DropEvent carries .files / .text.  See enable()
    :type rule:                (Rule | None)
    :param on_drop_callback:   Optional callback(drop_event) run before the default action; return False to cancel the default action
    :type on_drop_callback:    (callable | None)
    """
    TkinterDnD._require(window.TKroot)

    if rule is not None:
        _register_with_rule(window, element, rule, on_drop_callback)
        return

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


# Claude's epic fail trying to generate a figlet....
#                     ____                      ___              __
#                    /\  _`\                   /\_ \            /\ \\
#   __     ___     __\ \ \L\ \  __  __   ___   \//\ \      __   \_\ \\
#  /'___\ / __`\ /'__`\ \ ,  / /\ \/\ \ /'___\   \ \ \   /'__`\ /'_` \\
# /\ \__//\ \L\ \\ \ \L\.\_\ \ \\ \\ \ \_\ \/\ \__/    \_\ \_/\  __//\ \L\ \\
# \ \____\ \____/ \ \__/.\_\\ \_\ \_\ \____/\ \____\   /\____\ \____\ \___,_\\
#  \/____/\/___/   \/__/\/_/ \/_/\/_/\/___/  \/____/   \/____/\/____/\/__,_ /
#
# Rule-based registration: one call, every input-type element becomes a drop target with a standard behaviour.
#
#     import psgdnd
#     window = sg.Window('My App', layout, finalize=True)
#     psgdnd.enable(window)                        # or  psgdnd.enable(window, rules={K_MIDI: psgdnd.Rule(ext=('.mid',))}, skip=[K_SEARCH])
#     ...
#     if psgdnd.is_drop_event(event):               # event.key  event.files  event.file  event.text  event.applied  values[event]
#
# The default action (path into Input, lines into Multiline, items into Listbox, picture into Image ...) has already been done
# when the DropEvent reaches window.read(); most targets need no code in the event loop at all.

# file policies
PATH = 'path'                     # files -> put the path(s) into the element (default)
CONTENTS = 'contents'             # files -> read text file(s) and put their contents into the element (Multiline / Input)
IMAGE = 'image'                   # files -> show the picture in the element (Image)
EVENT_ONLY = 'event'              # files/text -> do not touch the element, only send the DropEvent (Graph, Table, Tree, window)
# text policies
REPLACE = 'replace'               # text -> replace the element's contents
INSERT = 'insert'                 # text -> insert at the cursor
APPEND = 'append'                 # text -> add at the end (Listbox: add items, one per line)

IMAGE_EXTS = ('.png', '.gif', '.jpg', '.jpeg', '.bmp', '.webp', '.tif', '.tiff', '.ico')
HIGHLIGHT_COLOR = '#3E8ED0'       # drop-target tint, the same in every app (blended HIGHLIGHT_MIX into the element's own background)
HIGHLIGHT_MIX = 0.35
MAX_CONTENTS_BYTES = 5_000_000    # CONTENTS policy refuses files bigger than this
WINDOW = None                     # key of a DropEvent for a drop on the window background (not on a registered element)


class Rule:
    """How one element (or one element type) treats a drop. All arguments are keyword-only."""
    def __init__(self, *, files=PATH, text=INSERT, multiple=False, ext=None, dirs=True, sep=';', element_event=None, highlight=True):
        self.files = files                    # PATH | CONTENTS | IMAGE | EVENT_ONLY | None (refuse file drops)
        self.text = text                      # REPLACE | INSERT | APPEND | EVENT_ONLY | None (refuse text drops)
        self.multiple = multiple              # accept several files at once (Input/Combo join with sep; Multiline/Listbox one per line/item)
        self.ext = tuple(e.lower() for e in ext) if ext else None    # allowed extensions e.g. ('.mid', '.midi'); None = any
        self.dirs = dirs                      # accept dropped folders
        self.sep = sep                        # joiner for multiple paths in an Input/Combo (matches sg.FilesBrowse)
        self.element_event = element_event    # also send the element's own (key, value) event; None = yes if element has enable_events=True
        self.highlight = highlight            # tint the element while a drag hovers over it

    def copy(self, **changes):
        r = Rule(**self.__dict__)
        r.__dict__.update(changes)
        return r

    def __repr__(self):
        return 'Rule(' + ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items()) + ')'


# Defaults per element type. First matching isinstance wins.
DEFAULT_RULES = [
    (sg.Input,     Rule(files=PATH, text=REPLACE, multiple=False)),
    (sg.Combo,     Rule(files=PATH, text=REPLACE, multiple=False)),
    (sg.Multiline, Rule(files=PATH, text=INSERT, multiple=True)),
    (sg.Listbox,   Rule(files=PATH, text=APPEND, multiple=True)),
    (sg.Image,     Rule(files=IMAGE, text=None, ext=IMAGE_EXTS)),
    (sg.Graph,     Rule(files=EVENT_ONLY, text=EVENT_ONLY, multiple=True)),
    (sg.Table,     Rule(files=EVENT_ONLY, text=EVENT_ONLY, multiple=True)),
    (sg.Tree,      Rule(files=EVENT_ONLY, text=EVENT_ONLY, multiple=True)),
    (sg.Button,    Rule(files=PATH, text=None)),                            # Browse-type buttons only; the drop is forwarded to the target
]
WINDOW_RULE = Rule(files=EVENT_ONLY, text=EVENT_ONLY, multiple=True, highlight=False)

_BROWSE_TYPES = (sg.BUTTON_TYPE_BROWSE_FILE, sg.BUTTON_TYPE_BROWSE_FILES, sg.BUTTON_TYPE_BROWSE_FOLDER, sg.BUTTON_TYPE_SAVEAS_FILE)


def enable(window: sg.Window, rules=None, skip=(), window_rule=WINDOW_RULE, on_drop_callback=None):
    """
    Make every input-type element of a finalized window a drop target with the standard behaviour.

    :param window:            Finalized window
    :type window:             (sg.Window)
    :param rules:             {element_key or element class: Rule or dict of Rule kwargs} overriding DEFAULT_RULES; value None removes the element
    :type rules:              (dict | None)
    :param skip:              keys of elements that must not accept drops
    :type skip:               (iterable)
    :param window_rule:       Rule for drops on the window background (None = window background refuses drops)
    :type window_rule:        (Rule | None)
    :param on_drop_callback:  callback(drop_event) run before the default action; return False to cancel it (event is still sent)
    :type on_drop_callback:   (callable | None)
    :return:                  number of targets registered
    :rtype:                   (int)
    """
    TkinterDnD._require(window.TKroot)
    rules = rules or {}
    count = 0
    for elem in window.element_list():
        if elem.key in skip or elem.widget is None:
            continue
        rule = _rule_for(elem, rules)
        if rule is None:
            continue
        if isinstance(elem, sg.Button) and (elem.BType not in _BROWSE_TYPES or _browse_target(elem) is None):
            continue
        _register_with_rule(window, elem, rule, on_drop_callback)
        count += 1
    if window_rule is not None:
        _register_with_rule(window, None, _as_rule(window_rule), on_drop_callback)
        count += 1
    return count


def target(window: sg.Window, element, rule=None, on_drop_callback=None):
    """Register a single element (key or Element) with a Rule, e.g. to add/re-register one target after enable()."""
    TkinterDnD._require(window.TKroot)
    elem = window[element] if not isinstance(element, sg.Element) else element
    _register_with_rule(window, elem, _as_rule(rule) if rule else _rule_for(elem, {}) or Rule(), on_drop_callback)


def untarget(window: sg.Window, element):
    """Stop an element (key or Element) from accepting drops."""
    elem = window[element] if not isinstance(element, sg.Element) else element
    try:
        elem.widget.drop_target_unregister()
    except Exception:
        pass


# ------------------------------------------------------------ internals -------------------------------------------------------------------
def _as_rule(r):
    return r if isinstance(r, Rule) else Rule(**r)


def _rule_for(elem, rules):
    try:
        if elem.key in rules:
            return _as_rule(rules[elem.key]) if rules[elem.key] is not None else None
    except TypeError:
        pass                                                  # unhashable key
    for cls, rule in rules.items():
        if isinstance(cls, type) and isinstance(elem, cls):
            return _as_rule(rule) if rule is not None else None
    for cls, rule in DEFAULT_RULES:
        if isinstance(elem, cls):
            return rule
    return None


def _browse_target(button):
    try:
        return button._find_target()[0]
    except Exception:
        return None


def _resolve(elem, rule):
    """A Browse-type button hands the drop to its target element, using the target's rule (FilesBrowse -> multiple)."""
    if isinstance(elem, sg.Button):
        tgt = _browse_target(elem)
        if tgt is None:
            return None, rule
        tgt_rule = _rule_for(tgt, {}) or Rule()
        return tgt, tgt_rule.copy(multiple=tgt_rule.multiple or elem.BType == sg.BUTTON_TYPE_BROWSE_FILES)
    return elem, rule


def _register_with_rule(window, elem, rule, on_drop_callback):
    widget = window.TKroot if elem is None else elem.widget
    if rule.files and rule.text:
        widget.drop_target_register(DND_ALL)
    elif rule.files:
        widget.drop_target_register(DND_FILES)
    elif rule.text:
        widget.drop_target_register(DND_TEXT)
    else:
        return
    state = {'saved_bg': None}
    widget.dnd_bind('<<DropEnter>>', lambda e: _enter(widget, elem, rule, e, state))
    widget.dnd_bind('<<DropPosition>>', lambda e: _accept(widget, elem, rule, e))
    widget.dnd_bind('<<DropLeave>>', lambda e: _unhighlight(widget, state))
    widget.dnd_bind('<<Drop>>', lambda e: _on_drop_rule(window, elem, widget, rule, e, state, on_drop_callback))


def _split_files(widget, data):
    try:
        raw = widget.tk.splitlist(data)
    except Exception:
        raw = _reformat_filenames(data).split(',')
    return [os.path.normpath(p) for p in raw if p]


def _is_files_type(tkdnd_type):
    return tkdnd_type in (CF_HDROP, DND_FILES, TK_DROP_TYPE_URI_LIST)


def _files_ok(rule, files):
    """True when the dropped files satisfy the rule (ext / dirs / multiple)."""
    if not files or (len(files) > 1 and not rule.multiple and rule.files in (CONTENTS, IMAGE)):
        return False
    for f in files:
        if os.path.isdir(f):
            if not rule.dirs:
                return False
        elif rule.ext and os.path.splitext(f)[1].lower() not in rule.ext:
            return False
    return True


def _accept(widget, elem, rule, event):
    """Return COPY (drop allowed -> "+" cursor) or REFUSE_DROP (no-entry cursor)."""
    try:
        if str(widget.cget('state')) == 'disabled':
            return REFUSE_DROP
    except Exception:
        pass
    types = tuple(getattr(event, 'types', ()) or ()) + tuple(getattr(event, 'commonsourcetypes', ()) or ())
    is_files = any(_is_files_type(t) for t in types)
    if is_files and not rule.files:
        return REFUSE_DROP
    if not is_files and types and not rule.text:
        return REFUSE_DROP
    data = getattr(event, 'data', '')
    if is_files and data and not _files_ok(_resolve(elem, rule)[1], _split_files(widget, data)):     # Windows supplies the data while hovering
        return REFUSE_DROP
    return COPY


def _enter(widget, elem, rule, event, state):
    action = _accept(widget, elem, rule, event)
    if action != REFUSE_DROP and rule.highlight:
        _highlight(widget, state)
    return action


def _highlight(widget, state):
    try:
        bg = widget.cget('background')
        r, g, b = (v >> 8 for v in widget.winfo_rgb(bg))
        hr, hg, hb = int(HIGHLIGHT_COLOR[1:3], 16), int(HIGHLIGHT_COLOR[3:5], 16), int(HIGHLIGHT_COLOR[5:7], 16)
        mix = lambda a, h: int(a + (h - a) * HIGHLIGHT_MIX)
        state['saved_bg'] = bg
        widget.configure(background=f'#{mix(r, hr):02x}{mix(g, hg):02x}{mix(b, hb):02x}')
    except Exception:
        state['saved_bg'] = None                              # ttk widgets (Combo, Table, Tree) have no plain background option


def _unhighlight(widget, state):
    if state['saved_bg'] is not None:
        try:
            widget.configure(background=state['saved_bg'])
        except Exception:
            pass
        state['saved_bg'] = None


def _on_drop_rule(window, elem, widget, rule, event, state, on_drop_callback):
    """<<Drop>> handler for rule-registered targets: filter, build the DropEvent, apply the default action, send the event."""
    _unhighlight(widget, state)
    elem, rule = _resolve(elem, rule)
    if _is_files_type(event.type):
        files = _split_files(widget, event.data)
        if not _files_ok(rule, files) or rule.files is None:
            return REFUSE_DROP
        if not rule.multiple and rule.files == PATH and len(files) > 1:
            files = files[:1]                                 # single-value elements take the first file only
        drop = DropEvent(window, elem.key if elem else WINDOW, elem, DROP_TYPE_FILES, event.type, files=files, rule=rule)
        value = ','.join(files)
    else:
        if rule.text is None:
            return REFUSE_DROP
        text = event.data if isinstance(event.data, str) else str(event.data)
        drop_type = DROP_TYPE_TEXT if event.type in (CF_TEXT, CF_UNICODETEXT, DND_TEXT, TK_DROP_TYPE_UTF8_STRING) else DROP_TYPE_UNKNOWN
        drop = DropEvent(window, elem.key if elem else WINDOW, elem, drop_type, event.type, text=text, rule=rule)
        value = text
    if on_drop_callback is None or on_drop_callback(drop) is not False:
        try:
            _apply(elem, drop)
        except Exception as e:
            print('psgdnd: default action failed:', e)
    window.write_event_value(drop, value)
    return COPY


def _apply(elem, drop):
    rule = drop.rule
    if elem is None:
        return
    if drop.files:
        if rule.files == EVENT_ONLY:
            return
        if rule.files == IMAGE:
            _put_image(elem, drop.file)
        elif rule.files == CONTENTS:
            _put_text(elem, rule, ''.join(_read_text(f) for f in drop.files if os.path.isfile(f)))
        elif isinstance(elem, (sg.Input, sg.Combo)):
            _put_text(elem, rule, rule.sep.join(drop.files) if rule.multiple else drop.file)
        elif isinstance(elem, sg.Listbox):
            elem.update(values=list(elem.get_list_values()) + drop.files)
        else:
            _put_text(elem, rule, '\n'.join(drop.files) + '\n')
    else:
        if rule.text == EVENT_ONLY:
            return
        _put_text(elem, rule, drop.text)
    drop.applied = True
    if rule.element_event or (rule.element_event is None and getattr(elem, 'ChangeSubmits', False)):
        try:
            elem.ParentForm.write_event_value(elem.key, elem.get())
        except Exception:
            pass


def _put_text(elem, rule, text):
    mode = rule.text or REPLACE
    if isinstance(elem, sg.Listbox):
        items = [line for line in text.splitlines() if line.strip()]
        elem.update(values=items if mode == REPLACE else list(elem.get_list_values()) + items)
    elif isinstance(elem, sg.Combo):
        values = list(elem.Values)
        if text not in values:
            values.append(text)
        elem.update(value=text, values=values)
    elif isinstance(elem, sg.Multiline):
        if mode == REPLACE:
            elem.update(text)
        else:
            elem.widget.insert('insert' if mode == INSERT else 'end', text)
            elem.widget.see('insert' if mode == INSERT else 'end')
    elif isinstance(elem, sg.Input):
        if mode == REPLACE:
            elem.update(text)
        else:
            elem.widget.insert('insert' if mode == INSERT else 'end', text.replace('\n', ' '))
    else:
        elem.update(text)


def _put_image(elem, path):
    if os.path.splitext(path)[1].lower() in ('.png', '.gif'):
        elem.update(filename=path)
        return
    try:
        from PIL import Image
        import io
        with Image.open(path) as im:
            buf = io.BytesIO()
            im.convert('RGBA').save(buf, format='PNG')
        elem.update(data=buf.getvalue())
    except ImportError:
        print('psgdnd: PIL is needed to show', path)


def _read_text(path):
    if os.path.getsize(path) > MAX_CONTENTS_BYTES:
        return f'[{os.path.basename(path)}: too large to load]\n'
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def main():
    """Demo window: every default behaviour plus a few overrides, with an event log.  Run with  python -m psgdnd"""
    K_PATH, K_FILES, K_FOLDER, K_SEARCH, K_EDITOR = '-PATH-', '-FILES-', '-FOLDER-', '-SEARCH-', '-EDITOR-'
    K_LIST, K_COMBO, K_IMAGE, K_GRAPH, K_LOG = '-LIST-', '-COMBO-', '-IMAGE-', '-GRAPH-', '-LOG-'
    lbl = dict(size=(24, 1), justification='r')
    targets = [[sg.Text('One file (.txt .md .py only)', **lbl), sg.Input(key=K_PATH, size=40, enable_events=True), sg.FileBrowse()],
               [sg.Text('Many files ( ; joined )', **lbl), sg.Input(key=K_FILES, size=40), sg.FilesBrowse()],
               [sg.Text('Folder', **lbl), sg.Input(key=K_FOLDER, size=40), sg.FolderBrowse()],
               [sg.Text('Search (drops refused)', **lbl), sg.Input(key=K_SEARCH, size=40)],
               [sg.Text('Editor (file -> contents)', **lbl), sg.Multiline(key=K_EDITOR, size=(48, 6))],
               [sg.Text('Playlist (paths appended)', **lbl), sg.Listbox(values=[], key=K_LIST, size=(48, 5))],
               [sg.Text('Combo (path added)', **lbl), sg.Combo(values=['(drop a file here)'], default_value='(drop a file here)', key=K_COMBO, size=46)],
               [sg.Text('Image (picture files)', **lbl), sg.Image(key=K_IMAGE, size=(200, 120), background_color='#2b2b2b'),
                sg.Text('Graph (event only)'), sg.Graph((200, 120), (0, 0), (200, 120), key=K_GRAPH, background_color='#1f3b52')]]
    log = [[sg.Text('Event log - every drop is a DropEvent object; values[event] is the text or the comma-joined paths', font='_ 10 bold')],
           [sg.Multiline(key=K_LOG, size=(80, 30), font='Courier 9', autoscroll=True, write_only=True, disabled=True, background_color='black', text_color='lime', expand_y=True, expand_x=True)],]
    layout = [[sg.Column(targets, vertical_alignment='top'), sg.VSeparator(), sg.Column(log)]]
    window = sg.Window(f'psgdnd {version} demo - drag files, folders and text onto the elements', layout, finalize=True)
    rules = {K_PATH: Rule(ext=('.txt', '.md', '.py')), K_FILES: Rule(multiple=True), K_EDITOR: Rule(files=CONTENTS, text=INSERT)}
    window[K_LOG].print(f'{enable(window, rules=rules, skip=[K_SEARCH])} drop targets registered', text_color='white')
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif is_drop_event(event):
            window[K_LOG].print(f'{event}', text_color='orange')
            window[K_LOG].print(f'   values[event] = {values[event]!r}')
            if event.key == K_GRAPH:
                window[K_GRAPH].erase()
                for i, f in enumerate(event.files[:5]):
                    window[K_GRAPH].draw_text(os.path.basename(f), (100, 105 - i * 22), color='white', font='_ 10')
        else:
            window[K_LOG].print(f'{event!r}  {values.get(event)!r}')
    window.close()


if __name__ == '__main__':
    main()