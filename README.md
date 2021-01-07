# Melee Code Manager (MCM)
This is a program to manage the installation of code-based mods in GameCube/Wii games, using a simple and very easy to use interface, and desgined particularly for Super Smash Bros. Melee. This includes Gecko codes, but can also install static overwrites and injection mods without the need for a codehandler. Default game settings for SSBM can also easily be set, including settings that aren't normally saved between resets. The program can operate on an ISO/GCM disc directly, or a standalone DOL file. Also available are multiple useful tools, including an assembler, a DOL offset to RAM address converter, number converters, ASCII to Hex converters, an interface to help construct new code mods, and more. It also has a useful conflict detection feature, to warn about cases where mods would interfere with one another.

Injection codes are installed to regions in the DOL marked as safe for overwriting. These custom code regions can be defined by opening and editing the settings.py file (which is available and still functional for edits even after the program is compiled). Many regions can be defined, and the actual ones used by the program can be set on a per-use basis by clicking on the "Code-Space Options" button in the program.

In a sense this also "wraps" the assembly language, adding a few extra special syntaxes: Standalone Functions, Special Branch Syntaxes, and RAM Pointer Symbols. These allow codes to share code or data in non-redundant ways, without having to hardcode their locations. Their functionality and usage can be found [here](https://smashboards.com/threads/melee-code-manager-v4-3-easily-add-mods-to-your-game.416437/post-20075377).

You can find the official thread for this program here: [Melee Code Manager on SmashBoards.com](https://smashboards.com/threads/melee-code-manager-v4-3-easily-add-mods-to-your-game.416437/)

Disclaimer: the structure of this program's code is largely a very functional style (i.e. built mostly using just strait functions). Certainly some parts would be better suited as objects, with classes and their own personal methods, and I know there are some things that could be done more efficiently. A big reason for these things is the fact that this is a really old project, built when I was first learning Python. :P But going forward I'll be occasionally refactoring parts of this program, and rewriting key components of it as I incorporate them into future projects. Let me know if there's anything you'd like to see broken out into a separate project.

## Installation & Setup
### Windows
In order to run or compile this program, you'll need to install Python 2 and a few modules. Any version of python between 2.7.12 up to the latest 2.7 should work.

After installing Python, the following Python modules must be installed:

    - Pillow      (internally referred to as PIL)
    - cx-Freeze   (if you want to compile)

The easiest way to install these is with pip, which comes with Python by default. It's found in C:\Python27\Scripts; which you'll need to navigate to if you didn't install Python to your PATH variable (which is an option when you install it). Once you're ready to run pip commands, you can install the above modules by running 'pip install [moduleName]' for each one. All other dependencies are included in the repo.

cx-Freeze will need to be less than version 6 for compatibility with Python 2.7. I recommend v5.1.1, as that's what I've been using. To install this specific version, you can use "pip install cx-Freeze==5.1.1"

### Other OSes
Running the program uncompiled on other platforms hasn't been tested yet. However, once compiled, MCM can be run on MacOS, Android, Ubuntu, and more using Wine. For platform and version compatibility of Wine, check [Wine's download page](https://wiki.winehq.org/Download). Homebrew can be used as a convenient package manager to install as Wine. Of course, running MCM within a VM (Virtual Machine) is also a viable option if this doesn't work for you.

The following directions are for MacOS, however I haven't tested them myself, so please let me know if you find any mistakes or have any improvements.

   1. Install Homebrew: open terminal and enter `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
   2. Enter `brew doctor` to make sure Homebrew is running well
   3. Install wine by entering `brew install wine`
   4. Install winetricks by entering `brew install winetricks`
   5. Enter 'winetricks -q dotnet452 corefonts' to install .net frameworks 4.5.2 for Wine
   6. Navigate to your MCM folder (you can use `cd` to enter a folder, and `ls` to see what folders you can enter)
   7. Run `wine Melee\ Code\ Manager.exe` (spaces in folder and file names need to be escaped with backslashes)

You can find a larger explanation and guide for installing Homebrew and Wine [here](https://www.davidbaumgold.com/tutorials/wine-mac/) (also includes making a dock icon), or try Google for more.

## Building (Windows)
This program uses cx-Freeze to compile, using the setup.py file. To compile the program, you just need to run the "Build Executable.bat" batch script, which is a simple wrapper for setup.py. Once compiled, the program will be found in the 'build' folder, and will be renamed to 'Melee Code Manager - v[version] ([x86|x64])'.
