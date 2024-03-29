# Created by Daniel Cappel ("DRGN")
# Script version: 2.2

from cx_Freeze import setup, Executable
import sys, os

programName = "Melee Code Manager"
mainScript = __import__( "Melee Code Manager" ) # This import method is used in order to import a file with spaces in its name.
preserveConsole = False # For the console to work, search for the string "logging output" in the main MCM script, and comment out the relevent code there.

# Dependencies are automatically detected, but it might need fine tuning.

buildOptions = dict(
	packages = [], 
	excludes = [ 'settings' ], # Prevent from adding module to lib/library.zip, to read from lib/settings.py instead
	include_files = [
		'.include',
		'About.txt',
		'bin',
		'defaultOptions.ini',
		'imgs',
		'Mods Library',
		'Original DOLs',
		'settings.py',
		'sfx',
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
simpleVersion = '.'.join( [char for char in mainScript.programVersion.split('.') if char.isdigit()] )

setup(
		name = programName,
		version = simpleVersion,
		description = 'DOL Modding Program for GameCube and Wii Games.',
		options = dict( build_exe = buildOptions ),
		executables = executables
	)

# Perform file/folder renames
print '\n'
print 'Main script version:    ', mainScript.programVersion
print 'Simplified version:     ', simpleVersion
print 'Platform architecture:  ', platformArchitecture

# Get the name of the new program folder that will be created in '\build\'
scriptHomeFolder = os.path.abspath( os.path.dirname(__file__) )
buildFolder = os.path.join( scriptHomeFolder, 'build' )
builtProgramFolder = ''
for directory in os.listdir( buildFolder ):
	if directory.startswith( 'exe.' ): # e.g. "exe.win-amd64-2.7"
		builtProgramFolder = os.path.join( buildFolder, directory )
		break
else: # The loop above didn't break
	print 'Unable to locate the new program folder!'
	sys.exit( 2 )

# Delete extra (test) .include items
#keepTheseIncludes = ( 'CommonMCM.s', 'punkpc' ) # Files other than these in the new .include folder will be deleted (assumed to be test files)
# try:
# 	rootIncludeFolder = os.path.join( builtProgramFolder, '.include' )
# 	for item in os.listdir( rootIncludeFolder ):
# 		if item not in keepTheseIncludes:
# 			os.remove( os.path.join( rootIncludeFolder, item ) )
# 	print '\nRemoved test .include files'
# except Exception as err:
# 	print '\nUnable to remove test .include files.'	#	<- Access is denied??
# 	print err

# Rename the default options (.ini) file
os.rename( builtProgramFolder + '\\defaultOptions.ini', builtProgramFolder + '\\options.ini' )

# Create a new name for the progam folder (ensuring it's unique) and rename it
newProgramFolderName = '{} - v{} ({})'.format( programName, mainScript.programVersion, platformArchitecture )
newProgramFolderPath = os.path.join( buildFolder, newProgramFolderName )
i = 2
while os.path.exists( newProgramFolderPath ):
	newProgramFolderPath = os.path.join( buildFolder, newProgramFolderName + ' ' + str( i ) )
	i += 1
os.rename( builtProgramFolder, newProgramFolderPath )
print 'Program folder renamed to "{}"'.format( newProgramFolderName )

# Move the settings.py configuration file to the lib folder
source = os.path.join( newProgramFolderPath, 'settings.py' )
destination = os.path.join( newProgramFolderPath, 'lib', 'settings.py' )
os.rename( source, destination )