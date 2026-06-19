import setuptools

def readme():
    try:
        with open('README.md') as f:
            return f.read()
    except IOError:
        return ''



setuptools.setup(
name="psgdnd",
version="6.0.2",
author="PySimpleGUI",
install_requires=["PySimpleGUI","tkinterdnd2"],
description="Drag and Drop expansion for PySimpleGUI",
long_description=readme(),
long_description_content_type="text/markdown",
license='GNU Lesser General Public License v3 (LGPLv3)',
keywords="psgdnd PySimpleGUI DragAndDrop",
url="https://github.com/PySimpleGUI/psgdnd",
packages=setuptools.find_packages(),
python_requires=">=3.6",
classifiers=[
"Intended Audience :: Developers",
"License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
"Operating System :: OS Independent",
"Framework :: PySimpleGUI",
"Programming Language :: Python :: 3",
"Programming Language :: Python :: 3.6",
"Programming Language :: Python :: 3.7",
"Programming Language :: Python :: 3.8",
"Programming Language :: Python :: 3.9",
"Programming Language :: Python :: 3.10",
"Programming Language :: Python :: 3.11",
"Programming Language :: Python :: 3.12",
"Programming Language :: Python :: 3.13",
"Programming Language :: Python :: 3.14",
"Programming Language :: Python :: 3.15",
"Topic :: Multimedia :: Graphics",
],
package_data={"":
["*","*.*"]
        },
)

