import base64
import io
import os
from typing import Tuple, Union, List, Any, Dict
import ast

try:
    import tinify
    tinify_available = True
except:
    tinify_available = False
    print('Tinify is not available.  Run "pip install tinify" if you want to use tinify.')


from PIL import Image
import PySimpleGUI as sg
import psgdnd as dnd
from pathlib import Path
from packaging.version import Version

try:
    from googletrans import Translator
    translate_installed = True
except:
    print('*** WARNING - unable to import from the googletrans package. You will not be able to access Translation features. ***')
    translate_installed = False

"""
    
    Creates what appears to be an icon on your desktop, but is in reality a PySimpleGUI program.
    
    NOTE - You need to use  PySimpleGUI version 6.2 with this program.  6.2 has the ability to set any color of border for Frame elements
    
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
    * Shows various dialog using a mini-window that's designed into this application
    
    Requires:
        PIL for image format conversion
        Google Translate to translate text.  To install run:
            pip install googletrans==3.1.0a0
    
    Copyright 2026 PySimpleGUI. All rights reserved.
"""


version = '6.2.7'
__version__ = version.split()[0]

"""
Changelog since last major release

6.0     9-Jun-2026      Initial release
6.1     14-Jun-2026     Addition of mini windows, made googletrans an optional package,  error checking, bug fixes
6.2     14-Jun-2026     Added checking that the PySimpleGUI version is at least 6.2.  If not, offer to install it
6.2.1   25-Jun-2026     Added support for converting to WebP image format
6.2.2   25-Jun-2026     Show program and modules versions in the settings window
                        Added support for resizing the images using absolute pixels or %
                        Show the image size and dimensions along with filename
6.2.3   25-Jun-2026     Added ability to both convert to base64 PNG and resize the image (first)
                        Better settings save by adding close attempted events to the window so that there are values to save
                        New brighter figlets          
6.2.4   27-Jun-2026     Change how popup MiniWindows are created. Using the new Window-Anchoring fearures added to PSG 6.2.8   
                        Added anchoring to settings so users can easily change them
                        Added more typedefs
                        Added globals class for the global settings... global state without global variables 🙂
                        Changed the pip install option to get the latest from GitHub rather than PyPI since Window Anchorings isn't on PyPI
6.2.5    5-Jul-2026     Added double-click action to take to settings 
                        Added tinifying PNG files.  Used when converting to a PNG file or encoding the base64 PNG. User needs a (free) API key
                        Added base64 mouseover image to the settings.  Mouseover will easily show the desktop icon isn't really an icon but an application.
6.2.6   12-Jul-2026     Added to text drop window the ability to decode and view a base64 encoded png image
6.2.7   13-Jul-2026     Fixed storing and using bytestrings.  Didn't know to use ast.literal_eval to convert from string to bytestring

"""


# ---------- CONSTANTS ----------
KEY_REMOVABLE_FOLDER = '-REMOVABLE FOLDER-'
KEY_JPG_QUALITY = '-JPG QUALITY-'
KEY_ALPHA = '-ALPHA-'
KEY_PNG_ICON_FILENAME= '-ICON-'
KEY_PNG_ICON_BASE64 = '-ICON-BASE64-'
KEY_PNG_MOUSEOVER_ICON_BASE64 = '-MOUSEOVER-ICON-BASE64-'
KEY_DOUBLE_CLICK_COMMAND = '-DOUBLE CLICK-'
KEY_TINIFY_API_KEY = '-TINIFY KEY-'
KEY_ICON_ANCHOR = '-ICON ANCHOR-'
KEY_WINDOW_ANCHOR = '-WINDOW ANCHOR-'

DEFAULT_JPG_QUALITY = 95

# Definitions of anchoring when showing a MiniWindow popup
# Default is currently to show the MiniWindow popup with lower right corner of the window being
#   placed at the upper left corner of the Drop Icon
# First define the anchor point ON the ICON that the MiniWindow will be created
DEFAULT_ICON_POPUP_ANCHOR = 'Upper Left'    # Where on the drop icon should windows be anchored
# Then define the anchor point ON the MINIWINDOW
DEFAULT_POPUP_ANCHOR = 'Lower Right'        # The location on the window to anchor when creating

anchor_choices = {'Center': sg.WIN_ANCHOR_CENTER, 'Upper Left': sg.WIN_ANCHOR_UPPER_LEFT, 'Upper Right': sg.WIN_ANCHOR_UPPER_RIGHT,
                  'Lower Left': sg.WIN_ANCHOR_LOWER_LEFT, 'Lower Right': sg.WIN_ANCHOR_LOWER_RIGHT}

# ------------------------------- GLOBALS -------------------------------
class G:
    # Current anchor settings that will be used when creating MiniWindows
    icon_popup_anchor: str = anchor_choices[sg.user_settings_get_entry('-ICON ANCHOR-', DEFAULT_ICON_POPUP_ANCHOR)]
    popup_anchor: str = anchor_choices[sg.user_settings_get_entry('-WINDOW ANCHOR-', DEFAULT_POPUP_ANCHOR)]
    tinify_api_key: str = None
    mouseover_icon:bytes = None
    icon = None                         # Icon currently being used

#   ███████╗███████╗████████╗████████╗██╗███╗   ██╗ ██████╗ ███████╗
#   ██╔════╝██╔════╝╚══██╔══╝╚══██╔══╝██║████╗  ██║██╔════╝ ██╔════╝
#   ███████╗█████╗     ██║      ██║   ██║██╔██╗ ██║██║  ███╗███████╗
#   ╚════██║██╔══╝     ██║      ██║   ██║██║╚██╗██║██║   ██║╚════██║
#   ███████║███████╗   ██║      ██║   ██║██║ ╚████║╚██████╔╝███████║
#   ╚══════╝╚══════╝   ╚═╝      ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝



def show_settings_window(location:Tuple[int, int], location_anchor=None):
    """
    Shows the settings window

    :param location:        Location of the icon window
    :type location:         Tuple[int, int]
    :param location_anchor: What part of the window should be anchored at the location
    :type location_anchor:  str
    """

    layout = [[sg.T('Drag and Drop Icon Settings', font='_ 15')],
              [sg.Input(setting=0, justification='r', s=3, k=KEY_JPG_QUALITY), sg.T('%  Default JPG quality', p=(None, (0,2)))],
              [sg.Input(setting=10, justification='r', s=3, k=KEY_ALPHA), sg.T('Alpha channel for icon (1-10)')],
              [sg.Input(setting='', placeholder='Icon image filename', placeholder_text_color='blue', placeholder_justification='c', justification='l', s=40, k=KEY_PNG_ICON_FILENAME) ],
              [sg.Input(setting='', justification='l', s=40, placeholder='Base64 PNG to use as icon',placeholder_text_color='blue', placeholder_justification='c',k=KEY_PNG_ICON_BASE64),],
              [sg.Input(setting='', justification='l', s=40, placeholder='Base64 PNG to use as mouseover', placeholder_justification='c',placeholder_text_color='blue',k=KEY_PNG_MOUSEOVER_ICON_BASE64), ],
              [sg.Input(setting='', justification='l', s=40, placeholder='Double-click action to take',placeholder_justification='c', placeholder_text_color='blue',k=KEY_DOUBLE_CLICK_COMMAND),],
              [sg.Input(setting='', justification='l',  s=40, k=KEY_TINIFY_API_KEY, placeholder='Paste Tinify API key here...', placeholder_justification='c', placeholder_text_color='blue',), ],
              [sg.Frame('Popup Anchoring',
                        [[sg.T('Location on Icon to anchor popups'), sg.Combo(values=list(anchor_choices.keys()), k=KEY_ICON_ANCHOR, setting=DEFAULT_ICON_POPUP_ANCHOR, size=(10,5), readonly=True)],
                            [sg.T('Location on popup Window to anchor to icon'), sg.Combo(values=list(anchor_choices.keys()), k=KEY_WINDOW_ANCHOR, setting=DEFAULT_POPUP_ANCHOR, size=(10,5), readonly=True)]])],
              [sg.T('Versions',font=('default', 14, 'bold'), p=0)],
              [sg.T(f'{version:6} this program', p=0)],
              [sg.T(f'{dnd.version:6} psgdnd', p=0)],
              [sg.T(f'{sg.version:6} PySimpleGUI', p=0)],
              [sg.Push(), sg.OK(), sg.Cancel()]]

    window = MiniWindow('Settings', layout, location=location, location_anchor=G.popup_anchor)

    window.settings_restore()

    while True:
        event, values  = window.read()          # type: Any, Dict
        if event in (sg.WIN_CLOSED, 'Cancel', 'Exit'):
            break
        elif event == 'OK':
            if values[KEY_PNG_MOUSEOVER_ICON_BASE64]:
                G.mouseover_icon = ast.literal_eval(values[KEY_PNG_MOUSEOVER_ICON_BASE64])
            else:
                G.mouseover_icon = None
            # saved_pngicon = sg.user_settings_get_entry(KEY_PNG_ICON_BASE64, None)
            # saved_icon_filename = sg.user_settings_get_entry(KEY_PNG_ICON_FILENAME, None)
            window.settings_save(values)
            G.icon_popup_anchor = anchor_choices[values.get(KEY_ICON_ANCHOR, DEFAULT_ICON_POPUP_ANCHOR)]
            G.popup_anchor = anchor_choices[values.get(KEY_WINDOW_ANCHOR, DEFAULT_POPUP_ANCHOR)]
            G.tinify_api_key = values[KEY_TINIFY_API_KEY]
            if tinify_available:
                tinify.key =  G.tinify_api_key
            icon_b64 = ast.literal_eval(values[KEY_PNG_ICON_BASE64]) if values[KEY_PNG_ICON_BASE64] else None
            icon_filename = values[KEY_PNG_ICON_FILENAME]
            if G.icon not in (icon_b64, icon_filename):
                G.icon = icon_b64 or icon_filename
                print(f'Set icon to {G.icon=}')
            break
    window.close()




#   ██╗███╗   ███╗ █████╗  ██████╗ ███████╗
#   ██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝
#   ██║██╔████╔██║███████║██║  ███╗█████╗
#   ██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝
#   ██║██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗
#   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
#
#   ██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗██╗███╗   ██╗ ██████╗
#   ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝██║████╗  ██║██╔════╝
#   ██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗██║██╔██╗ ██║██║  ███╗
#   ██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║██║██║╚██╗██║██║   ██║
#   ██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║██║██║ ╚████║╚██████╔╝
#   ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝

def convert_formats(input_file:str, encode_format:str='PNG', resize_percent=None, resize_w_h=(None, None), encode_to_base64=-False, tinify=False):
    """
    Converts an image file to the specified format (PNG or JPEG).

    :param input_file:          The path to the input image file.
    :type input_file:           str
    :param encode_format:       The target format for the image conversion ('PNG' or 'JPEG'), defaults to 'PNG'.
    :type encode_format:        str
    :type resize_percent:       Percentage amount to scale the image
    :param resize_percent:      in
    :param resize_w_h:          The width and height of the image to be resized
    :type resize_w_h:           Tuple[int, int] | Tuple[None, None]
    :param encode_to_base64:    Encode the image to base64 - do not write a file
    :type encode_to_base64:     bool
    :param tinify:              If True, tinify PNG files
    :type tinify:                bool
    """
    jpg_quality = None

    image = Image.open(input_file)

    if encode_format.lower() in ('jpeg', 'jpg'):
        image = image.convert("RGB")
        encode_format = 'jpg'
        try:
            jpg_quality = int(sg.user_settings_get_entry(KEY_JPG_QUALITY, DEFAULT_JPG_QUALITY))
        except:
            jpg_quality = DEFAULT_JPG_QUALITY

    w, h = image.size
    if resize_percent is None and resize_w_h == (None, None):       # if no resize is happening
        resized_image = image
        size_string = ''
    else:
        if resize_percent is not None:
            scale = resize_percent / 100
        elif resize_w_h != (None, None):
            scale = min(resize_w_h[0] / w, resize_w_h[1] / h)
        new_w, new_h = int(w * scale), int(h * scale)
        # print(f'New size will be: {new_w, new_h}')
        resized_image = image.resize((new_w, new_h), Image.LANCZOS)
        size_string = f'{new_w}x{new_h}'

    if tinify and tinify_available:
        resized_image = tinify_pil_image(resized_image)
        size_string += '_tinify'

    if encode_to_base64:
        return encode_image_base64( pil_image=resized_image)

    path = Path(input_file)
    output_file = path.with_name(path.stem + size_string + '.' + encode_format.lower())
    # print(f'{output_file=}')
    if not os.path.exists(output_file):
        if jpg_quality:
            resized_image.save(output_file, quality=jpg_quality)
        else:
            resized_image.save(output_file)
        display_message(f'Converted {input_file} to {encode_format}')

    else:
        display_message(f'Skipping overwrite {output_file}')
    return None


def tinify_pil_image(img: Image.Image) -> Image.Image:
    # 1) PIL Image -> PNG bytes in memory
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # 2) Send bytes to Tinify
    result = tinify.from_buffer(png_bytes)  # compress buffer [web:59][web:77]

    # 3) Get compressed bytes back
    compressed_bytes = result.to_buffer()   # returns PNG/JPEG bytes [web:77][web:81]

    # 4) Turn bytes back into a Pillow Image
    out_buf = io.BytesIO(compressed_bytes)
    compressed_img = Image.open(out_buf)
    compressed_img.load()  # force load from buffer


    return compressed_img


def encode_image_base64(pil_image=None):
    """
    takes either a fjlename or a PIL image.  Image is converted
    to a base64 encoded PNG

    :param pil_image:      PIL Image object.
    :type pil_image:       PIL.Image.Image
    :return:               The base64-encoded PNG bytes of the image.
    :rtype:                bytes
    """


    # Always encode as PNG in memory
    with io.BytesIO() as bio:
        pil_image.save(bio, format="PNG")
        contents = bio.getvalue()
        encoded = base64.b64encode(contents)
    display_message(f'B64PNG encoded')

    return encoded

def get_image_size_and_dimensions(filename, as_text=True):
    """

    :param filename:    image filename
    :type filename:     str
    :param as_text:     if True then return will be info as a single string
    :type as_text:      bool
    :return:            size in bytesm, width, height
    :rtype:             Tuple[int, int, int]
    """
    image = Image.open(filename)
    width, height = image.size
    size_bytes = Path(filename).stat().st_size
    size_kb = size_bytes / 1024
    if as_text:
        return f"{size_kb:.1f} KB - {width} X {height}"
    return size_kb, width, height



def decode_base64(s):
    """
    Decodes and displays a base64 encoded PNG.  Displays the pixel dimensions and thge image
    :param s:           The base64 encoded string
    :type               str
    """
    image_bytes = ast.literal_eval(s)
    image = sg.tk.PhotoImage(data=image_bytes)         # used only to get image size
    sg.Window('', [[sg.Image(data=image_bytes), sg.T(f'{image.width()} x {image.height()}'),sg.Button('Ok')]], finalize=True).read(close=True)



#   ██████╗  ██████╗ ██████╗ ██╗   ██╗██████╗
#   ██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔══██╗
#   ██████╔╝██║   ██║██████╔╝██║   ██║██████╔╝
#   ██╔═══╝ ██║   ██║██╔═══╝ ██║   ██║██╔═══╝
#   ██║     ╚██████╔╝██║     ╚██████╔╝██║
#   ╚═╝      ╚═════╝ ╚═╝      ╚═════╝ ╚═╝
#
#   ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗███████╗
#   ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║██╔════╝
#   ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║███████╗
#   ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║╚════██║
#   ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝███████║
#    ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚══════╝




def image_popup(filenames:str, location, location_anchor=None):
    """
      Displays a popup window with options for the dropped files.  Performs chosen operation.

      If image files are dropped, options to convert to JPG, PNG, or Base64 PNG are shown.d
      For other file types, a list of the dropped files is displayed.

    :param filenames:       A comma-separated string of the dropped file paths.
    :type filenames:        str
    :param location:        The (x, y) coordinates of the icon window
    :type location:         Tuple[int, int] | Tuple[None, None]
    :param location_anchor: What part of the window should be anchored at the location
    :type location_anchor:  str
    """
    file_list = filenames.split(',')
    # if len(file_list) == 1:                 # If single item, see if it's a flash drive for photos
    #     sg.popup(f'Single file = {file_list[0]}')
    actions = ('Convert to JPG', 'Convert to PNG', 'Convert to GIF', 'Convert to ICO',  'Convert to WEBP','Convert to Base64-PNG', 'Cancel')
    image_files = all(file.lower().endswith(('jpeg', 'jpg', 'png', 'gif', 'ico', 'webp')) for file in file_list)
    if image_files:
        button_size = max(len(a) for a in actions)
        layout = [[sg.Text('Images dropped - What do you want to do with them?')],
                  [[sg.Text(f'{get_image_size_and_dimensions(file)} - {file}', p=0)] for file in file_list],
                  # [sg.Text('\n'.join(file_list))],
                  [sg.Column([[sg.Button(action, s=button_size, )] for action in actions], justification='c')],
                  [sg.P(), sg.Checkbox('Tinify PNGs', setting=False,  k='-TINIFY-', p=((20,0),0)), sg.P()] if tinify_available else [],
                  [sg.Push(), sg.Frame('', [[sg.Checkbox('Optional resizing', setting=False, font=('default', 14, 'bold'), k='-RESIZE-', p=((20,0),0))],
                  [sg.Input(setting='', justification='r', s=4, k='-RESIZE PERCENT-', p=((20,0),0)), sg.T('%')],
                  [sg.Input(setting='', justification='r', s=4, k='-RESIZE WIDTH-', p=((20,0),0)), sg.T('X'), sg.Input(setting='', justification='r', s=4, k='-RESIZE HEIGHT-',p=0)],
                  [sg.Button('Clear')]], border_width_no_relief=1), sg.Push()]]

        convert_window = MiniWindow('Image actions', layout, location=location, enable_close_attempted_event=True,  location_anchor=G.popup_anchor if location_anchor is None else location_anchor)
        convert_window.settings_restore()

        while True:
            event, values = convert_window.read()
            if event in ('Exit', 'Cancel', sg.WIN_CLOSED, sg.WIN_CLOSE_ATTEMPTED_EVENT):
                break
            # Perform actions
            if event.startswith('Convert'):
                image_format = event.split()[-1]                # The image format is always at the end of the button string
                encode_only = image_format == 'Base64-PNG'      # If is basse64 format, then do a special encode
                for file in file_list:
                    if values['-RESIZE-']:
                        percent = values['-RESIZE PERCENT-']
                        percent = None if not percent else int(percent)
                        width, height = values['-RESIZE WIDTH-'], values['-RESIZE HEIGHT-']
                        resize_w_h = (int(width), int(height)) if width and height else (None, None)
                    else:
                        percent, resize_w_h = None, (None, None)
                    if encode_only:
                        image_format = 'PNG'
                        # sg.clipboard_set(encode_image_base64(file))
                    b64_encoded = convert_formats(file, image_format, percent, resize_w_h, encode_to_base64=encode_only, tinify=values.get('-TINIFY-', False))
                    if encode_only:
                        sg.clipboard_set(b64_encoded)
                break
            elif event == 'Clear':
                convert_window['-RESIZE PERCENT-'].update('')
                convert_window['-RESIZE WIDTH-'].update('')
                convert_window['-RESIZE HEIGHT-'].update('')
        convert_window.settings_save(values)
        convert_window.close()
    else:
        # if they're not image files just show the list of files
        layout = [[sg.Text('Files dropped:', font='_ 15', p=(10,0))]]
        for file in file_list:
            layout.append([sg.Text(file, p=(10,0))])
        layout.append([sg.Push(), sg.Ok()])
        window = MiniWindow('Files Dropped', layout, location=location,  location_anchor= location_anchor if location_anchor else G.popup_anchor)
        window.refresh()
        event, values = window.read(close=True)

        # sg.popup(f'Dropped files:', '\n'.join(file_list), non_blocking=True, line_width=max(len(f)+1 for f in file_list), location=location, no_titlebar=True)

def text_popup(text:str, location, location_anchor=None):
    """
    Displays a popup window with options for dropped text.  Performs chosen operation.

    :param text:            The text dropped onto the icon
    :type text:             str
    :param location:        The (x, y) coordinates of the icon window.  Will want to show the popup offset from this location
    :type location:         Tuple[int, int] | Tuple[None, None]
    :param location_anchor: What part of the window should be anchored at the location
    :type location_anchor:  str
    """
    actions = ('Translate to English', 'Translate to Spanish',  'Decode BASE64 PNG', 'Cancel')
    lang_to_dest = {'Spanish' : 'es', 'English' : 'en'}
    button_size = max(len(a) for a in actions)
    layout = [[sg.Text('Text dropped - What do you want to do with it?')],
              [sg.Text('' if translate_installed else '* NOTE * Unable to use translate features. You need to install googletrans: pip install googletrans==3.1.0a0')],
              [sg.Column([[sg.Button(action, s=button_size, )] for action in actions], justification='c')]]
    convert_window = MiniWindow('Text actions', layout, location=location,  location_anchor=location_anchor if location_anchor  else G.popup_anchor)
    event, values = convert_window.read(close=True)
    # Perform actions
    if event.startswith('Translate'):
        lang = event.split()[-1]                # The image format is always at the end of the button string
        # Translate the text; dest='es' specifies Spanish as the destination language
        if translate_installed:
            translator = Translator()

            translation = translator.translate(text, dest=lang_to_dest[lang])
            display_message(f'Translated to {lang}')
            sg.clipboard_set(translation.text)
    elif event == 'Decode BASE64 PNG':
        decode_base64(text)
        # sg.popup(f'Dropped files:', '\n'.join(file_list), non_blocking=True, line_width=max(len(f)+1 for f in file_list), location=location, no_titlebar=True)



#   ███╗   ███╗██╗███╗   ██╗██╗    ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗
#   ████╗ ████║██║████╗  ██║██║    ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║
#   ██╔████╔██║██║██╔██╗ ██║██║    ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║
#   ██║╚██╔╝██║██║██║╚██╗██║██║    ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║
#   ██║ ╚═╝ ██║██║██║ ╚████║██║    ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝
#   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝

def MiniWindow(title: str, layout: List, **kwargs: Any) -> sg.Window:
    """
    A function that returns a Window object. The snake case MiniWindow name means we're acting like an object. An object is returned so the use won't notice
    :param title:       Title for the window titlebar
    :type title:        str
    :param layout:      The window layout
    :type layout:       List[List[sg.Element]]
    :param kwargs:      The normal Window arguments that a user is using to create the window
    :type kwargs:       Any
    :return:            A Window object that's a mini window with no titlebar
    :rtype:             sg.Window
    """
    # first embed the supplied layout into a layout that has a fake titlebar and frame used to draw the border
    layout = wrap_in_border(title, layout)
    return sg.Window(title, layout, no_titlebar=True, grab_anywhere=True, keep_on_top=True, finalize=True, margins=(0, 0), **kwargs)



def wrap_in_border(title: str, layout_rows: list, close_key: Any = 'Exit') -> list:
    """
    Wraps a Window Layout with a mini window outline with a titlebar and close button

        ┌──────────────────────────┐
        │ ▌  Title              ✕  │
        ├──────────────────────────┤
        │   ...layout_rows...      │
        └──────────────────────────┘
    :param title:               Title for the window titlebar
    :type title:                str
    :param layout_rows:         The layout for the window
    :type layout_rows:          List[List[sg.Element]]
    :param close_key:           Key to use for the window close button
    :type close_key:            Any
    :return:                    A layout to put into an sg.Window
    :rtype:                     List[List[sg.Element]]
    """

    titlebar = [sg.Text("▌", text_color=sg.theme_button_color_background(), font=("Segoe UI", 14)),
                sg.Text(title, font=("Segoe UI", 14, "bold"), expand_x=True),
                sg.Button(sg.SYMBOL_X_SMALL, key=close_key, border_width=0, pad=(2,0), font=("Segoe UI", 11, "bold"), mouseover_colors=("#ffffff", "#a13544"), tooltip="Close")]

    layout = [[sg.Column([titlebar], expand_x=True, pad=(0, 0))],
              [sg.HorizontalSeparator(color=sg.theme_text_color(),  pad=(0, 0))],
              *layout_rows]
    return [[sg.Frame("", layout, border_width_no_relief=1, p=0, expand_x=True, expand_y=True)]]




def display_message(message='')->None:
    """
    Displays a message in a small window like a tooltip.  Note a function attribute "window" must be set when program starts in order for this function to work
    :param message:         The text message to display
    :type message:          str
    """
    location = display_message.window.current_location()            # cheating and assuming there is a function attribute set that holds the icon's window
    location =  (location[0]-len(message)*2, location[1]+70)        # show the message just under the icon
    sg.popup_quick_message(message, font='_ 10', location=location,  background_color="#ffffe0",text_color='black', auto_close_duration=5)


#   ███╗   ███╗ █████╗ ██╗███╗   ██╗
#   ████╗ ████║██╔══██╗██║████╗  ██║
#   ██╔████╔██║███████║██║██╔██╗ ██║
#   ██║╚██╔╝██║██╔══██║██║██║╚██╗██║
#   ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
#   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝

def main():
    # sg.theme('dark red')          # try another theme... the mini windows look nice

    # get settings from settings file
    b64icon = sg.user_settings_get_entry(KEY_PNG_ICON_BASE64, None)
    pngicon = sg.user_settings_get_entry(KEY_PNG_ICON_FILENAME, None)
    keep_on_top = sg.user_settings_get_entry('-keep on top-', True)
    mouseover_icon = sg.user_settings_get_entry(KEY_PNG_MOUSEOVER_ICON_BASE64, None)
    try:
        alpha = int(sg.user_settings_get_entry(KEY_ALPHA, 10))/10
    except:
        alpha = 1
    # set the icon to use
    if b64icon:
        G.icon = ast.literal_eval(b64icon)
    elif pngicon:
        G.icon = pngicon
    else:
        G.icon = sg.EMOJI_BASE64_COOL

    if mouseover_icon:
        G.mouseover_icon = ast.literal_eval(mouseover_icon)


    if tinify_available:
        G.tinify_api_key = sg.user_settings_get_entry(KEY_TINIFY_API_KEY, None)
        tinify.key = G.tinify_api_key



    #------- GUI definition & setup --------#


    RIGHT_CLICK_MENU = ['', ['Settings', f'Keep on top is {"ON" if keep_on_top else "OFF"}', 'Edit Me', 'Version', 'Exit']]
    # layout = [[sg.Button(image_source=icon, key='-ICON-', p=0, button_color='black', border_width=0, mouseover_image_source=G.mouseover_icon)]]
    layout = [[sg.Image(source=G.icon, key='-ICON-', p=0, background_color='black', enable_events=True, mouseover_image_source=G.mouseover_icon)]]

    window = sg.Window('Desktop Icon Demo', layout, element_justification='center', resizable=True, no_titlebar=True, right_click_menu=RIGHT_CLICK_MENU, margins=(0,0), grab_anywhere=True, auto_save_location=True, keep_on_top=keep_on_top,  finalize=True, alpha_channel=alpha, transparent_color='black')

    display_message.window = window           # important.... need to set this function attribute for the display message function to work... sorry, it's a hack

    dnd.register_element_dnd(window['-ICON-'], window, dnd.DROP_TYPE_ALL)        # The one line of code needed to add drag and drop

    window['-ICON-'].bind('<Double-Button-1>', '+DOUBLE_CLICK+')

    #------------ The Event Loop ------------#
    while True:
        event, values = window.read()
        # print(event, values)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        if dnd.is_drop_event(event):                            # Drag and Drop event
            dnd_event: dnd.DropEvent = event
            if dnd_event.drop_type == dnd.DROP_TYPE_FILES:      # If files are dropped, show a window with choices of what to do with them
                image_popup(values[event], window.current_location(use_anchor=G.icon_popup_anchor))
            elif dnd_event.drop_type == dnd.DROP_TYPE_TEXT:      # If files are dropped, show a window with choices of what to do with them
                text_popup(values[event], window.current_location(use_anchor=G.icon_popup_anchor))
        if event == '-ICON-+DOUBLE_CLICK+':                    # Add your double-click action here... such as launching another program
            command = sg.user_settings_get_entry(KEY_DOUBLE_CLICK_COMMAND, '')
            if command:
                try:
                    sg.execute_command_subprocess(command)
                except:
                    print('Error running double-click')
            else:
                event = 'Settings'                    # Fake a settings event
        if event == 'Settings':
            display_message('Opening settings')
            show_settings_window(window.current_location(use_anchor=G.icon_popup_anchor))
            window['-ICON-'].mouseover_image_set(image_source=G.mouseover_icon)           # in case the mouseover image changed
            if not G.icon:
                G.icon = sg.EMOJI_BASE64_COOL
            window['-ICON-'].update(source=G.icon)
        elif event in ('Keep on top is OFF', 'Keep on top is ON'):          # Keep on top right click menu
            window.keep_on_top_set() if event.endswith('OFF') else window.keep_on_top_clear()
            RIGHT_CLICK_MENU[1][1] = f'Keep on top is {"ON" if event.endswith("OFF") else "OFF"}'
            window['-ICON-'].set_right_click_menu(RIGHT_CLICK_MENU)
            sg.user_settings_set_entry('-keep on top-', event.endswith("OFF"))
        elif event == 'Version':
            sg.popup_scrolled( f'This Program: {__file__} version {version}', sg.get_versions(), f'psgdnd version: {dnd.version}',  keep_on_top=True, non_blocking=True, button_justification='right', size=(102, 12))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    window.close()

if __name__ == '__main__':
    required_psg_version = '6.2.14'
    if Version(sg.version) < Version(required_psg_version):
        if sg.popup_yes_no(f'ERROR - PySimpleGUI version is {sg.version}', f'PySimpleGUI version {required_psg_version} or greater is required to run this program.', 'To pip install it, execute the command:', r'python -m pip install --upgrade https://github.com/PySimpleGUI/PySimpleGUI/zipball/master', 'Would you like to upgrade to latest from GitHub?', line_width=100) == 'Yes':
            sg.execute_pip_install_package(r'https://github.com/PySimpleGUI/PySimpleGUI/zipball/master')
            sg.popup_auto_close('Please restart the application to use the newly installed PySimpleGUI package.', auto_close_duration=3)
            exit()
        else:
            print('Exiting')
            exit()
    main()