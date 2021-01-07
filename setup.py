# Created by Daniel Cappel ("DRGN")
# Script version: 2.1

from cx_Freeze import setup, Executable
from shutil import copyfile
import sys, os

programName = "Melee Code Manager"
mcmMainScript = __import__( "Melee Code Manager" ) # This import method is used in order to import a file with spaces in its name.
preserveConsole = True # For the console to work, search for the string "logging output" in the main MCM script, and comment out the relevent code there.

# Dependencies are automatically detected, but it might need fine tuning.

keepTheseIncludes = ( 'CommonMCM.s', 'punkpc' ) # Files other than these in the new .include folder will be deleted (assumed to be test files)

buildOptions = dict(
	packages = [], 
	#includes = [newTkDnD],
	excludes = [], 
	include_files = [
		'.include',
		'About.txt',
		'bin',
		'defaultOptions.ini',
		#'geckoCodehandler0.bin',
		'imgs',
		'Mods Library',
		'settings.py',
		'sfx',
		'Original DOLs',
		'tk', # For drag 'n drop functionality.
	])

if preserveConsole:
	base = 'Console'
else:
	base = 'Win32GUI' if sys.platform == 'win32' else None

# Determine platform architecture
if sys.maxsize > 2**32:
	platformArchitecture = 'x64'
else:
	platformArchitecture = 'x86'

executables = [
	Executable(
		"Melee Code Manager.py", 
		icon='appIcon1.3.ico',
		base=base )
	]

print 'Preparing setup....'

# Normalize the version string for setup ('version' below must be a string, with only numbers or dots)
simpleVersion = '.'.join( [char for char in mcmMainScript.programVersion.split('.') if char.isdigit()] )

setup(
		name=programName,
		version = simpleVersion,
		description = 'DOL Modding Program for GameCube and Wii Games.',
		options = dict( build_exe = buildOptions ),
		executables = executables
	)

# Perform file/folder renames
print '\n'
print 'Main script version:    ', mcmMainScript.programVersion
print 'Simplified version:     ', simpleVersion
print 'Platform architecture:  ', platformArchitecture

# Get the name of the new program folder that will be created in '\build\'
scriptHomeFolder = os.path.abspath( os.path.dirname(__file__) )
buildFolder = os.path.join( scriptHomeFolder, 'build' )
programFolder = ''
for directory in os.listdir( buildFolder ):
	if directory.startswith( 'exe.' ): # e.g. "exe.win-amd64-2.7"
		programFolder = os.path.join( buildFolder, directory )
		break
else: # The loop above didn't break
	print 'Unable to locate the new program folder!'
	sys.exit( 2 )

# Delete extra (test) .include items
try:
	rootIncludeFolder = os.path.join( programFolder, '.include' )
	for item in os.listdir( rootIncludeFolder ):
		if item not in keepTheseIncludes:
			os.remove( os.path.join( rootIncludeFolder, item ) )
	print '\nRemoved test .include files'
except Exception as err:
	print '\nUnable to remove test .include files.'	#	<- Access is denied??
	print err

# Rename the default options (.ini) file
os.rename( programFolder + '\\defaultOptions.ini', programFolder + '\\options.ini' )

# Create a new name for the progam folder (and make sure it's unique) and rename it
newProgramFolderName = '{} - v{} ({})'.format( programName, mcmMainScript.programVersion, platformArchitecture )
newProgramFolderPath = os.path.join( buildFolder, newProgramFolderName )
i = 2
while os.path.exists( newProgramFolderPath ):
	newProgramFolderPath = os.path.join( buildFolder, newProgramFolderName + ' ' + str( i ) )
	i += 1
os.rename( programFolder, newProgramFolderPath )
print 'Program folder renamed to', os.path.basename( newProgramFolderPath )

# Open the build folder for viewing
os.startfile( buildFolder )