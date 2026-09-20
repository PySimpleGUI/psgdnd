"""
psgdnd_demo.py — standalone demo of drag & drop with the psgdnd package.

    pip install psgdnd            (installs tkinterdnd2 too)

Drag files, folders and text from anywhere (File Explorer, Finder, a browser, another app) and drop them on the elements.
Every drop is applied to the element by psgdnd's default rules and reported in the event log as a DropEvent.
"""
import os
import PySimpleGUI as sg
import psgdnd

K_PATH = '-PATH-'
K_FILES = '-FILES-'
K_FOLDER = '-FOLDER-'
K_SEARCH = '-SEARCH-'
K_EDITOR = '-EDITOR-'
K_LIST = '-LIST-'
K_COMBO = '-COMBO-'
K_IMAGE = '-IMAGE-'
K_GRAPH = '-GRAPH-'
K_LOG = '-LOG-'
K_CLEAR = '-CLEAR-'
K_STATUS = '-STATUS-'

# ---- Drag & drop rules: only the exceptions are listed; everything else gets psgdnd's default for its element type ------------------------
DND_RULES = {K_PATH: psgdnd.Rule(ext=('.txt', '.md', '.py')),                   # one file, only these extensions (no-entry cursor for others)
             K_FILES: psgdnd.Rule(multiple=True),                               # several files, joined with ';' like sg.FilesBrowse
             K_EDITOR: psgdnd.Rule(files=psgdnd.CONTENTS, text=psgdnd.INSERT)}  # a dropped text file is loaded; dropped text goes at the cursor
DND_SKIP = [K_SEARCH]                                                           # never a drop target


def main():
    sg.theme('DarkGrey13')
    lbl = dict(size=(26, 1), justification='r')
    targets = [[sg.Text('One file (.txt .md .py only)', **lbl), sg.Input(key=K_PATH, size=40, enable_events=True), sg.FileBrowse()],
               [sg.Text('Many files ( ; joined )', **lbl), sg.Input(key=K_FILES, size=40), sg.FilesBrowse()],
               [sg.Text('Folder', **lbl), sg.Input(key=K_FOLDER, size=40), sg.FolderBrowse()],
               [sg.Text('Search (drops refused)', **lbl), sg.Input(key=K_SEARCH, size=40)],
               [sg.Text('Editor (file → contents)', **lbl), sg.Multiline(key=K_EDITOR, size=(48, 6))],
               [sg.Text('Playlist (paths appended)', **lbl), sg.Listbox(values=[], key=K_LIST, size=(48, 5))],
               [sg.Text('Combo (path added + selected)', **lbl), sg.Combo(values=['(drop a file here)'], default_value='(drop a file here)', key=K_COMBO, size=46)],
               [sg.Text('Image (picture files)', **lbl), sg.Image(key=K_IMAGE, size=(200, 120), background_color='#2b2b2b'),
                sg.Text('Graph (event only)'), sg.Graph((200, 120), (0, 0), (200, 120), key=K_GRAPH, background_color='#1f3b52')]]
    log = [[sg.Text('Event log — every drop is a DropEvent; values[event] is the text or the comma-joined paths', font='_ 10 bold')],
           [sg.Multiline(key=K_LOG, size=(78, 30), font='Courier 9', autoscroll=True, write_only=True, disabled=True,  background_color='black', text_color='lime')],
           [sg.Button('Clear log', key=K_CLEAR), sg.Text('', key=K_STATUS, expand_x=True)]]
    layout = [[sg.Column(targets, vertical_alignment='top'), sg.VSeparator(), sg.Column(log, vertical_alignment='top')]]
    window = sg.Window(f'psgdnd {psgdnd.__version__} demo — drag files, folders and text onto the elements', layout, finalize=True, resizable=True)

    count = psgdnd.enable(window, rules=DND_RULES, skip=DND_SKIP)              # <-- the whole drag & drop integration
    window[K_STATUS].update(f'{count} drop targets registered', text_color='white')

    log_widget = window[K_LOG].widget                                            # standard keyboard shortcuts for the scrollable log
    scroll_keys = {'Up': ('scroll', -1, 'units'), 'Down': ('scroll', 1, 'units'), 'Prior': ('scroll', -1, 'pages'), 'Next': ('scroll', 1, 'pages'),
                   'Home': ('moveto', 0), 'End': ('moveto', 1)}
    for keysym, cmd in scroll_keys.items():
        window.TKroot.bind(f'<{keysym}>', lambda e, c=cmd: log_widget.yview(*c))
    window.TKroot.bind('<Escape>', lambda e: window.write_event_value(sg.WIN_CLOSED, None))

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == K_CLEAR:
            window[K_LOG].update('')
        elif psgdnd.is_drop_event(event):                                        # <-- one branch handles every drop
            window[K_LOG].print(f'{event}', text_color='orange')
            window[K_LOG].print(f'   values[event] = {values[event]!r}')
            if event.key == K_GRAPH:                                             # EVENT_ONLY target: the app decides what a drop means
                window[K_GRAPH].erase()
                for i, f in enumerate(event.files[:5]):
                    window[K_GRAPH].draw_text(os.path.basename(f), (100, 105 - i * 22), color='white', font='_ 10')
            elif event.key is None:                                              # dropped on the window background
                window[K_LOG].print('   (window background — nothing registered under the cursor)', text_color='orange')
        elif event == K_PATH:                                                    # the Input's own event still fires after a drop
            window[K_LOG].print(f'{event}  value changed → {values[K_PATH]}', text_color='orange')
        else:
            window[K_LOG].print(f'{event!r}')
    window.close()


if __name__ == '__main__':
    main()
