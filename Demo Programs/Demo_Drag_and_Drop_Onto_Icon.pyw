import base64
import io
import os
import random
import webbrowser
from typing import Tuple, Union
from PIL import Image
import PySimpleGUI as sg
import psgdnd as dnd
from pathlib import Path
from googletrans import Translator

"""

Creates what appears to be an icon on your desktop, but is in reality a PySimpleGUI program.

Ways to interface with the icon include:
* Right click menu
* Double click of icon
* Dropping files onto icon
* Dropping text onto icon

Features:
* Settings window that includes:
    - JPG quality level
    - Alpha channel setting for the icon (creates a dimmed effect)
    - Icon filename and Base64Png - can specify the icon through the settings rather than changing the code
* When JPG, PNG, GIF, ICO images are dropped onto icon, a popup window of options is shown.
    - Images can be converted to PNG, JPG, GIF, ICO
    - An image can be converted to base64 encoded PNG. The result is put onto clipboard
* If the icon is double clicked, it opens the PySimpleGUI github page
* When other file types is dropped onto icon, a popup is shown with the list of files
* When text is dropped onto the icon, a popup of text options is displayed.  You can
    - Translate text into English and put on clipboard
    - Translate text into Spanish and put on clipboard
* Toggle keep on top using right click menu

Requires:
    PIL for image format conversion
    Google Translate to translate text.  To install run:
        pip install googletrans==3.1.0a0

Copyright 2026 PySimpleGUI. All rights reserved.
"""


version = '6.0.1'
__version__ = version.split()[0]


"""
Changelog since last major release

6.0     9-Jun-2026      Initial release
6.0.1   13-Jun-2026     Added image type converstion, English/Spanash translate
"""



"""
                    dP     dP   oo                            
                    88     88                                 
.d8888b. .d8888b. d8888P d8888P dP 88d888b. .d8888b. .d8888b. 
Y8ooooo. 88ooood8   88     88   88 88'  `88 88'  `88 Y8ooooo. 
      88 88.  ...   88     88   88 88    88 88.  .88       88 
`88888P' `88888P'   dP     dP   dP dP    dP `8888P88 `88888P' 
                                                 .88          
                                             d8888P
"""

KEY_REMOVABLE_FOLDER = '-REMOVABLE FOLDER-'
KEY_JPG_QUALITY = '-JPG QUALITY-'
KEY_ALPHA = '-ALPHA-'
KEY_PNG_ICON_FILENAME= '-ICON-'
KEY_PNG_ICON_BASE64 = '-ICON-BASE64-'

def show_settings_window(location:Tuple[int, int]):
    """
    Shows the settings window

    :param location:        Location of the icon window
    :type location:         Tuple[int, int]
    """
    layout = [[sg.T('Drag and Drop Icon Settings', font='_ 15')],
              [sg.Input(setting='', key=KEY_REMOVABLE_FOLDER, s=40), sg.T('Path to Removable Disk')],
              [sg.Input(setting=0, justification='r', s=3, k=KEY_JPG_QUALITY), sg.T('%  Default JPG quality', p=(None, (0,2)))],
              [sg.Input(setting=10, justification='r', s=3, k=KEY_ALPHA), sg.T('Alpha channel for icon (1-10)')],
              [sg.Input(setting='', justification='r', s=40, k=KEY_PNG_ICON_FILENAME), sg.T('Icon filename')],
              [sg.Input(setting='', justification='r', s=40, k=KEY_PNG_ICON_BASE64), sg.T('Icon Base64')],
              [sg.Push(), sg.OK(), sg.Cancel()]]

    window = sg.Window('Settings', layout, location=location, keep_on_top=True, no_titlebar=True, finalize=True)
    window.settings_restore()
    window.refresh()
    window.move(location[0]-window.size[0]-10, location[1]-window.size[1])
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == 'OK':
            if values[KEY_PNG_ICON_BASE64].startswith(("b'", 'b"')):        # if the bytestring included quotes, strip off the quotes
                values[KEY_PNG_ICON_BASE64] = values[KEY_PNG_ICON_BASE64][2:-1]    # remove 2 chars from the front, 1 from the end
            window.settings_save(values)
            break
    window.close()




"""
oo                                       
                                         
dP 88d8b.d8b. .d8888b. .d8888b. .d8888b. 
88 88'`88'`88 88'  `88 88'  `88 88ooood8 
88 88  88  88 88.  .88 88.  .88 88.  ... 
dP dP  dP  dP `88888P8 `8888P88 `88888P' 
                            .88          
                        d8888P           
                                                               oo                   
                                                                                    
88d888b. 88d888b. .d8888b. .d8888b. .d8888b. .d8888b. .d8888b. dP 88d888b. .d8888b. 
88'  `88 88'  `88 88'  `88 88'  `"" 88ooood8 Y8ooooo. Y8ooooo. 88 88'  `88 88'  `88 
88.  .88 88       88.  .88 88.  ... 88.  ...       88       88 88 88    88 88.  .88 
88Y888P' dP       `88888P' `88888P' `88888P' `88888P' `88888P' dP dP    dP `8888P88 
88                                                                              .88 
dP                                                                          d8888P
"""

def convert_formats(input_file:str, encode_format:str='PNG') -> bool:
    """
    Converts an image file to the specified format (PNG or JPEG).

    :param input_file:          The path to the input image file.
    :type input_file:           str
    :param encode_format:       The target format for the image conversion ('PNG' or 'JPEG'), defaults to 'PNG'.
    :type encode_format:        str
    :return:                    True if the file was successfully converted and saved, False if the target file already exists.
    :rtype:                     bool
    """
    jpg_quality = None

    image = Image.open(input_file)

    if encode_format.lower() in ('jpeg', 'jpg'):
        image = image.convert("RGB")
        encode_format = 'jpg'
        jpg_quality = int(sg.user_settings_get_entry(KEY_JPG_QUALITY, 0))
    path = Path(input_file)
    output_file = path.with_name(path.stem).with_suffix('.'+encode_format.lower())
    # print(f'{output_file=}')
    if not os.path.exists(output_file):
        if jpg_quality:
            image.save(output_file, quality=jpg_quality)
        else:
            image.save(output_file)
    else:
        return False
    return True


def encode_image_base64(input_file):
    """
    Encodes a PNG image file into a base64 string.

    :param input_file:          The path to the input PNG image file.
    :type input_file:           str
    :return:                    The base64 encoded byte string of the image, or None if the file is not a PNG.
    :rtype:                     bytes or None
    """

    if not input_file.lower().endswith('.png'):
        print('Error - Can only base64 encode PNG files')
        return None

    image = Image.open(input_file)

    # encode a PNG formatted version of image into BASE64
    with io.BytesIO() as bio:
        image.save(bio, format='PNG')
        contents = bio.getvalue()
        encoded = base64.b64encode(contents)

    display_message(f'B64PNG encoded {input_file}')
    return encoded


"""
                                                           oo          
                                                                       
88d888b. .d8888b. 88d888b. dP    dP 88d888b.    dP  dP  dP dP 88d888b. 
88'  `88 88'  `88 88'  `88 88    88 88'  `88    88  88  88 88 88'  `88 
88.  .88 88.  .88 88.  .88 88.  .88 88.  .88    88.88b.88' 88 88    88 
88Y888P' `88888P' 88Y888P' `88888P' 88Y888P'    8888P Y8P  dP dP    dP 
88                88                88                                 
dP                dP                dP
"""


def image_popup(filenames:str, location):
    """
      Displays a popup window with options for the dropped files.  Performs chosen operation.

      If image files are dropped, options to convert to JPG, PNG, or Base64 PNG are shown.d
      For other file types, a list of the dropped files is displayed.

      :param filenames:         A comma-separated string of the dropped file paths.
      :type filenames:          str
      :param location:          The (x, y) coordinates of the icon window
      :type location:           Tuple[int, int] | Tuple[None, None]
    """
    file_list = filenames.split(',')
    # if len(file_list) == 1:                 # If single item, see if it's a flash drive for photos
    #     sg.popup(f'Single file = {file_list[0]}')
    actions = ('Convert to JPG', 'Convert to PNG', 'Convert to GIF', 'Convert to ICO', 'Convert to Base64-PNG', 'Cancel')
    image_files = all(file.endswith(('jpeg', 'jpg', 'png', 'gif', 'ico')) for file in file_list)
    if image_files:
        button_size = max(len(a) for a in actions)
        layout = [[sg.Text('Images dropped - What do you want to do with them?')],
                  [sg.Text('\n'.join(file_list))],
                  [[sg.Button(action, s=button_size)] for action in actions],]
        convert_window = sg.Window('Image actions', layout, location=location, keep_on_top=True, no_titlebar=True, finalize=True)
        convert_window.refresh()
        convert_window.move(location[0] - convert_window.size[0], location[1] - convert_window.size[1])
        event, values = convert_window.read(close=True)
        # Perform actions
        if event.startswith('Convert'):
            image_format = event.split()[-1]                # The image format is always at the end of the button string
            encode_only = image_format == 'Base64-PNG'      # If is basse64 format, then do a special encode
            for file in file_list:
                if encode_only:
                    sg.clipboard_set(encode_image_base64(file))
                else:
                    convert_formats(file, image_format)
                    display_message(f'Converted {file} to {image_format}')

        # sg.popup(f'Dropped files:', '\n'.join(file_list), non_blocking=True, line_width=max(len(f)+1 for f in file_list), location=location, no_titlebar=True)

def text_popup(text:str, location):
    """
      Displays a popup window with options for dropped text.  Performs chosen operation.

      :param text:              The text dropped onto the icon
      :type text:               str
      :param location:          The (x, y) coordinates of the icon window
      :type location:           Tuple[int, int] | Tuple[None, None]
    """
    actions = ('Translate to English', 'Translate to Spanish',  'Cancel')
    lang_to_dest = {'Spanish' : 'es', 'English' : 'en'}
    button_size = max(len(a) for a in actions)
    layout = [[sg.Text('Text dropped - What do you want to do with it?')],
              [sg.Text()],
              [[sg.Button(action, s=button_size)] for action in actions],]
    convert_window = sg.Window('Text actions', layout, location=location, keep_on_top=True, no_titlebar=True, finalize=True)
    convert_window.refresh()
    convert_window.move(location[0] - convert_window.size[0], location[1] - convert_window.size[1])
    event, values = convert_window.read(close=True)
    # Perform actions
    if event.startswith('Translate'):
        lang = event.split()[-1]                # The image format is always at the end of the button string
        # Translate the text; dest='es' specifies Spanish as the destination language
        translator = Translator()

        translation = translator.translate(text, dest=lang_to_dest[lang])
        display_message(f'Translated to {lang}')
        sg.clipboard_set(translation.text)

        # sg.popup(f'Dropped files:', '\n'.join(file_list), non_blocking=True, line_width=max(len(f)+1 for f in file_list), location=location, no_titlebar=True)

def display_message(message='')->None:
    """
    Displays a message in a small window like a tooltip
    :param message:         The text message to display
    :type message:          str
    """
    location = display_message.window.current_location()
    location =  (location[0]-len(message)*2, location[1]+70)
    # if location is not None:
    #     location = (location[0]-len(message)*2, location[1]+70)
    sg.popup_quick_message(message, font='_ 10', location=location,  background_color="#ffffe0",text_color='black', auto_close_duration=5)


"""
                    oo          
                                
88d8b.d8b. .d8888b. dP 88d888b. 
88'`88'`88 88'  `88 88 88'  `88 
88  88  88 88.  .88 88 88    88 
dP  dP  dP `88888P8 dP dP    dP

"""
def main():

    # get settings from settings file
    b64icon = sg.user_settings_get_entry(KEY_PNG_ICON_BASE64, None)
    pngicon = sg.user_settings_get_entry(KEY_PNG_ICON_FILENAME, None)
    keep_on_top = sg.user_settings_get_entry('-keep on top-', False)

    # set the icon to use
    if b64icon:
        icon = bytes(b64icon, 'utf-8')
    elif pngicon:
        icon = pngicon
    else:
        icon = sg.EMOJI_BASE64_COOL

    #------- GUI definition & setup --------#

    RIGHT_CLICK_MENU = ['', ['Settings', 'Edit Me', f'Keep on top is {"ON" if keep_on_top else "OFF"}', 'Version', 'Exit']]
    layout = [[sg.Image(source=icon, key='-IMAGE-', p=0, background_color='black', enable_events=True)]]

    window = sg.Window('Desktop Icon Demo', layout, element_justification='center', resizable=True, no_titlebar=True, right_click_menu=RIGHT_CLICK_MENU, margins=(0,0), grab_anywhere=True, auto_save_location=True, keep_on_top=keep_on_top,  finalize=True, alpha_channel=int(sg.user_settings_get_entry(KEY_ALPHA, 10))/10)

    display_message.window=window

    dnd.register_element_dnd(window['-IMAGE-'], window, dnd.DROP_TYPE_ALL)        # The one line of code needed to add drag and drop

    window['-IMAGE-'].bind('<Double-Button-1>', '+DOUBLE_CLICK+')

    #------------ The Event Loop ------------#
    while True:
        event, values = window.read()
        # print(event, values)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        if dnd.is_drop_event(event):                            # Drag and Drop event
            dnd_event: dnd.DropEvent = event
            if dnd_event.drop_type == dnd.DROP_TYPE_FILES:      # If files are dropped, show a window with choices of what to do with them
                image_popup(values[event], window.current_location())
            elif dnd_event.drop_type == dnd.DROP_TYPE_TEXT:      # If files are dropped, show a window with choices of what to do with them
                text_popup(values[event], window.current_location())
        if event == '-IMAGE-+DOUBLE_CLICK+':                    # Add your double-click action here... such as launching another program
            loc = window.current_location()
            loc = (loc[0]-40, loc[1]-50)
            webbrowser.open(r'https://github.PySimpleGUI.com')
        elif event == 'Settings':
            display_message('Opening settings')
            show_settings_window(window.current_location())
        elif event in ('Keep on top is OFF', 'Keep on top is ON'):          # Keep on top right click menu
            window.keep_on_top_set() if event.endswith('OFF') else window.keep_on_top_clear()
            RIGHT_CLICK_MENU[1][1] = f'Keep on top is {"ON" if event.endswith("OFF") else "OFF"}'
            window['-IMAGE-'].set_right_click_menu(RIGHT_CLICK_MENU)
            sg.user_settings_set_entry('-keep on top-', event.endswith("OFF"))
        elif event == 'Version':
            sg.popup_scrolled(sg.get_versions(), f'This Program: {__file__}', keep_on_top=True, non_blocking=True, button_justification='right')
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    window.close()

if __name__ == '__main__':
    main()