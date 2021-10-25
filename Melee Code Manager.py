#!/usr/bin/python
# This Python file uses the following encoding: utf-8

							# ------------------------------------------------------------------- #
						   # ~ ~ Written by DRGN of SmashBoards (Daniel R. Cappel); June, 2015 ~ ~ #
							#       -       -       [Python v2.7.9 & 2.7.12]      -       -       #
							# ------------------------------------------------------------------- #

programVersion = '4.4'

# # Find the official thread here:
# http://smashboards.com/threads/melee-code-manager-easily-add-codes-to-your-game.416437/

# Primary logic.
import os # For various file and directory operations.
import time # For performance testing
import json	# For opening/parsing yaml config files (used for alternate mod folder structure syntax)
import errno
import codecs
import sys, csv
import datetime
#import win32api # Needs to be installed via "pip install pywin32"
import webbrowser # Used to open a web page (the Melee Workshop, from the createNewDolMod function) or text file.
import subprocess, math # For communication with command line, and rounding operations, respectively.
import struct, binascii # For converting byte strings to integers. And binascii for the file hash function.
from decimal import Decimal # For the Code Creation tab's number conversions
from string import hexdigits # For checking that a string only consists of hexadecimal characters.
from binascii import hexlify
from collections import OrderedDict
from sets import Set # Used for duplicate mod detection and other unique lists
try: from cStringIO import StringIO # For compiling/decompiling. cStringIO referred for performance.
except: from StringIO import StringIO

# GUI stuff
from Tkinter import Tk, Toplevel, Frame, StringVar, IntVar, BooleanVar, Label, OptionMenu, Spinbox, Button, Menu, Scrollbar, Canvas
from commonGuiModules import getWindowGeometry, basicWindow, CopyableMsg, PopupEntryWindow, PopupScrolledTextWindow, ToolTip
import Tkinter, ttk, tkMessageBox, tkFileDialog, tkFont
from ScrolledText import ScrolledText
from PIL import Image, ImageTk # For working with more image formats than just GIF.
from urlparse import urlparse # For validating and security checking URLs
from threading import Thread
from newTkDnD import TkDND # Access files given (drag-and-dropped) onto the running program GUI.
import pyaudio, wave
import webbrowser # Used for opening web pages

# User defined settings / persistent memory.
import settings as settingsFile
import ConfigParser
settings = ConfigParser.SafeConfigParser()
settings.optionxform = str # Tells the parser to preserve case sensitivity (for camelCase).

# Set up some useful globals
scriptHomeFolder = os.path.abspath( os.path.dirname(sys.argv[0]) )
dolsFolder = scriptHomeFolder + '\\Original DOLs'
imageBank = {} # Populates with key=fileNameWithoutExt, value=ImageTk.PhotoImage object
soundBank = {} # Populates with key=fileNameWithoutExt, value=fullFilePath

genGlobals = { # General Globals (migrate other globals to here)
	'optionsFilePath': scriptHomeFolder + '\\options.ini',
	'allModNames': Set(), # Will contain only unique mod names (used for duplicate mod detection)
	'allMods': [],
	'allStandaloneFunctions': {},
	'originalDolRevisions': [],
	'modifiedRegions': []
}

# The following are saved in the options.ini file (if it exists). To access them within the program, use:
#		settings.get( 'General Settings', [valueName] )
#		settings.set( 'General Settings', [valueName], [newValue] )
# And save them to file with a call to saveOptions()
generalOptionDefaults = {
	'modsFolderPath': scriptHomeFolder + '\\Mods Library',
	'modsFolderIndex': '0',
	'defaultSearchDirectory': os.path.expanduser( '~' ),
	'defaultFileFormat': 'iso',
	'onlyUpdateGameSettings': 'False',
	'hexEditorPath': '',
	# 'altFontColor': '#d1cede', # A shade of silver; useful for high-contrast system themes
	'offsetView': 'ramAddress', # alternate acceptable value=dolOffset (not case sensitive or affected by spaces)
	'summaryOffsetView': 'dolOffset',
	'sortSummaryByOffset': 'False'
	}
overwriteOptions = OrderedDict() # Populates with key=customCodeRegionName, value=BooleanVar (to describe whether the regions should be used.)

# The following two dictionaries are only used for SSBM, for the game's default settings.
# Key = target widget, value = tuple of "(tableOffset, gameDefault, tourneyDefault [, str translations])".
# The gameDefault and tourneyDefault integers are indexes, relating to the string portion of the tuple (if it has a string portion).
# If the tuple doesn't have a string portion, then the values are instead the direct value for the setting (e.g. 3 stock or 4 stock).
settingsTableOffset = { 'NTSC 1.00': 0x3CFB90, 'NTSC 1.01': 0x3D0D68, 'NTSC 1.02': 0x3D1A48, 'NTSC 1.03': 0x3D1A48, 'PAL 1.00': 0x3D20C0 }
gameSettingsTable = {
	'gameModeSetting': 			(2, 0, 1, 'Time', 'Stock', 'Coin', 'Bonus'),				# AA
	'gameTimeSetting': 			(3, 2, 2),													# BB
	'stockCountSetting': 		(4, 3, 4),													# CC
	'handicapSetting': 			(5, 0, 0, 'Off', 'Auto', 'On'),								# DD
	'damageRatioSetting': 		(6, 1.0, 1.0),												# EE
	'stageSelectionSetting': 	(7, 0, 0, 'On', 'Random', 'Ordered', 'Turns', 'Loser'),		# FF
	'stockTimeSetting': 		(8, 0, 8),													# GG
	'friendlyFireSetting': 		(9, 0, 1, 'Off', 'On'),										# HH
	'pauseSetting': 			(10, 1, 0, 'Off', 'On'),									# II
	'scoreDisplaySetting': 		(11, 0, 1, 'Off', 'On'),									# JJ
	'selfDestructsSetting':		(12, 0, 0, '-1', '0', '-2'),								# KK
	'itemFrequencySetting': 	(24, 3, 0, 'None', 'Very Low', 'Low', 
									'Medium', 'High', 'Very High', 'Extremely High'),		# PP 
	'itemToggleSetting': 		(36, 'FFFFFFFF', '00000000'),
	'p1RumbleSetting': 			(40, 1, 0, 'Off', 'On'),									# R1
	'p2RumbleSetting': 			(41, 1, 0, 'Off', 'On'),									# R2
	'p3RumbleSetting': 			(42, 1, 0, 'Off', 'On'),									# R3
	'p4RumbleSetting': 			(43, 1, 0, 'Off', 'On'),									# R4
	#'soundBalanceSetting': 	(44, 0, 0),													# MM
	#'deflickerSetting': 		(45, 1, 1, 'Off', 'On'),									# SS
	#'languageSetting': 		(46, ),	# Game ignores this in favor of system default?		# LL
	'stageToggleSetting': 		(48, 'FFFFFFFF', 'E70000B0')								# TT
	#'bootToSetting':			()
	#'dbLevelSetting': 			()
	} # The variables that the program and GUI use to track the user's changes to these settings are contained in 'currentGameSettingsValues'


																				 #=========================#
																				# ~ ~ General Functions ~ ~ #
																				 #=========================#

def msg( *args ):
	if len(args) > 2: tkMessageBox.showinfo( message=args[0], title=args[1], parent=args[2] )
	elif len(args) > 1: tkMessageBox.showinfo( message=args[0], title=args[1] )
	else: tkMessageBox.showinfo( message=args[0] )

def toInt( input ): # Converts 1, 2, and 4 byte bytearray values to integers.
	try:
		byteLength = len( input )
		if byteLength == 1: return struct.unpack( '>B', input )[0] 		# big-endian unsigned char (1 byte)
		elif byteLength == 2: return struct.unpack( '>H', input )[0] 	# big-endian unsigned short (2 bytes)
		else: return struct.unpack( '>I', input )[0] 						# big-endian unsigned int (4 bytes)
	except:
		raise ValueError( 'toInt was not able to convert the ' + str(type(input))+' type' )
			
def isNaN( var ): ## Test if a variable 'is Not a Number'
	try:
		float( var )
		return False
	except ValueError:
		return True

def isEven( inputVal ):
	if inputVal % 2 == 0: return True # Non-zero modulus indicates an odd number.
	else: return False

def roundTo32( x, base=32 ): # Rounds up to nearest increment of 32.
	return int( base * math.ceil(float(x) / base) )

def uHex( integer ): # Quick conversion to have a hex function which uses uppercase characters.
	if integer == 0: return '0'
	else: return '0x' + hex( integer )[2:].upper()

def toHex( intOrStr, padTo ): # Creates a hex string (from an int or int string) and pads the result to n zeros (nibbles), the second parameter.
	return "{0:0{1}X}".format( int( intOrStr ), padTo )

def grammarfyList( theList ): # For example, the list [apple, pear, banana, melon] becomes the string 'apple, pear, banana, and melon'.
	if len(theList) == 1: return str(theList[0])
	elif len(theList) == 2: return str(theList[0]) + ' and ' + str(theList[1])
	else:
		string = ', '.join( theList )
		indexOfLastComma = string.rfind(',')
		return string[:indexOfLastComma] + ', and ' + string[indexOfLastComma + 2:]

def convertCamelCase( originalString ): # Normalizes camelCase strings to normal writing; e.g. "thisIsCamelCase" to "This is camel case"
	stringList = []
	for character in originalString:
		if stringList == []: stringList.append( character.upper() )	# Capitalize the first character in the string
		elif character.isupper(): stringList.append( ' ' + character )
		else: stringList.append( character )
	return ''.join( stringList )

def humansize( nbytes ): # Used for converting file sizes, in terms of human readability.
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	if nbytes == 0: return '0 B'
	i = 0
	while nbytes >= 1024 and i < len(suffixes)-1:
		nbytes /= 1024.
		i += 1
	f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
	return '%s %s' % (f, suffixes[i])

def createFolders( folderPath ):
	try:
		os.makedirs( folderPath )
	except OSError as exc: # Suppresses error if the directory already exists. Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir( folderPath ):
			pass
		else: raise

def findAll( stringToLookIn, subString, charIncrement=2 ): # Finds ALL instances of a string in another string
	matches = []
	i = stringToLookIn.find( subString )
	while i >= 0:
		matches.append( i )
		i = stringToLookIn.find( subString, i + charIncrement ) # Change 2 to 1 if not going by bytes.
	return matches

def getType( object ):
	return str(type(object)).replace("<type '", '').replace("'>", '')

# def CRC32_from_file( filepath ):
# 	#buf = open( filepath, 'rb').read()
# 	with open( filepath, 'rb' ) as file: buf = file.read()
# 	buf = (binascii.crc32( buf ) & 0xFFFFFFFF)
# 	return "%08X" % buf

def validHex( offset ): # Accepts a string.
	if offset == '': return False
	return all(char in hexdigits for char in offset) # Returns Boolean

def copyToClipboard( text ):
	root.clipboard_clear()
	root.clipboard_append( text )

def rgb2hex( color ): return '#{:02x}{:02x}{:02x}'.format( color[0], color[1], color[2]) # input can be RGBA, but output will still be RGB

def hex2rgb( hexColor ): # Expects '#RRGGBB' or '#RRGGBBAA'
	hexColor = hexColor.replace( '#', '' )
	channelsList = []

	if len( hexColor ) % 2 != 0: # Checks whether the string is an odd number of characters
		raise ValueError( 'Input to hex2rgb must be an even number of characters!' )
	else:
		for i in xrange( 0, len(hexColor), 2 ): # Iterate by 2 over the length of the input string
			channelByte = hexColor[i:i+2]
			channelsList.append( int( channelByte, 16 ) )

	return tuple(channelsList)

def name2rgb( name ):

	""" Converts a Tkinter color name to an RGB tuple. """

	colorChannels = root.winfo_rgb( name ) # Returns a 16-bit RGB tuple (0-65535)
	return tuple( [channel / 256 for channel in colorChannels] ) # Converts to an 8-bit RGB tuple (0-255)

def openFolder( folderPath, fileToSelect='' ): # Slow function, but cannot select files
	folderPath = os.path.abspath( folderPath ) # Turns relative to absolute paths, and normalizes them (switches / for \, etc.)

	if os.path.exists( folderPath ):
		if fileToSelect: # Slow method, but can select/highlight items in the folder
			if not os.path.exists( folderPath + '\\' + fileToSelect ):
				print( 'Could not find this file: \n\n' + fileToSelect )
				return

			command = '"C:\\Windows\\explorer.exe" /select, \"{}\\{}\"'.format( folderPath, fileToSelect )

			try:
				outputStream = subprocess.check_output(command, shell=False, stderr=subprocess.STDOUT, creationflags=0x08000000) # shell=True gives access to all shell features.
			except subprocess.CalledProcessError as error:
				outputStream = str(error.output)
				if len(outputStream) != 0:
					exitCode = str(error.returncode)
					print( 'IPC error: \n\n' + outputStream + '\n\nErrorlevel ' + exitCode )
			except Exception as generalError:
					print( 'IPC error: \n\n' + generalError )

		else: # Fast method, but cannot select files
			os.startfile( folderPath )

	else: print( 'Could not find this folder: \n\n' + folderPath )


																	 #=====================================#
																	# ~ ~ Initialization & File Reading ~ ~ #
																	 #=====================================#

class dolInitializer( object ):

	def __init__( self ):
		self.reset()

	def reset( self ):
		self.path = ''
		self.type = ''				# Essentially the file type/extension. Expected to be 'dol', 'iso', or 'gcm'
		self.gameId = ''
		self.discVersion = ''
		self.region = ''
		self.offset = 0
		self.version = ''
		self.revision = ''
		self.isMelee = False		# Will only be true for Super Smash Bros. Melee
		self.is20XX = False
		self.data = ''				# Future #todo: upgrade to a bytearray, below
		#self.bytes = bytearray()
		self.sectionInfo = OrderedDict()
		self.maxDolOffset = 0
		self.maxRamAddress = 0
		self.customCodeRegions = OrderedDict()
		self.isLoading = False

	def checkIfMelee( self ):
		# Check the DOL for a string of "Super Smash Bros. Melee" at specific locations
		self.isMelee = True

		ssbmStringBytes = bytearray()
		ssbmStringBytes.extend( "Super Smash Bros. Melee" )

		dataBytes = bytearray.fromhex( self.data )
		if dataBytes[0x3B78FB:0x3B7912] == ssbmStringBytes: self.region = 'NTSC'; self.version = '1.02' # most common, so checking for it first
		elif dataBytes[0x3B6C1B:0x3B6C32] == ssbmStringBytes: self.region = 'NTSC'; self.version = '1.01'
		elif dataBytes[0x3B5A3B:0x3B5A52] == ssbmStringBytes: self.region = 'NTSC'; self.version = '1.00'
		elif dataBytes[0x3B75E3:0x3B75FA] == ssbmStringBytes: self.region = 'PAL'; self.version = '1.00'
		else: 
			self.region = self.version = ''
			self.isMelee = False

	def getDolVersion( self ):
		# The range 0xE4 to 0x100 in the DOL is normally unused padding. This can be used to specify a DOL version.
		customDolVersionRange = bytearray.fromhex( self.data )[0xE4:0x100]
		customVersionString = customDolVersionRange.split(b'\x00')[0].decode( 'ascii' )

		# If a custom string exists, validate and use that, or else prompt the user (using disc region/version for predictors)
		if customVersionString and ' ' in customVersionString: # Highest priority for determining version
			apparentRegion, apparentVersion = normalizeRegionString( customVersionString ).split() # Should never return 'ALL' in this case

			if ( apparentRegion == 'NTSC' or apparentRegion == 'PAL' ) and apparentVersion.find( '.' ) != -1:
				self.region, self.version = apparentRegion, apparentVersion

		if not self.region or not self.version:
			# Check the filepath; if this is an original DOL in the Original DOLs folder, use the file name to determine version
			if self.type == 'dol' and os.path.dirname( self.path ) == dolsFolder:
				self.region, self.version = normalizeRegionString( os.path.basename(self.path) ).split()
				return

			# Attempt to predict details based on the disc, if present
			regionSuggestion = 'NTSC'
			versionSuggestion = '02'
			if self.type == 'iso' or self.type == 'gcm':
				if self.region == 'NTSC' or self.region == 'PAL': 
					regionSuggestion = self.region

				if '.' in self.discVersion: 
					versionSuggestion = self.discVersion.split('.')[1]

				userMessage = ( "The revision of the DOL within this disc is being predicted from the disc's details. Please verify them below. "
								  "(If this disc has not been altered, these predictions can be trusted.)" )
			else:
				userMessage = "This DOL's revision could not be determined. Please select a region and game version below."
			userMessage += ' Note that codes may not be able to be installed or detected properly if these are set incorrectly.'

			revisionWindow = RevisionPromptWindow( userMessage, regionSuggestion, versionSuggestion )

			if revisionWindow.region and revisionWindow.version: # Save the user-confirmed revision
				self.region = revisionWindow.region
				self.version = revisionWindow.version
				self.writeSig()

				# Write the new DOL data to file/disc
				if self.type == 'dol':
					with open( self.path, 'wb') as dolBinary:
						dolBinary.write( bytearray.fromhex(self.data) )
						
				elif ( self.type == 'iso' or self.type == 'gcm' ) and self.offset != 0:
					with open( self.path, 'r+b') as isoBinary:
						isoBinary.seek( self.offset  )
						isoBinary.write( bytearray.fromhex(self.data) )

			else: # Checking for the window sinceAssume the suggested revision
				self.region = regionSuggestion
				self.version = '1.' + versionSuggestion
				msg( 'Without confirmation, the DOL file will be assumed as ' + self.region + ' ' + self.version + '. '
					 'If this is incorrect, you may run into problems detecting currently installed mods or with adding/removing mods. '
					 'And installing mods may break game functionality.', 'Revision Uncertainty', root )

	def checkIf20XX( self ):
		
		""" 20XX has a version string in the DOL at 0x0x3F7158, preceded by an ASCII string of '20XX'.
			Versions up to 4.07++ used an ASCII string for the version as well (v4.07/4.07+/4.07++ have the same string).
			Versions 5.x.x use a new method of project code, major version, minor version, and patch, respectively (one byte each). """

		# Check for the '20XX' string
		if self.data[0x3F7154*2:0x3F7154*2+8] != '32305858':
			self.is20XX = ''
			return

		versionData = bytearray.fromhex( self.data[0x3F7158*2:0x3F7158*2+8] )
		
		# Check if using the new v5+ format
		if versionData[0] == 0:
			self.project, self.major, self.minor, self.patch = struct.unpack( 'BBBB', versionData )
			self.is20XX = '{}.{}.{}'.format( self.major, self.minor, self.patch )
		
		else: # Using the old string format, with just major and minor
			self.is20XX = versionData.decode( 'ascii' )

			# Parse out major/minor versions
			major, minor = self.is20XX.split( '.' )
			self.major = int( major )
			self.minor = int( minor )

			# May be able to be more accurate
			if self.is20XX == '4.07' and len( self.data ) == 0x438800 and self.data[-4:] == bytearray( b'\x00\x43\x88\x00' ):
				self.is20XX = '4.07++'
				self.patch = 2
			else:
				self.patch = 0

	def writeSig( self ):
		
		""" Saves the DOL's determined revision to the file in an unused area, 
			so that subsequent loads don't have to ask about it. """

		# Create the hex string; [DOL Revision]00[Program Version]
		revisionDataHex = ( self.region + ' ' + self.version ).encode("hex")
		revisionDataHex += '00' + ( 'MCM v' + programVersion ).encode("hex") # Adds a stop byte and MCM's version number

		# Ensure the data length never exceeds 0x1C bytes
		nibLength = len( revisionDataHex )
		if nibLength > 0x38: # 0x38 = 0x1C * 2
			revisionDataHex = revisionDataHex[:0x38]
			padding = ''

		else:
			# Fill the rest of the section with zeroes
			padding = '0' * ( 0x38 - nibLength )

		# Write the string to the file data
		self.data = self.data[:0x1C8] + revisionDataHex + padding + self.data[0x200:] # Static values doubled to count by nibbles; 0x1C8 = 0xE4 * 2

	def getDolDataFromIso( self, isoPath ):
		with open( isoPath, 'rb') as isoBinary:
			# Collect info on the disc
			self.gameId = isoBinary.read(6).decode( 'ascii' ) # First 6 bytes
			isoBinary.seek( 1, 1 ) # Second arg means to seek relative to current position
			versionHex = isoBinary.read(1).encode("hex")
			regionCode = self.gameId[3]
			ntscRegions = ( 'A', 'E', 'J', 'K', 'R', 'W' )
			if regionCode in ntscRegions: self.region = 'NTSC'
			else: self.region = 'PAL'
			self.discVersion = '1.' + versionHex

			# Get the DOL's ISO file offset, length, and data.
			isoBinary.seek( 0x0420 )
			self.offset = toInt( isoBinary.read(4) ) # Should be 0x1E800 for SSBM NTSC v1.02
			tocOffset = toInt( isoBinary.read(4) )
			dolLength = tocOffset - self.offset # Should be 0x438600 for SSBM NTSC v1.02
			isoBinary.seek( self.offset )
			self.data = isoBinary.read( dolLength ).encode("hex")

	def load( self, filepath ):
		self.reset()
		self.isLoading = True

		# Initialize the file path and type
		self.path = filepath
		self.type = os.path.splitext( filepath )[1].lower().replace( '.', '' )

		# Validate the given path
		if not filepath or not os.path.exists( filepath ): 
			msg( 'The recieved filepath was invalid, or for some reason the file was not found.' )
			return

		# Get the DOL's file data
		if self.type == 'iso' or self.type == 'gcm':
			self.getDolDataFromIso( filepath )

		elif self.type == 'dol':
			with open( filepath, 'rb') as binaryFile:
				self.data = binaryFile.read().encode("hex")

		else:
			msg( "The given file doesn't appear to be an ISO/GCM or DOL file. \nIf it in fact is, "
				 "you'll need to rename it with a file extension of '.iso/.gcm' or '.dol'.", 'Incorrect file type.' )
			return
		
		# Check if this is a revision of Super Smash Bros. Melee for the Nintendo GameCube.
		self.checkIfMelee()

		# General check for DOL revision (region + version). This will prompt the user if it cannot be determined.
		self.getDolVersion()

		if self.isMelee:
			self.checkIf20XX()

		if ( self.region == 'NTSC' or self.region == 'PAL' ) and '.' in self.version: 
			self.revision = self.region + ' ' + self.version

		self.parseHeader()

		self.isLoading = False

	def parseHeader( self ):
		headerData = bytearray.fromhex( self.data )[:0x100]

		# Separate the section information
		textFileOffsets = headerData[:0x1C]
		dataFileOffsets = headerData[0x1C:0x48]
		textMemAddresses = headerData[0x48:0x64]
		dataMemAddresses = headerData[0x64:0x90]
		textSizes = headerData[0x90:0xAC]
		dataSizes = headerData[0xAC:0xD8]
		self.bssMemAddress = toInt( headerData[0xD8:0xDC] )
		self.bssSize = toInt( headerData[0xDC:0xE0] )
		self.entryPoint = toInt( headerData[0xE0:0xE4] )

		self.maxDolOffset = 0
		self.maxRamAddress = 0

		# Combine data points into a single definition for each text section
		for i in xrange( 6 ): # No more than 6 possible
			listIndex = i * 4
			fileOffset = toInt( textFileOffsets[listIndex:listIndex+4] )
			memAddress = toInt( '\x00' + textMemAddresses[listIndex+1:listIndex+4] )
			size = toInt( textSizes[listIndex:listIndex+4] )

			# If any of the above values are 0, there are no more sections
			if fileOffset == 0 or memAddress == 0 or size == 0: break
			self.sectionInfo['text'+str(i)] = ( fileOffset, memAddress, size )

			# Find the max possible dol offset and ram address for this game's dol
			if fileOffset + size > self.maxDolOffset: self.maxDolOffset = fileOffset + size
			if memAddress + size > self.maxRamAddress: self.maxRamAddress = memAddress + size

		# Combine data points into a single definition for each data section
		for i in xrange( 10 ): # No more than 10 possible
			listIndex = i * 4
			fileOffset = toInt( dataFileOffsets[listIndex:listIndex+4] )
			memAddress = toInt( '\x00' + dataMemAddresses[listIndex+1:listIndex+4] )
			size = toInt( dataSizes[listIndex:listIndex+4] )
			if fileOffset == 0 or memAddress == 0 or size == 0: break
			self.sectionInfo['data'+str(i)] = ( fileOffset, memAddress, size )

			# Find the max possible dol offset and ram address for this game's dol
			if fileOffset + size > self.maxDolOffset: self.maxDolOffset = fileOffset + size
			if memAddress + size > self.maxRamAddress: self.maxRamAddress = memAddress + size

	def loadCustomCodeRegions( self ):

		""" Loads and validates the custom code regions available for this DOL revision.
			Filters out regions pertaining to other revisions, and those that fail basic validation. """

		incompatibleRegions = []

		print '\nLoading custom code regions....'

		# Load all regions applicable to this DOL (even if disabled in options)
		for fullRegionName, regions in settingsFile.customCodeRegions.items():
			revisionList, regionName = parseSettingsFileRegionName( fullRegionName )

			# Skip recent 20XX regions if this is not a recent 20XX DOL (v4.07++ or higher)
			# if not self.is20XX and regionName.startswith( '20XXHP' ):
			# 	continue

			# Check if the region/version of these regions are relavant to the currently loaded DOL revision
			if 'ALL' in revisionList or self.revision in revisionList:

				# Validate the regions; perform basic checks that they're valid ranges for this DOL
				for i, ( regionStart, regionEnd ) in enumerate( regions, start=1 ):

					# Check that the region start is actually smaller than the region end
					if regionStart >= regionEnd:
						msg( 'Warning! The starting offset for region ' + str(i) + ' of "' + regionName + '" for ' + self.revision + ' is greater or '
							 "equal to the ending offset. A region's starting offset must be smaller than the ending offset.", 'Invalid Custom Code Region' )
						incompatibleRegions.append( regionName )
						break

					# Check that the region start is within the DOL's code or data sections
					elif regionStart < 0x100 or regionStart >= self.maxDolOffset:
						print "Region start (0x{:X}) for {} is outside of the DOL's code\\data sections.".format( regionStart, regionName )
						incompatibleRegions.append( regionName )
						break

					# Check that the region end is within the DOL's code or data sections
					elif regionEnd > self.maxDolOffset:
						print "Region end (0x{:X}) for {} is outside of the DOL's code\\data sections.".format( regionEnd, regionName )
						incompatibleRegions.append( regionName )
						break

				# Regions validated; allow them to show up in the GUI (Code-Space Options)
				if regionName not in incompatibleRegions:
					self.customCodeRegions[regionName] = regions

		if incompatibleRegions: 
			print ( '\nThe following regions are incompatible with the ' + self.revision + ' DOL, '
					'because one or both offsets fall outside of the offset range of the file:\n\n\t' + '\n\t'.join(incompatibleRegions) + '\n' )


class geckoInitializer( object ):

	""" Validates Gecko configuration settings in the settings.py file, collects info, and ensures Gecko codes can be utilzed. """

	def __init__( self ):
		self.reset()

	def reset( self ):
		self.environmentSupported = False
		self.hookOffset = -1
		self.codelistRegion = ''
		self.codelistRegionStart = self.codelistRegionEnd = -1
		self.codehandlerRegion = ''
		self.codehandlerRegionStart = self.codehandlerRegionEnd = -1
		self.codehandler = bytearray()
		self.codehandlerLength = 0
		self.spaceForGeckoCodelist = 0
		self.spaceForGeckoCodehandler = 0
		#self.geckoConfigWarnings = [] # todo: better practice to use this to remember them until the user 
									   # tries to enable Gecko codes (instead of messaging the user immediately)

		# Check for a dictionary on Gecko configuration settings; this doesn't exist in pre-v4.0 settings files
		self.geckoConfig = getattr( settingsFile, "geckoConfiguration", {} )

	def checkSettings( self ):
		self.reset()

		if not dol.revision: return

		self.setGeckoHookOffset()
		if self.hookOffset == -1:
			msg( 'Warning! No geckoConfiguration properties could be found in the settings.py file for DOL revision "' + dol.revision + '".'
				 'Gecko codes cannot be used until this is resolved.', 'Gecko Misconfiguration' )
			return

		self.codelistRegionStart, self.codelistRegionEnd = self.getCodelistRegion()
		if self.codelistRegionStart == -1: return

		self.codehandlerRegionStart, self.codehandlerRegionEnd = self.getCodehandlerRegion()
		if self.codehandlerRegionStart == -1: return

		self.codehandler = self.getGeckoCodehandler()

		self.spaceForGeckoCodelist = self.codelistRegionEnd - self.codelistRegionStart
		self.spaceForGeckoCodehandler = self.codehandlerRegionEnd - self.codehandlerRegionStart

		# Check that the codehandler can fit in the space defined for it
		if self.codehandlerLength > self.spaceForGeckoCodehandler:
			msg( 'Warning! The region designated to store the Gecko codehandler is too small! The codehandler is ' + uHex( self.codehandlerLength ) + ' bytes '
				 'in size, while the region defined for it is ' + uHex( self.spaceForGeckoCodehandler) + ' bytes long (only the first section among those '
				 'regions will be used). Gecko codes cannot be used until this is resolved.', 'Gecko Misconfiguration' )

		else: 
			# If this has been reached, everything seems to check out.
			self.environmentSupported = True

		# Set the maximum value for the gecko code fill meter
		freeGeckoSpaceIndicator['maximum'] = self.spaceForGeckoCodelist

	def setGeckoHookOffset( self ):
		
		""" Checks for the geckoConfiguration dictionary in the config file, and gets the hook offset for the current revision. """

		if not self.geckoConfig: # For backwards compatability with pre-v4.0 config file.
			oldHooksDict = getattr( settingsFile, "geckoHookOffsets", {} )

			if not oldHooksDict:
				self.hookOffset = -1
			else:
				if dol.region == 'PAL':
					self.hookOffset = oldHooksDict['PAL']
				else: self.hookOffset = oldHooksDict[dol.version]

		# The usual expectation for v4.0+ settings files
		elif self.geckoConfig:
			self.hookOffset = self.geckoConfig['hookOffsets'].get( dol.revision, -1 ) # Assigns -1 if this dol revision isn't found

	def getCodelistRegion( self ):
		# Get the region defined in settings.py that is to be used for the Gecko codelist
		if not self.geckoConfig and dol.isMelee: # For backwards compatability with pre-v4.0 config file.
			self.codelistRegion = 'DebugModeRegion'

		elif self.geckoConfig:
			self.codelistRegion = self.geckoConfig['codelistRegion']

		# Check for the codelist region among the defined regions, and get its first DOL area
		if self.codelistRegion in dol.customCodeRegions:
			return dol.customCodeRegions[self.codelistRegion][0]
		else:
			msg( 'Warning! The region assigned for the Gecko codelist (under geckoConfiguration in the settings.py file) could not '
				 'be found among the code regions defined for ' + dol.revision + '. Double check the spelling, '
				 'and keep in mind that the strings are case-sensitive. Gecko codes cannot be used until this is resolved.', 'Gecko Misconfiguration' )
			self.codelistRegion = ''
			return ( -1, -1 )

	def getCodehandlerRegion( self ):
		# Get the region defined in settings.py that is to be used for the Gecko codehandler
		if not self.geckoConfig and dol.isMelee: # For backwards compatability with pre-v4.0 config file.
			self.codehandlerRegion = 'AuxCodeRegions'

		elif self.geckoConfig:
			self.codehandlerRegion = self.geckoConfig['codehandlerRegion']

		# Check for the codehandler region among the defined regions, and get its first DOL area
		if self.codehandlerRegion in dol.customCodeRegions:
			return dol.customCodeRegions[self.codehandlerRegion][0]
		else:
			msg( 'Warning! The region assigned for the Gecko codehandler (under geckoConfiguration in the settings.py file) could not '
				 'be found among the code regions defined for ' + dol.revision + '. Double check the spelling, '
				 'and keep in mind that the strings are case-sensitive. Gecko codes cannot be used until this is resolved.', 'Gecko Misconfiguration' )
			self.codehandlerRegion = ''
			return ( -1, -1 )

	def getGeckoCodehandler( self ):
		# Get the Gecko codehandler from an existing .bin file if present, or from the settings.py file
		if os.path.exists( scriptHomeFolder + '\\codehandler.bin' ):
			with open( scriptHomeFolder + '\\codehandler.bin', 'rb' ) as binFile:
				geckoCodehandler = bytearray( binFile.read() )
		else:
			geckoCodehandler = bytearray.fromhex( settingsFile.geckoCodehandler )

		# Append any padding needed to align its length to 4 bytes (so that any codes applied after it will be aligned).
		self.codehandlerLength = len( geckoCodehandler )
		totalRequiredCodehandlerSpace = roundTo32( self.codehandlerLength, base=4 ) # Rounds up to closest multiple of 4 bytes
		paddingLength = totalRequiredCodehandlerSpace - self.codehandlerLength # in bytes
		padding = bytearray( paddingLength )
		geckoCodehandler.extend( padding ) # Extend returns nothing

		return geckoCodehandler


def loadGeneralOptions():

	""" Check for user defined settings / persistent memory, from the "options.ini" file. 
		If values don't exist in it for particular settings, defaults are loaded from the 'generalOptionDefaults' dictionary. """

	# Read the file if it exists (this should create it if it doesn't)
	if os.path.exists( genGlobals['optionsFilePath'] ):
		settings.read( genGlobals['optionsFilePath'] )

	# Add the 'General Settings' section if it's not already present
	if not settings.has_section( 'General Settings' ):
		settings.add_section( 'General Settings' )

	# Set default [hardcoded] settings only if their values don't exist in the options file; don't want to modify them if they're already set.
	for key, option in generalOptionDefaults.items():
		if not settings.has_option( 'General Settings', key ): settings.set( 'General Settings', key, option )

	onlyUpdateGameSettings.set( settings.getboolean( 'General Settings', 'onlyUpdateGameSettings' ) ) # Sets a booleanVar for the GUI


def getModsFolderPath( getAll=False ):

	pathsString = settings.get( 'General Settings', 'modsFolderPath' )
	pathsList = csv.reader( [pathsString] ).next()

	if getAll:
		return pathsList
		
	pathIndex = int( settings.get('General Settings', 'modsFolderIndex') )

	if pathIndex < 0 or pathIndex >= len( pathsList ):
		print 'Invalid mods library path index:', pathIndex
		return pathsList[0]

	return pathsList[pathIndex]


def loadRegionOverwriteOptions():

	""" Checks saved options (the options.ini file) for whether or not custom code regions are selected for use (i.e. can be overwritten). 
		This is called just before scanning/parsing mod libraries, checking for enabled codes, or installing a mods list. 
		Creates new BooleanVars only on first run, which should exist for the life of the program (they will only be updated after that). """

	# Check for options file / persistent memory.
	if os.path.exists( genGlobals['optionsFilePath'] ): settings.read( genGlobals['optionsFilePath'] )
	if not settings.has_section( 'Region Overwrite Settings' ): settings.add_section( 'Region Overwrite Settings' )

	# Create BooleanVars for each defined region. These will be used to track option changes
	for regionName in dol.customCodeRegions.keys():
		# Create a new boolVar entry for this region.
		if regionName not in overwriteOptions: # This function may have already been called (s)
			overwriteOptions[ regionName ] = BooleanVar()

		# If the options file contains an option for this region, use it.
		if settings.has_option( 'Region Overwrite Settings', regionName ):
			overwriteOptions[ regionName ].set( settings.getboolean( 'Region Overwrite Settings', regionName ) )

		# Otherwise, set a default for this region's use.
		else: overwriteOptions[ regionName ].set( False )

	# Set the option for allowing Gecko codes, if it doesn't already exist (initial program load)
	if 'EnableGeckoCodes' not in overwriteOptions:
		overwriteOptions[ 'EnableGeckoCodes' ] = BooleanVar()

	# First check whether a setting already exists for this in the options file
	if settings.has_option( 'Region Overwrite Settings', 'EnableGeckoCodes' ):
		allowGeckoCodes = settings.getboolean( 'Region Overwrite Settings', 'EnableGeckoCodes' )
	else: # The option doesn't exist in the file
		allowGeckoCodes = False

	if not dol.data:
		overwriteOptions[ 'EnableGeckoCodes' ].set( allowGeckoCodes )
		return # No file loaded; can't confirm gecko settings are valid
	
	# Check that the gecko configuration in settings.py are valid
	if not allowGeckoCodes or not gecko.environmentSupported:
		overwriteOptions[ 'EnableGeckoCodes' ].set( False )

	else: # Make sure the appropriate regions required for gecko codes are also set.
		if overwriteOptions[ gecko.codelistRegion ].get() and overwriteOptions[ gecko.codehandlerRegion ].get():
			overwriteOptions[ 'EnableGeckoCodes' ].set( True )
		else:
			promptToUser = ( 'The option to enable Gecko codes is set, however the regions required for them, '
				'the ' + gecko.codelistRegion + ' and ' + gecko.codehandlerRegion + ', are not set for use (i.e for partial or full overwriting).'
				'\n\nDo you want to allow use of these regions \nin order to allow Gecko codes?' )
			willUserAllowGecko( promptToUser, False, root ) # Will prompt the user with the above message and set the overwriteOption


def loadImageBank():

	""" Loads and stores images required by the GUI. This allows all of the images to be 
		stored together in a similar manner, and ensures references to all of the loaded 
		images are stored, which prevents them from being garbage collected (which would 
		otherwise cause them to disappear from the GUI after rendering is complete). The 
		images are only loaded when first requested, and then kept for future reference. """

	loadFailed = []

	for item in os.listdir( os.path.join( scriptHomeFolder, 'imgs' ) ):
		if not item.endswith( '.png' ): continue
		
		filepath = os.path.join( scriptHomeFolder, 'imgs', item )

		try: 
			imageBank[item[:-4]] = ImageTk.PhotoImage( Image.open(filepath) )
		except: loadFailed.append( filepath )

	if loadFailed:
		msg( 'Unable to load some images:\n\n' + '\n'.join(loadFailed) )


def openFileByField( event ):

	""" Called by the user pressing Enter in the "ISO / DOL" field. Simply attempts 
		to load whatever path is in the text field. """

	readRecievedFile( openedFilePath.get().replace('"', '') )
	playSound( 'menuChange' )

	# Move the cursor position to the end of the field (default is the beginning)
	event.widget.icursor( Tkinter.END )


def openFileByButton():

	""" Called by the "Open" button. Prompts the user for a file to open, and then 
		attempts to open it. """

	# Set the default file formats to choose from in the file chooser dialog box
	defaultFileFormat = settings.get( 'General Settings', 'defaultFileFormat' )
	if defaultFileFormat.lower() == 'dol' or defaultFileFormat.lower() == '.dol':
		filetypes = [ ('Melee executable', '*.dol'), ('Disc image files', '*.iso *.gcm'), ('all files', '*.*') ]
	else: filetypes = [ ('Disc image files', '*.iso *.gcm'), ('Melee executable', '*.dol'), ('all files', '*.*') ]

	# Present a file chooser dialog box to the user
	filepath = tkFileDialog.askopenfilename(
		title="Choose a DOL or disc image file to open.", 
		initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
		defaultextension=defaultFileFormat,
		filetypes=filetypes
		)

	if filepath:
		readRecievedFile( filepath )
		playSound( 'menuChange' )


def restoreOriginalDol():
	if problemWithDol(): return
	elif not dol.revision:
		msg( 'The revision of the currently loaded DOL could not be determined.' )
		return

	restoreConfirmed = tkMessageBox.askyesno( 'Restoration Confirmation', 'This will revert the currently loaded DOL to be practically '
											  'identical to a vanilla ' + dol.revision + ' DOL (loaded from the "Original DOLs" folder). '
											  '"Free space" regions selected for use will still be zeroed-out. This process does not preserve '
											  'a copy of the current DOL, and any current changes will be lost.\n\nAre you sure you want to do this?' )
	if restoreConfirmed:
		vanillaDol = loadVanillaDol() # Should prompt the user with details if there's a problem here

		if vanillaDol and vanillaDol.data:
			# Seems that the original DOL was loaded successfully. Perform the data replacement.
			dol.data = vanillaDol.data # Will be re-signed when the user saves.

			# Rescan for mods
			checkForEnabledCodes()

			# Ensure that the save buttons are enabled
			saveChangesBtn.config( state='normal' )
			saveChangesBtn2.config( state='normal' )

			# Provide user feedback
			playSound( 'menuChange' )
			programStatus.set( 'Restoration Successful' )

		else:
			programStatus.set( 'Restoration Unsuccessful' )


def readRecievedFile( filepath, defaultProgramStatus='', checkForCodes=True ):
	if dol.isLoading: # Simple failsafe
		discVersion.set( '' )
		dolVersion.set( 'File already loading!' )
		return

	# Reset/clear the gui.
	discVersion.set( '' )
	programStatus.set( defaultProgramStatus )
	openedFilePath.set( '' )
	dolVersion.set( 'Nothing Loaded' )
	showRegionOptionsBtn.config( state='disabled' )
	exportFileBtn.config( state='disabled' )
	importFileBtn.config( state='disabled' )
	restoreDolBtn.config( state='disabled' )

	# Validate the given path, and update the default search directory and file format settings
	normalizedPath = os.path.normpath( filepath ).replace('{', '').replace('}', '')
	if not normalizedPath or not os.path.exists( normalizedPath ):
		saveChangesBtn.config( state='disabled' )
		saveChangesBtn2.config( state='disabled' )
		saveChangesAsBtn.config( state='disabled' )
		saveChangesAsBtn2.config( state='disabled' )
		msg( 'Unable to find this file: "' + normalizedPath + '".', 'Invalid Filepath' )
		return

	else: # File seems good
		saveChangesAsBtn.config( state='normal' )
		saveChangesAsBtn2.config( state='normal' )
		# The other standard save buttons will become enabled once changes are detected.

	# Load the DOL file to be modded (from a disc or DOL file path)
	# tic = time.clock()
	dol.load( normalizedPath )
	# toc = time.clock()
	# print '\nDOL load time:', toc-tic
	dol.loadCustomCodeRegions()

	# Remember the given path and file type for later defaults
	settings.set( 'General Settings', 'defaultSearchDirectory', os.path.dirname( normalizedPath ).encode('utf-8').strip() )
	settings.set( 'General Settings', 'defaultFileFormat', os.path.splitext( normalizedPath )[1].replace('.', '').encode('utf-8').strip() )
	saveOptions()

	# Update the GUI with the ISO/DOL's details
	if dol.revision: dolVersion.set( dol.version + ' DOL Detected' )
	else: dolVersion.set( 'Unknown DOL Revision' )
	openedFilePath.set( normalizedPath.replace('"', '') )
	showRegionOptionsBtn.config( state='normal' )
	if dol.type == 'iso' or dol.type == 'gcm':
		if dol.discVersion: discVersion.set( dol.discVersion + ' Disc,' )
		exportFileBtn.config( state='normal' )
	elif dol.type == 'dol': importFileBtn.config( state='normal' )
	restoreDolBtn.config( state='normal' )

	# Enable buttons on the Summary tab
	for widget in summaryTabFirstRow.rightColumnFrame.winfo_children():
		widget['state'] = 'normal'

	# Validate the settings.py file for parameters on the installation of Gecko codes
	gecko.checkSettings()

	# Output some info to console
	if 1:
		print '\nPath:', '\t', dol.path
		print 'File Type:', '\t', dol.type
		print 'Disc Version:', '\t', dol.discVersion
		print 'DOL Offset:', '\t', hex( dol.offset )
		print 'DOL Size:', '\t', hex( len(dol.data) /2 )
		print 'DOL Region:', '\t', dol.region
		print 'DOL Version:', '\t', dol.version
		print 'Is Melee:', '\t', dol.isMelee
		print 'Is 20XX: ', '\t', dol.is20XX
		print 'Max DOL Offset:', hex( dol.maxDolOffset )
		print 'bssMemAddress:', hex( dol.bssMemAddress ).replace('L', '')
		print 'bssSize:', hex( dol.bssSize )
		print 'entryPoint:', hex( dol.entryPoint ).replace('L', '')

		if 1: # DOL Section printout
			print '\n\tfO, RAM, size'
			for sectionName, ( fileOffset, memAddress, size ) in dol.sectionInfo.items():
				print sectionName + ':', hex(fileOffset), hex(memAddress), hex(size)
		
			for regionName, regions in dol.customCodeRegions.items():
				print '\n\t', regionName + ':\t', [(hex(start), hex(end)) for start, end in regions]

		# Gecko configuration printout
		print '\nGecko configuration:'
		for key, value in gecko.__dict__.items():
			if key == 'codehandler': continue

			if type( value ) == int:
				print '\t', key + ':', hex(value)
			else:
				print '\t', key + ':', value
		print ''

	if checkForCodes and dol.data:
		collectAllStandaloneFunctions()
		checkForEnabledCodes()


def isSpecialBranchSyntax( code ):

	""" Identifies syntaxes such as "bl 0x800948a8" or "bl <functionName>". 
		Comments should already have been removed by this point. """

	lineParts = code.split()

	if code.lower().startswith( 'b' ) and len( lineParts ) == 2:
		targetDescriptor = lineParts[1]
		if targetDescriptor.startswith('0x8') and len( targetDescriptor ) == 10: return True # Using a RAM address
		elif isStandaloneFunctionHeader( targetDescriptor ): return True # Using a function name
		
	return False


def isStandaloneFunctionHeader( targetDescriptor ):

	""" Identifies a string representing a standalone function. Usually a text line for a mod description 
		header, but may also be used to help recognize the latter half (i.e. target descriptor) of a 
		special branch syntax (such as the '<ShineActionState>' from 'bl <ShineActionState>').
		Comments should already have been removed by this point. """

	if targetDescriptor.startswith('<') and '>' in targetDescriptor and not ' ' in targetDescriptor.split( '>' )[:1]:
		return True
	else:
		return False


def containsPointerSymbol( codeLine ): # Comments should already be excluded

	""" Returns a list of names, but can also just be evaluated as True/False. """

	symbolNames = []

	if '<<' in codeLine and '>>' in codeLine:
		for block in codeLine.split( '<<' )[1:]: # Skips first block (will never be a symbol)
			if '>>' in block:
				for potentialName in block.split( '>>' )[:-1]: # Skips last block (will never be a symbol)
					if potentialName != '' and ' ' not in potentialName: 
						symbolNames.append( potentialName )
	
	return symbolNames


def isGeckoCodeHeader( codeline ): # Should return True for short header lines such as '1.02', 'PAL', 'ALL', etc (old syntaxes), or 'NTSC 1.02', 'PAL 1.00', etc (new syntaxes)
	if codeline == '': return False

	isGeckoHeader = False
	if len( codeline ) < 10 and not '<' in codeline:
		codeline = codeline.upper()

		# Check for the old formatting first ('PAL'), or a header designating a Gecko code for all revisions ('ALL')
		if codeline == 'PAL' or codeline == 'ALL': isGeckoHeader = True

		# All other conditions should include a version number (e.g. '1.02')
		elif '.' in codeline[1:]: # Excludes first character, which may be a period indicating an assembly directive
			# Check for a short version number string (still old formatting), e.g. '1.00', '1.01'
			if len( codeline ) == 4: isGeckoHeader = True

			elif 'NTSC' in codeline or 'PAL' in codeline: isGeckoHeader = True # Should be the new syntax, e.g. 'NTSC 1.02'

	return isGeckoHeader


def normalizeRegionString( revisionString ):
	
	""" Ensures consistency in revision strings. Should produce something like 'NTSC 1.02', 'PAL 1.00', etc., or 'ALL'. """

	revisionString = revisionString.upper()
	if 'ALL' in revisionString: return 'ALL'

	# Check for a game/dol version
	verIdPosition = revisionString.find( '.' )
	if verIdPosition == -1: ver = '1.00' # The default assumption
	else: ver = revisionString[verIdPosition-1:verIdPosition+3]

	# Check for the region
	if 'PAL' in revisionString: region = 'PAL '
	else: region = 'NTSC ' # The default assumption

	return region + ver


def parseSettingsFileRegionName( fullRegionName ):
	revisionList = []
	regionName = ''

	if '|' in fullRegionName: # Using new naming convention (MCM version 4+); should start with something like 'NTSC 1.02', or 'PAL 1.00', or 'NTSC 1.02, PAL 1.00'
		revisionString, regionName = fullRegionName.split( '|' )
		revisionStringList = revisionString.split( ',' )

		for revisionString in revisionStringList: 
			normalizedRevisionString = normalizeRegionString( revisionString )

			if normalizedRevisionString == 'ALL': 
				revisionList = [ 'ALL' ]
				break
			else:
				revisionList.append( normalizedRevisionString.upper() )

	 # Attempt to match using the old (MCM v3) naming convention
	elif fullRegionName.startswith( 'v10' ):
		revisionList = [ 'NTSC 1.' + fullRegionName[2:4] ]
		regionName = fullRegionName[4:]

	elif fullRegionName.startswith( 'vPAL' ): # Using the old naming convention (MCM version 3.x)
		revisionList = [ 'PAL 1.00' ]
		regionName = fullRegionName[4:]

	elif fullRegionName.startswith( 'vAll' ):
		revisionList = [ 'ALL' ]
		regionName = fullRegionName[4:]

	else: msg( 'Warning! Invalid code region name, "' + fullRegionName + '", defined in the settings.py file.' )

	return revisionList, regionName


def parseModsLibraryFile( filepath, modModulesParent, includePaths ):

	""" This is the main parsing function for the Mods Library, which reads a single text file and creates modModules out of the mods found.
		These modules are then attached to the GUI within the given parent, a VerticalScrolledFrame. """

	geckoCodesAllowed = overwriteOptions[ 'EnableGeckoCodes' ].get()

	# Open the text file and get its contents, creating a list of raw chunks of text for each mod
	with open( filepath, 'r' ) as modFile:
		mods = modFile.read().split( '-==-' )

	# Parse each chunk of text for each mod, to get its info and code changes
	for fileIndex, mod in enumerate( mods ):
		if mod.strip() == '' or mod.lstrip()[0] == '!': continue # Skip this mod.

		if modsLibraryNotebook.stopToRescan: break
		else:
			modName = modAuth = currentRevision = ''
			modDesc = []
			customCode = []
			standaloneName = origHex = newHex = ''
			longStaticOriginal = []
			isInjectionCode = isGeckoCode = isLongStaticOriginal = isLongStaticNew = False
			currentStandaloneRevisions = []
			modType = 'static'
			basicInfoCollected = parsingErrorOccurred = False
			offsetString = ''
			reasonToDisable = ''
			missingIncludes = False
			assemblyError = False
			webLinks = [] # Will be a list of tuples, of the form (urlparseObject, comments)

			modData = {} # A dictionary that will be populated by lists of "codeChange" tuples

			# Iterate over the text/code lines for this mod
			for rawLine in mod.splitlines():
				# Separate out comments for parsing purposes.
				if '##' in rawLine:
					rawLine = rawLine.split( '##' )[0].strip() # Comments with these, '##' (hard comments), are totally ignored by the parser.

				# Separate lines of description or code text from comments
				if '#' in rawLine:
					lineParts = rawLine.split( '#' )

					# Check if this line is a url containing a fragment identifier
					if lineParts[0].lstrip().startswith( '<' ):
						# Look for the ending '>' character. Put everything to the left of it into 'line', and everything else should be a comment
						for i, part in enumerate( lineParts, start=1 ):
							if part.rstrip().endswith( '>' ):
								line = '#'.join( lineParts[:i] ).strip()
								lineComments = ' #' + '#'.join( lineParts[i:] )
								break
						else: # No ending '>'; guess this wasn't a url
							line = lineParts[0].strip() # Remove whitespace from start and end of line
							lineComments = ' #' + '#'.join( lineParts[1:] )
					else:
						line = lineParts[0].strip() # Remove whitespace from start and end of line
						lineComments = ' #' + '#'.join( lineParts[1:] )
				else:
					line = rawLine.strip()
					lineComments = ''

				if not basicInfoCollected: # The purpose of this flag is to avoid all of the extra checks in this block once this info is collected.
					# Capture the first non-blank, non-commented line for the name of the mod.
					if modName == '' and line != '':
						modName = rawLine
						continue
						
					if line.startswith( '<' ) and line.endswith( '>' ):
						potentialLink = line[1:-1].replace( '"', '' ) # Removes beginning/ending angle brackets
						webLinks.append( (potentialLink, lineComments) ) # Will be validated on GUI creation

					elif line.startswith( '[' ) and line.endswith( ']' ):
						modAuth = line.split(']')[0].replace( '[', '' )
						basicInfoCollected = True

						# if modName == 'Default Game Settings': # Expected in the 20XX HP 5.0 library
						# 	reasonToDisable = 'Use the Default Game Settings tab for these.'
						# 	break

					elif line.lower().startswith( 'customizations:' ):
						reasonToDisable = 'Customizations not supported.'
						break
					else: # Assume all other lines are more description text
						modDesc.append( rawLine )

				elif ( line.startswith('Version') or line.startswith('Revision') ) and 'Hex to Replace' in line: continue
				else: # If this is reached, the name, description, and author have been parsed.
					isVersionHeader = False
					headerStringStart = ''

					# Check if this is the start of a new code change
					if '---' in line:
						headerStringStart = line.split('---')[0].rstrip().replace(' ', '') # Left-hand strip of whitespace has already been done
						if headerStringStart: # i.e. not an empty string
							isVersionHeader = True

					# Check if it's a Gecko codes header (the version or revision should be the only thing on that line), but don't set that flag yet
					elif isGeckoCodeHeader( line ):
						isVersionHeader = True
						headerStringStart = line

					# If this is a header line (marking the start of a new code change), check for lingering collected codes that must first be added to the previous code change.
					if ( isVersionHeader or '---' in line or isStandaloneFunctionHeader(line) ) and customCode != []:

						# Perform a quick check
						# returnCode = 2
						# if len( customCode ) == 1:
						# 	customCodeLine = customCode[0].strip()
						# 	if len( customCodeLine ) == 8 and validHex( customCodeLine ):
						# 		rawCustomCode = preProcessedCustomCode = customCodeLine
						# 		returnCode = 0
						# 		#print 'skipped', customCode

						# if returnCode != 0:
						rawCustomCode = '\n'.join( customCode ).strip() # Collapses the list of collected code lines into one string, removing leading & trailing whitespace
						returnCode, preProcessedCustomCode = customCodeProcessor.preAssembleRawCode( customCode, includePaths, suppressWarnings=True )
							#print 'still processed', customCode

						# If pre-processing was successful, assemble collected info into a "code change" tuple,
						# which are of the form: ( changeType, customCodeLength, offset, originalCode, customCode, preProcessedCustomCode )
						if returnCode == 0 and preProcessedCustomCode:
							customCodeLength = getCustomCodeLength( preProcessedCustomCode )

							if isInjectionCode:
								modData[currentRevision].append( ( 'injection', customCodeLength, offsetString, origHex, rawCustomCode, preProcessedCustomCode ) )
								isInjectionCode = False
							elif isGeckoCode:
								modData[currentRevision].append( ( 'gecko', customCodeLength, '', '', rawCustomCode, preProcessedCustomCode ) )
								isGeckoCode = False
							elif standaloneName != '':
								for revision in currentStandaloneRevisions:
									if revision not in modData: modData[revision] = []
									modData[revision].append( ( 'standalone', customCodeLength, standaloneName, '', rawCustomCode, preProcessedCustomCode ) )
								currentStandaloneRevisions = []
								standaloneName = ''
							elif isLongStaticNew:
								modData[currentRevision].append( ( 'static', customCodeLength, offsetString, '\n'.join(longStaticOriginal), rawCustomCode, preProcessedCustomCode ) )
								longStaticOriginal = []
								isLongStaticNew = False
							else: # Standard static overwrite
								if not origHex or not customCode:
									cmsg( '\nProblem detected while parsing "' + modName + '" in the mod library file "' 
										+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
										'One of the inputs for a static overwrite (the original or new custom code) were found to be empty, which means that '
										'the mod is probably not formatted correctly.', 'Incorrect Mod Formatting (Error Code 04.4)' )
									parsingErrorOccurred = True
									customCode = []
									break
								elif getCustomCodeLength( origHex ) != customCodeLength: # Not pre-processing in this case since it should only be one line
									cmsg( '\nProblem detected while parsing "' + modName + '" in the mod library file "' 
										+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
										'Inputs for static overwrites (the original code and custom code) should be the same '
										'length. Original code:\n' + origHex + '\n\nCustom code:\n' + rawCustomCode, 'Incorrect Mod Formatting (Error Code 04.3)' )
									parsingErrorOccurred = True
									customCode = []
									break
								else:
									modData[currentRevision].append( ( 'static', customCodeLength, offsetString, origHex, rawCustomCode, preProcessedCustomCode ) )

						elif returnCode == 2:
							assemblyError = True
							currentStandaloneRevisions = []
							break
						elif returnCode == 3: # preProcessedCustomCode should be the missing include file name
							missingIncludes = True
							currentStandaloneRevisions = []
							break

						customCode = []

					elif line == '->': # Divider between long static overwrite original and new code.
						if isLongStaticOriginal and longStaticOriginal != []:
							isLongStaticOriginal = False
							isLongStaticNew = True
						continue

					if isVersionHeader:
						# Track the version that subsequent code lines are for
						currentRevision = normalizeRegionString( headerStringStart )
						if currentRevision not in modData: modData[currentRevision] = []

						if isGeckoCodeHeader( line ):
							isGeckoCode = True # True for just this code change, not necessarily for the whole mod, like the variable below
							modType = 'gecko'

					elif isStandaloneFunctionHeader( line ):
						modType = 'standalone'
						standaloneName, revisionIdentifiers = line.lstrip()[1:].split( '>' )

						# Parse content after the header (on the same line) to see if they are identifiers for what game version to add this for.
						if revisionIdentifiers.strip() == '':
							currentStandaloneRevisions = [ 'ALL' ]
						else:
							for revision in revisionIdentifiers.split(','):
								thisRevision = normalizeRegionString( revision )

								if thisRevision == 'ALL': # Override any versions that might already be accumulated, and set the list to just ALL
									currentStandaloneRevisions = [ 'ALL' ]
									break

								else: currentStandaloneRevisions.append( thisRevision )
						continue

					if currentRevision != '' or currentStandaloneRevisions != []: # At least one of these should be set, even for subsequent lines that don't have a version header.									
						if line and '---' in line: # Ensures the line isn't blank, and it is the start of a new code change definition
							hexCodes = [ item.strip() for item in line.replace('->', '--').split('-') if item ] # Breaks down the line into a list of values.
							if isVersionHeader: hexCodes.pop(0) # Removes the revision indicator.
						
							offsetString = hexCodes[0]
							totalValues = len( hexCodes )

							if totalValues == 1: # This is the header for a Long static overwrite (e.g. "1.02 ----- 0x804d4d90 ---"). (hexCodes would actually be just ["0x804d4d90"])
								isLongStaticOriginal = True

							elif totalValues == 2: # Should have an offset and an origHex value; e.g. from a line like "1.02 ------ 804D7A4C --- 00000000 ->"
								origHex = ''.join( hexCodes[1].replace('0x', '').split() ) # Remove whitespace

								if not validHex( origHex ): # This is the game's original code, so it should just be hex.
									msg( 'Problem detected while parsing "' + modName + '" in the mod library file "' 
										+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
										'There is an invalid (non-hex) original hex value: ' + origHex, 'Incorrect Mod Formatting (Error Code 04.2)' )
									parsingErrorOccurred = True
									customCode = []
									break

							elif totalValues > 2: # Could be a standard static overwrite (1-liner), long static overwrite, or an injection mod
								origHex = ''.join( hexCodes[1].replace('0x', '').split() ) # Remove whitespace
								newHex = hexCodes[2]

								if newHex.lower() == 'branch': 
									isInjectionCode = True # Will later be switched back off, which is why this is separate from the modType variable below
									if modType == 'static': modType = 'injection' # 'static' is the only type that 'injection' can override.
									
								else: 
									# If the values exist and are valid, add a codeChange tuple to the current game version changes list.
									if not validHex( offsetString.replace( '0x', '' ) ): # Should just be a hex offset.
										msg( 'Problem detected while parsing "' + modName + '" in the mod library file "' 
											+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
											'There is an invalid (non-hex) offset value: ' + offsetString, 'Incorrect Mod Formatting (Error Code 04.1)' )
										parsingErrorOccurred = True
										customCode = []
										break
									elif not validHex( origHex ): # This is the game's original code, so it should just be hex.
										msg( 'Problem detected while parsing "' + modName + '" in the mod library file "' 
											+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
											'There is an invalid (non-hex) original hex value: ' + origHex, 'Incorrect Mod Formatting (Error Code 04.2)' )
										parsingErrorOccurred = True
										customCode = []
										break
									else:
										customCode.append( newHex + lineComments )

							if not offsetString.startswith( '0x' ):
								offsetString = '0x' + offsetString

						elif not isVersionHeader:
							if isLongStaticOriginal:
								longStaticOriginal.append( line )

							else: # This may be an empty line/whitespace. Only adds this if there is already custom code accumulating for something.
								customCode.append( rawLine )

			# End of per-line loop for the current mod (all lines have now been gone through).
			# If there is any code left, save it to the last version codeset.
			if customCode != [] or currentStandaloneRevisions != []:
				rawCustomCode = '\n'.join( customCode ).strip()
				returnCode, preProcessedCustomCode = customCodeProcessor.preAssembleRawCode( customCode, includePaths, suppressWarnings=True )

				if returnCode == 0 and preProcessedCustomCode:
					customCodeLength = getCustomCodeLength( preProcessedCustomCode )

					if isInjectionCode: 	modData[currentRevision].append( ( 'injection', customCodeLength, offsetString, origHex, rawCustomCode, preProcessedCustomCode ) )
					elif isGeckoCode: 		modData[currentRevision].append( ( 'gecko', customCodeLength, '', '', rawCustomCode, preProcessedCustomCode ) )
					elif standaloneName:
						for revision in currentStandaloneRevisions:
							if revision not in modData: modData[revision] = []
							modData[revision].append( ( 'standalone', customCodeLength, standaloneName, '', rawCustomCode, preProcessedCustomCode ) )
					elif isLongStaticNew:
						modData[currentRevision].append( ( 'static', customCodeLength, offsetString, '\n'.join(longStaticOriginal), rawCustomCode, preProcessedCustomCode ) )
					else: # standard static (1-liner)
						if not origHex or not newHex:
							cmsg( '\nProblem detected while parsing "' + modName + '" in the mod library file "' 
								+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
								'One of the inputs for a static overwrite (origHex or newHex) were found to be empty, which means that '
								'the mod is probably not formatted correctly.', 'Incorrect Mod Formatting (Error Code 04.4)' )
							parsingErrorOccurred = True
							customCode = []
							break
						elif getCustomCodeLength( origHex ) != customCodeLength:
							cmsg( '\nProblem detected while parsing "' + modName + '" in the mod library file "' 
								+ os.path.basename( filepath ) + '" (index ' + str(fileIndex+1) + ').\n\n'
								'Inputs for static overwrites (the original code and custom code) should be the same '
								'length. Original code:\n' + origHex + '\n\nCustom code:\n' + newHex, 'Incorrect Mod Formatting (Error Code 04.3)' )
							parsingErrorOccurred = True
							customCode = []
							break
						else:
							modData[currentRevision].append( ( 'static', customCodeLength, offsetString, origHex, rawCustomCode, preProcessedCustomCode ) )

				elif returnCode == 2:
					assemblyError = True
				elif returnCode == 3:
					missingIncludes = True

			# If codes were found for the current mod, create a gui element for it and populate it with the mod's details.
			if not modsLibraryNotebook.stopToRescan: # This might be queued in order to halt and restart the scan
				# Create a new module in the GUI, both for user interaction and data storage
				newModModule = ModModule( modModulesParent, modName, '\n'.join(modDesc).strip(), modAuth, modData, modType, webLinks )
				newModModule.pack( fill='x', expand=1 )
				newModModule.sourceFile = filepath
				newModModule.fileIndex = fileIndex
				newModModule.includePaths = includePaths
				genGlobals['allMods'].append( newModModule )

				# Set the mod widget's status and add it to the global allModNames list
				if reasonToDisable: newModModule.setState( 'unavailable', specialStatusText=reasonToDisable )
				elif modData == {}: newModModule.setState( 'unavailable', specialStatusText='Missing mod data.' )
				elif parsingErrorOccurred: newModModule.setState( 'unavailable', specialStatusText='Error detected during parsing.' )
				elif assemblyError: newModModule.setState( 'unavailable', specialStatusText='Error during assembly' )
				elif missingIncludes: newModModule.setState( 'unavailable', specialStatusText='Missing include file: ' + preProcessedCustomCode )
				else:
					# No problems detected so far. Check if this is a duplicate mod, and add it to the list of all mods if it's not
					if modName in genGlobals['allModNames']:
						newModModule.setState( 'unavailable', specialStatusText='Duplicate Mod' )
					else:
						genGlobals['allModNames'].add( modName )

					if modType == 'gecko' and not geckoCodesAllowed:
						newModModule.setState( 'unavailable' )
					elif settingsFile.alwaysEnableCrashReports and modName == "Enable OSReport Print on Crash":
						newModModule.setState( 'pendingEnable' )


class CodeMod( object ):

	""" Basically just a data container for now. So far only used for the new ASM Mod Folder Structure (AMFS). 
		For parsing of MCM's usual format, see the parseModsLibraryFile function above. """

	def __init__( self, name, auth='', desc='', srcPath='', isAmfs=False ):

		self.name = name
		self.auth = auth
		self.desc = desc
		self.type = 'static'
		self.data = {} 			# A dictionary that will be populated by lists of "codeChange" tuples
		
		self.path = srcPath		# Root folder path that contains this mod
		self.isAmfs = isAmfs
		self.webLinks = []
		self.includePaths = []


class ModsLibraryParser():

	""" So far only used for the new ASM Mod Folder Structure (AMFS). For parsing 
		of MCM's usual format, see the parseModsLibraryFile function above. """

	def __init__( self, modModulesParent, includePaths ):

		self.modModulesParent = modModulesParent
		self.includePaths = includePaths
		self.errors = []

	def parseAmfs( self, folderName, fullFolderPath, jsonContents ):

		""" This method is the primary handler of the ASM Mod Folder Structure (AMFS). This will 
			create a mod container object to store the mod's code changes and other data, and 
			step through each code change dictionary in the JSON file's build list. """

		codeSection = jsonContents.get( 'codes' )

		if codeSection:
			for codeset in jsonContents['codes']:
				# Typecast the authors and description lists to strings
				authors = ', '.join( codeset['authors'] )
				description = '\n'.join( codeset['description'] )

				mod = CodeMod( codeset['name'], authors, description, fullFolderPath, True )

				# Set the revision (region/version)
				revision = codeset.get( 'revision', 'NTSC 1.02' )
				mod.revision = normalizeRegionString( revision ) # Normalize it
				mod.data[revision] = [] # Initialize a codeChange list for it

				# Load a vanilla DOL for the above revision (will only actually be loaded once)
				mod.vanillaDol = loadVanillaDol( revision ) # This will report any errors it has

				mod.assemblyError = False
				mod.parsingError = False
				mod.missingVanillaHex = False
				mod.missingIncludes = ''

				mod.includePaths = self.includePaths
				mod.webLinks = codeset.get( 'webLinks', () )

				buildSet = codeset.get( 'build' )

				if buildSet:
					for codeChangeDict in buildSet:
						codeType = codeChangeDict['type']
						
						if codeType == 'replace': # Static Overwrite; basically an 04 Gecko codetype (hex from json)
							self.parseAmfsReplace( codeChangeDict, mod )
							if mod.assemblyError or mod.missingVanillaHex or mod.missingIncludes: break

						elif codeType == 'inject': # Standard code injection
							self.parseAmfsInject( codeChangeDict, mod )
							if mod.assemblyError or mod.parsingError or mod.missingVanillaHex or mod.missingIncludes: break
							elif mod.type == 'static': mod.type = 'injection' # 'static' is the only type that 'injection' can override.

						elif codeType == 'replaceCodeBlock': # Static overwrite of variable length (hex from file)
							self.parseAmfsReplaceCodeBlock( codeChangeDict, mod )
							if mod.assemblyError or mod.missingVanillaHex or mod.missingIncludes: break

						elif codeType == 'branch' or codeType == 'branchAndLink':
							self.errors.append( 'The ' + codeType + ' AMFS code type is not yet supported' )

						elif codeType == 'injectFolder':
							self.parseAmfsInjectFolder( codeChangeDict, mod )
							if mod.assemblyError or mod.parsingError or mod.missingVanillaHex or mod.missingIncludes: break
							elif mod.type == 'static': mod.type = 'injection' # 'static' is the only type that 'injection' can override.

						elif codeType == 'replaceBinary':
							self.errors.append( 'The replaceBinary AMFS code type is not yet supported' )

						elif codeType == 'binary':
							self.errors.append( 'The binary AMFS code type is not yet supported' )

						else:
							self.errors.append( 'Unrecognized AMFS code type: ' + codeType )

					# Create a new code module, and add it to the GUI
					self.buildCodeModule( mod )

				else: # Build all subfolders/files
					self.errors.append( "No 'build' section found in codes.json" )

		else: # Grab everything from the current folder (and subfolders). Assume .s are static overwrites, and .asm are injections
			# Typecast the authors and description lists to strings
			# authors = ', '.join( codeset['authors'] )
			# description = '\n'.join( codeset['description'] )
			
			# mod = CodeMod( codeset['name'], authors, description, fullFolderPath, True )

			self.errors.append( "No 'codes' section found in codes.json" ) #todo

	def buildCodeModule( self, mod ):

		""" Builds a code module for the GUI, sets its status, and adds it to the interface. """

		# Create a new module in the GUI, both for user interaction and data storage
		newModModule = ModModule( self.modModulesParent, mod.name, mod.desc, mod.auth, mod.data, mod.type, mod.webLinks )
		newModModule.pack( fill='x', expand=1 )
		newModModule.sourceFile = mod.path
		newModModule.fileIndex = 0
		newModModule.includePaths = mod.includePaths
		genGlobals['allMods'].append( newModModule )

		# Set the mod widget's status and add it to the global allModNames list
		if mod.data == {}: newModModule.setState( 'unavailable', specialStatusText='Missing mod data.' )
		elif mod.parsingError: newModModule.setState( 'unavailable', specialStatusText='Error detected during parsing.' )
		elif mod.missingVanillaHex: newModModule.setState( 'unavailable', specialStatusText='Unable to get vanilla hex' )
		elif mod.assemblyError: newModModule.setState( 'unavailable', specialStatusText='Error during assembly' )
		elif mod.missingIncludes: newModModule.setState( 'unavailable', specialStatusText='Missing include file: ' + mod.missingIncludes )
		else:
			# No problems detected so far. Check if this is a duplicate mod, and add it to the list of all mods if it's not
			if mod.name in genGlobals['allModNames']:
				newModModule.setState( 'unavailable', specialStatusText='Duplicate Mod' )
			else:
				genGlobals['allModNames'].add( mod.name )

			if mod.type == 'gecko' and not overwriteOptions[ 'EnableGeckoCodes' ].get():
				newModModule.setState( 'unavailable' )
			elif settingsFile.alwaysEnableCrashReports and mod.name == "Enable OSReport Print on Crash":
				newModModule.setState( 'pendingEnable' )

		if self.errors:
			print '\nFinal errors:', '\n'.join( self.errors )

	def parseAmfsReplace( self, codeChangeDict, mod ):

		""" AMFS Static Overwrite of 4 bytes; custom hex code sourced from json file. """

		# Pre-process the custom code (make sure there's no whitespace, and/or assemble it)
		customCode = codeChangeDict['value']
		returnCode, preProcessedCustomCode = customCodeProcessor.preAssembleRawCode( customCode, mod.includePaths, suppressWarnings=True )
		if returnCode in ( 1, 2 ):
			mod.assemblyError = True
			self.errors.append( "Encountered a problem while assembling a 'replace' code change" )
			return
		elif returnCode == 3: # Missing an include file
			mod.missingIncludes = preProcessedCustomCode # The custom code string will be the name of the missing include file
			self.errors.append( "Unable to find this include file: " + preProcessedCustomCode )
			return
		
		# Get the offset of the code change, and the original code at that location
		offset = codeChangeDict['address']
		dolOffset = normalizeDolOffset( offset, dolObj=mod.vanillaDol )
		origHex = getVanillaHex( dolOffset, revision=mod.revision, suppressWarnings=False )
		if not origHex:
			mod.missingVanillaHex = True
			self.errors.append( "Unable to get original code for a 'replace' code change" )
			return

		# Preserve the annotation using a comment
		annotation = codeChangeDict.get( 'annotation', None )
		if annotation:
			customCode += ' # ' + annotation

		mod.data[mod.revision].append( ('static', 4, offset, origHex, customCode, preProcessedCustomCode) )

	def readInjectionAddressHeader( self, asmFile ):
		# Parse the first line to get an injection site (offset) for this code
		headerLine = asmFile.readline()

		# Check for the original 1-line format
		if headerLine.startswith( '#' ) and 'inserted' in headerLine:
			return headerLine.split()[-1] # Splits by whitespace and gets the resulting last item

		# Check for the multi-line format
		elif headerLine.startswith( '#######' ):
			while 1:
				line = asmFile.readline()
				if 'Address:' in line:
					return line.split()[2]
				elif line.startswith( '#######' ):
					return -1 # Failsafe; reached the end of the header without finding the address

	def getCustomCodeFromFile( self, fullAsmFilePath, mod, parseOffset=False, annotation='' ):

		""" Gets custom code from a given file and pre-processes it (removes whitespace, and/or assembles it). 
			If parseOffset is False, the offset in the file header isn't needed because the calling function 
			already has it from a codeChange dictionary. If it does need to be parsed, the calling function 
			only had a sourceFile for reference (most likely through a injectFolder code type). """

		if not annotation: # Use the file name for the annotation (without file extension)
			annotation = os.path.splitext( os.path.basename(fullAsmFilePath) )[0]
		
		# Get the custom code, and the address/offset if needed
		try:
			# Open the file in byte-reading mode (rb). Strings will then need to be encoded.
			with codecs.open( fullAsmFilePath, encoding='utf-8' ) as asmFile: # Using a different read method for UTF-8 encoding
				if parseOffset:
					offset = self.readInjectionAddressHeader( asmFile )
					decodedString = asmFile.read().encode( 'utf-8' )
					customCode = '# {}\n{}'.format( annotation, decodedString )
				else:
					offset = ''

					# Clean up the header line (changing first line's "#To" to "# To")
					firstLine = asmFile.readline()
					if firstLine.startswith( '#' ):
						customCode = '# {}\n# {}\n{}'.format( annotation, firstLine.lstrip( '# '), asmFile.read().encode( 'utf-8' ) )
					else:
						customCode = '# {}\n{}\n{}'.format( annotation, firstLine, asmFile.read().encode( 'utf-8' ) )

		except IOError as err: # File couldn't be found
			mod.parsingError = True
			print err
			self.errors.append( "Unable to find the file " + os.path.basename(fullAsmFilePath) )
			return 4, '', '', ''
		except Exception as err: # Unknown error
			mod.parsingError = True
			print err
			self.errors.append( 'Encountered an error while parsing {}: {}'.format(os.path.basename(fullAsmFilePath), err) )
			return 5, '', '', ''
			
		# Pre-process the custom code (make sure there's no whitespace, and/or assemble it)
		returnCode, preProcessedCustomCode = customCodeProcessor.preAssembleRawCode( customCode, [os.path.dirname(fullAsmFilePath)] + mod.includePaths, suppressWarnings=True )

		# Check for errors
		if returnCode in ( 1, 2 ):
			mod.assemblyError = True
			self.errors.append( 'Encountered a problem while assembling ' + os.path.basename(fullAsmFilePath) )
			return returnCode, '', '', ''
		elif returnCode == 3: # Missing an include file
			mod.missingIncludes = preProcessedCustomCode # The custom code string will be the name of the missing include file
			self.errors.append( 'Unable to find this include file: ' + preProcessedCustomCode )
			return 3, '', '', ''

		return 0, offset, customCode, preProcessedCustomCode

	def parseAmfsInject( self, codeChangeDict, mod, sourceFile='' ):

		""" AMFS Injection; custom code sourced from an assembly file. """

		if not sourceFile:
			sourceFile = codeChangeDict['sourceFile'] # Relative path
			fullAsmFilePath = os.path.join( mod.path, sourceFile )
			offset = codeChangeDict['address']
			annotation = codeChangeDict.get( 'annotation', '' )
		else: # No codeChangeDict if a source file was provided (this is an inject folder being processed)
			fullAsmFilePath = sourceFile # This will be a full path in this case
			offset = ''
			annotation = ''

		# Get the custom code from the ASM file and pre-process it (make sure there's no whitespace, and/or assemble it)
		returnCode, offset, customCode, preProcessedCustomCode = self.getCustomCodeFromFile( fullAsmFilePath, mod, True, annotation )

		# Check for errors
		if returnCode != 0:
			return
		elif not offset:
			mod.parsingError = True
			self.errors.append( 'Unable to find an offset/address for ' + sourceFile )
			return

		# Normalize the offset of the code change, and get the game's original code at that location
		dolOffset = normalizeDolOffset( offset, dolObj=mod.vanillaDol )
		origHex = getVanillaHex( dolOffset, revision=mod.revision, suppressWarnings=False )
		if not origHex:
			mod.missingVanillaHex = True
			self.errors.append( 'Unable to find vanilla hex for {}. Found in {}.'.format(offset, sourceFile) )
			return

		# Get the custom code's length, and store the info for this code change
		customCodeLength = getCustomCodeLength( preProcessedCustomCode )
		if customCodeLength == 4:
			mod.data[mod.revision].append( ('static', customCodeLength, offset, origHex, customCode, preProcessedCustomCode) )
		else:
			mod.data[mod.revision].append( ('injection', customCodeLength, offset, origHex, customCode, preProcessedCustomCode) )

	def parseAmfsReplaceCodeBlock( self, codeChangeDict, mod ):

		""" AMFS Long Static Overwrite of variable length. """

		# Pre-process the custom code (make sure there's no whitespace, and/or assemble it)
		sourceFile = codeChangeDict['sourceFile'] # Expected to be there
		annotation = codeChangeDict.get( 'annotation', '' ) # May not be there
		fullAsmFilePath = '\\\\?\\' + os.path.normpath( os.path.join( mod.path, sourceFile ))
		
		# Get the custom code from the ASM file and pre-process it (make sure there's no whitespace, and/or assemble it)
		returnCode, offset, customCode, preProcessedCustomCode = self.getCustomCodeFromFile( fullAsmFilePath, mod, False, annotation )
		if returnCode != 0: return

		# Get the offset of the code change, and the original code at that location
		offset = codeChangeDict['address']
		dolOffset = normalizeDolOffset( offset, dolObj=mod.vanillaDol )
		origHex = getVanillaHex( dolOffset, revision=mod.revision, suppressWarnings=False )
		if not origHex:
			mod.missingVanillaHex = True
			self.errors.append( 'Unable to find vanilla hex for ' + offset )
			return
		
		# Get the custom code's length, and store the info for this code change
		customCodeLength = getCustomCodeLength( preProcessedCustomCode )
		mod.data[mod.revision].append( ('static', customCodeLength, offset, origHex, customCode, preProcessedCustomCode) )

	def processAmfsInjectSubfolder( self, fullFolderPath, mod, isRecursive ):

		""" Processes all files/folders in a directory """

		try:
			for item in os.listdir( fullFolderPath ):
				itemPath = os.path.join( fullFolderPath, item )

				if os.path.isdir( itemPath ) and isRecursive:
					self.processAmfsInjectSubfolder( itemPath, mod, isRecursive )
				elif itemPath.endswith( '.asm' ):
					self.parseAmfsInject( None, mod, sourceFile=itemPath )
		except WindowsError as err:
			mod.parsingError = True
			self.errors.append( 'Unable to find the folder "{}"'.format(fullFolderPath) )
			print err

	def parseAmfsInjectFolder( self, codeChangeDict, mod ):
		# Get/construct the root folder path
		sourceFolder = codeChangeDict['sourceFolder']
		sourceFolderPath = os.path.join( mod.path, sourceFolder )

		# try:
		self.processAmfsInjectSubfolder( sourceFolderPath, mod, codeChangeDict['isRecursive'] )
		# except WindowsError as err:
		#	# Try again with extended path formatting
		# 	print 'second try for', sourceFolderPath
		# 	self.processAmfsInjectSubfolder( '\\\\?\\' + os.path.normpath(sourceFolderPath), mod, codeChangeDict['isRecursive'] )


def clearModsLibraryTab():

	""" Clears the Mods Library tab's GUI (removes buttons and deletes mod modules) """

	# Remove the Mods Library selection button from the GUI
	librarySelectionLabel.place_forget()

	# Delete all mods currently populated in the GUI (by deleting the associated tab),
	# and remove any other current widgets/labels in the main notebook
	for child in modsLibraryNotebook.winfo_children():
		child.destroy()

	# Remove any description text ('Click this button to....')
	for child in modsLibraryTab.mainRow.winfo_children():
		if child.winfo_class() == 'TLabel' and child != librarySelectionLabel:
			child.destroy()


def placeModLibrarySelectionBtn( placeLibrarySelectionBtnDescriptor ):

	if len( modsLibraryNotebook.tabs() ) > 0: # There is space in the usual place
		librarySelectionLabel['bg'] = 'SystemButtonFace'
		librarySelectionLabel.place( anchor='e', relx=1, x=-13, y=16 )

	else: # No tabs means no usual space for this button
		librarySelectionLabel['bg'] = 'white'
		librarySelectionLabel.place( anchor='e', relx=1, x=-64, y=66 )

	if placeLibrarySelectionBtnDescriptor:
		btnDescriptor = ttk.Label( modsLibraryTab.mainRow, text='Click this button to select a directory for your Mods Library  -->', background='white' )
		btnDescriptor.place( anchor='e', relx=1, x=-120, y=66 )


def scanModsLibrary( playAudio=True ):

	""" The primary function for processing a Mods Library. Will identify and parse the standard .txt file mod format, 
		as well as the AMFS structure. The primary .include paths for import statements are also set here. 
			Include Path Priority:
				1) The current working directory (usually the MCM root folder)
				2) Directory of the mod's code file (or the code's root folder with AMFS)
				3) The current Mods Library's ".include" directory
				4) The MCM root folder's ".include" directory """

	# If this scan is triggered while it is already running, queue/wait for the previous iteration to cancel and re-run
	if modsLibraryNotebook.isScanning:
		modsLibraryNotebook.stopToRescan = True
		return

	tic = time.clock()

	# Remember the currently selected tab and its scroll position.
	currentTab = getCurrentModsLibraryTab()
	lastSelectedTabFileSource = ''
	if currentTab != 'emptyNotebook':
		frameForBorder = currentTab.winfo_children()[0]
		modsPanelInterior = frameForBorder.winfo_children()[0].interior # frameForBorder -> modsPanel.interior
		lastSelectedTabFileSource = modsPanelInterior.winfo_children()[0].sourceFile # Checking the first mod of the mods panel (should all have same source file)
		sliderYPos = frameForBorder.winfo_children()[0].vscrollbar.get()[0] # .get() returns e.g. (0.49505277044854884, 0.6767810026385225)

	genGlobals['allMods'] = []
	genGlobals['allModNames'] = Set()
	modsLibraryFolder = getModsFolderPath()

	# Build the list of paths for .include script imports (this will be prepended by the folder housing each mod text file)
	includePaths = [ os.path.join(modsLibraryFolder, '.include'), os.path.join(scriptHomeFolder, '.include') ]

	clearModsLibraryTab()

	# Validate the current Mods Library folder
	if not os.path.exists( modsLibraryFolder ): 
		msg( 'Unable to find the "' + os.path.split(modsLibraryFolder)[1] + '" folder.' )

		ttk.Label( modsLibraryNotebook, text='No Mods Library directory found.', background='white' ).place( relx=.5, rely=.5, anchor='center' )
		ttk.Label( modsLibraryNotebook, image=imageBank['randall'], background='white' ).place( relx=0.5, rely=0.5, anchor='n', y=15 ) # y not :P
		placeModLibrarySelectionBtn( True )
		return

	modsLibraryNotebook.isScanning = True
	parentFrames = {} # Tracks tabs that mod modules are attached to (their parents), so the frames can be added to at any time

	# Load settings from the settings.py file
	loadRegionOverwriteOptions()

	def processItemInDir( parentDirectory, parentNotebook, fileOrFolderItem ):
		itemPath = os.path.normpath( os.path.join(parentDirectory, fileOrFolderItem) )

		# Create a new tab for the parent notebook for this item (folder or text file).
		newTab = Frame( parentNotebook )

		if os.path.isdir( itemPath ):
			# Scan this folder to determine if it's of the new ASM Mod Folder Structure (AMFS) Amphis/Amfis?
			folderItems = os.listdir( itemPath )

			if 'codes.json' in folderItems:
				# Open the json file and get its file contents (need to do this early so we can check for a mod category)
				with open( os.path.join(itemPath, 'codes.json'), 'r') as jsonFile:
					jsonContents = json.load( jsonFile )

				# Check for a mod category
				category = jsonContents.get( 'category', 'Uncategorized' )
				if category in parentFrames:
					ModsLibraryParser( parentFrames[category], [itemPath] + includePaths ).parseAmfs( fileOrFolderItem, itemPath, jsonContents )

				else: # Need to create a new parent frame and notebook
					parentNotebook.add( newTab, text=category )
					
					# Create a space for new modules, and then parse the file to populate it.
					frameForBorder = Frame( newTab, borderwidth=2, relief='groove' )
					modsPanel = VerticalScrolledFrame( frameForBorder )
						# Code modules will go here, as children of a modsPanel.
					modsPanel.pack( side='left', fill='both', expand=1 )
					frameForBorder.place( x=0, y=0, relwidth=.65, relheight=1.0 )

					ModsLibraryParser( modsPanel.interior, [itemPath] + includePaths ).parseAmfs( fileOrFolderItem, itemPath, jsonContents )
					parentFrames[category] = modsPanel.interior

					# If this tab was selected before this scan, reselect it and restore the previous scroll position.
					if itemPath == lastSelectedTabFileSource:
						if selectModLibraryTab( newTab ): # Ensures all tabs leading to this tab are all selected (multiple may be nested)
							modsPanel.canvas.yview_moveto( sliderYPos )
			else:
				parentNotebook.add( newTab, image=imageBank['folderIcon'], text=fileOrFolderItem, compound='left' )

				# Create a new Notebook object (tab group) for this directory.
				newNotebook = ttk.Notebook( newTab )
				newNotebook.pack( fill='both', expand=1 )
				newNotebook.bind( '<<NotebookTabChanged>>', onTabChange )

				processDirectory( itemPath, newNotebook ) # Recursive fun!

		elif itemPath.lower().endswith('.txt'): # This tab will be for a file.
			tabName = fileOrFolderItem[:-4] # Removes '.txt'/'.TXT' from the string.
			parentNotebook.add( newTab, text=tabName )

			# Create a space for new modules, and then parse the file to populate it.
			frameForBorder = Frame( newTab, borderwidth=2, relief='groove' )
			modsPanel = VerticalScrolledFrame( frameForBorder )
				# Code modules will go here, as children of a modsPanel.
			modsPanel.pack( side='left', fill='both', expand=1 )
			frameForBorder.place( x=0, y=0, relwidth=.65, relheight=1.0 )

			# Add all mod definitions from this file to the GUI
			parseModsLibraryFile( itemPath, modsPanel.interior, [parentDirectory] + includePaths )
			parentFrames[tabName] = modsPanel.interior

			# Update the GUI
			modsLibraryNotebook.update()

			# If this tab was selected before this scan, reselect it and restore the previous scroll position.
			if itemPath == lastSelectedTabFileSource:
				if selectModLibraryTab( newTab ): # Ensures all tabs leading to this tab are all selected (multiple may be nested)
					modsPanel.canvas.yview_moveto( sliderYPos )

	def processDirectory( parentDirectory, parentNotebook ):
		itemsInDir = os.listdir( parentDirectory )
		somethingCreated = False

		# Check if there are any items in this folder to be processed exclusively (item starting with '+')
		for fileOrFolderItem in itemsInDir:
			if fileOrFolderItem.startswith( '+' ):
				processItemInDir( parentDirectory, parentNotebook, fileOrFolderItem )
				somethingCreated = True
				break
		else: # Loop above didn't break; no item with '+' found, so process everything in this folder
			for fileOrFolderItem in itemsInDir:
				if modsLibraryNotebook.stopToRescan:
					break
				elif fileOrFolderItem.startswith( '!' ) or fileOrFolderItem.startswith( '.' ): 
					continue # User can optionally exclude these folders from parsing
				else:
					processItemInDir( parentDirectory, parentNotebook, fileOrFolderItem )
					somethingCreated = True

		if not somethingCreated:
			# Nothing in this folder. Add a label to convey this.
			Label( parentNotebook, text='No text files found here.', bg='white' ).place( relx=.5, rely=.5, anchor='center' )
			ttk.Label( parentNotebook, image=imageBank['randall'], background='white' ).place( relx=0.5, rely=0.5, anchor='n', y=15 ) # y not :P

	processDirectory( modsLibraryFolder, modsLibraryNotebook )

	def restartScan( playAudio ):
		time.sleep( .2 ) # Give a moment to allow for current settings to be saved via saveOptions.
		modsLibraryNotebook.isScanning = False
		modsLibraryNotebook.stopToRescan = False
		scanModsLibrary( playAudio )

	if modsLibraryNotebook.stopToRescan:
		restartScan( playAudio )
	else:
		toc = time.clock()
		print 'library parsing time:', toc - tic

		# Add the Mods Library selection button to the GUI
		placeModLibrarySelectionBtn( False )

		totalModsInLibraryLabel.set( 'Total Mods in Library: ' + str(len( genGlobals['allMods'] )) ) # todo: refactor code to count mods in the modsPanels instead
		#totalSFsInLibraryLabel.set( 'Total Standalone Functions in Library: ' + str(len( collectAllStandaloneFunctions(genGlobals['allMods'], forAllRevisions=True) )) )

		realignControlPanel()
		root.bind_class( 'moduleClickTag', '<1>', modModuleClicked )

		if dol.data:
			collectAllStandaloneFunctions()
			checkForEnabledCodes()
		
		if playAudio: playSound( 'menuChange' )

		# Check once more if another scan is queued. (e.g. if the scan mods button was pressed again while checking for installed mods)
		if modsLibraryNotebook.stopToRescan:
			restartScan( playAudio )
		else:
			modsLibraryNotebook.isScanning = False
			modsLibraryNotebook.stopToRescan = False


def parseGeckoCode( gameRevision, codeText ):

	""" Returns a tuple of 'title', 'author(s)', and the mod's code changes'.
		The code changes list is in the same format as those parsed by codes in MCM's
		usual format, and created internally as 'ModModule' modData dictionary entries. """

	title = authors = ''
	description = []
	codeChanges = []		# A Codechange = a tuple of ( changeType, customCodeLength, offset, originalCode, customCode, preProcessedCustomCode )
	codeBuffer = []			# Temp staging area while code lines are collected, before they are submitted to the above codeChanges list.

	# Load the DOL for this revision (if one is not already loaded), for original/vanilla code look-ups
	vanillaDol = loadVanillaDol( gameRevision )

	for line in codeText.splitlines():
		if not line: continue

		elif line.startswith( '*' ): # [Another?] form of comment
			description.append( line[1:] )

		elif line.startswith( '$' ) or ( '[' in line and ']' in line ):
			line = line.lstrip( '$' )

			# Sanity check; the buffer should be empty if a new code is starting
			if codeBuffer: 
				print 'Warning! Gecko code parsing ran into an error or an invalid code!'
				print 'The code buffer was not emptied before a new code was encountered.'
				codeBuffer = []

			if title: # It's already been set, meaning this is another separate code
				break

			if '[' in line and ']' in line:
				titleParts = line.split( '[' )
				authors = titleParts[-1].split( ']' )[0]

				title = '['.join( titleParts[:-1] )
			else:
				title = line

		elif codeBuffer: # Multi-line code collection is in-progress
			changeType, customCodeLength, ramAddress, _, collectedCodeLength = codeBuffer

			newHex = ''.join( line.split( '#' )[0].split() ) # Should remove all comments and whitespace
			newHexLength = len( newHex ) / 2 # Divide by 2 to count by bytes rather than nibbles

			if collectedCodeLength + newHexLength < customCodeLength:
				codeBuffer[3].append( newHex )
				codeBuffer[4] += newHexLength

			else: # Last line to collect from for this code change
				# Collect the remaining new hex and consolidate it
				bytesRemaining = customCodeLength - collectedCodeLength
				codeBuffer[3].append( newHex[:bytesRemaining*2] ) # x2 to count by nibbles
				rawCustomCode = ''.join( codeBuffer[3] ) # no whitespace
				customCode = customCodeProcessor.beautifyHex( rawCustomCode ) # Formats to 8 byte per line

				# Get the original/vanilla code
				intRamAddress = int( ramAddress[3:], 16 ) # Trims off leading 0x8 before conversion
				dolOffset = offsetInDOL( intRamAddress, vanillaDol.sectionInfo )
				if dolOffset == -1: originalCode = ''
				else: originalCode = vanillaDol.data[dolOffset*2:(dolOffset+4)*2].upper() # At the injection point

				# Add the finished code change to the list, and reset the buffer
				codeChanges.append( (changeType, customCodeLength, ramAddress, originalCode, customCode, rawCustomCode) )
				codeBuffer = []

		elif line.startswith( '04' ): # A Static Overwrite
			ramAddress = '0x80' + line[2:8]
			customCode = line.replace( ' ', '' )[8:16]

			# Get the vanilla code from the DOL
			dolOffset = offsetInDOL( int(line[2:8], 16), vanillaDol.sectionInfo )
			if dolOffset == -1: originalCode = ''
			else: originalCode = vanillaDol.data[dolOffset*2:(dolOffset+4)*2].upper()

			codeChanges.append( ('static', 4, ramAddress, originalCode, customCode, customCode) )

		elif line.startswith( '06' ): # A Long Static Overwrite (string write)
			ramAddress = '0x80' + line[2:8]
			totalBytes = int( line.replace( ' ', '' )[8:16], 16 )

			# Set up the code buffer, which will be filled with data until it's gathered all the bytes
			codeBuffer = [ 'static', totalBytes, ramAddress, [], 0 ]

		elif line.upper().startswith( 'C2' ): # An Injection
			ramAddress = '0x80' + line[2:8]
			totalBytes = int( line.replace( ' ', '' )[8:16], 16 ) * 8 # The count in the C2 line is a number of lines, where each line should be 8 bytes

			# Set up the code buffer, which will be filled with data until it's gathered all the bytes
			codeBuffer = [ 'injection', totalBytes, ramAddress, [], 0 ]

	return title, authors, '\n'.join( description ), codeChanges


def getGameSettingValue( widgetSettingID, settingsSource ):
	if settingsSource == 'fromDOL' and not dol.revision:
		settingsSource = 'vMeleeDefaults' # No DOL has been loaded; can't read from it

	if settingsSource == 'fromDOL': # Get the setting's current value from the DOL.
		# Determine the offset for the setting's value
		relOffset = gameSettingsTable[widgetSettingID][0]
		offset = ( settingsTableOffset[dol.revision] + relOffset ) *2 # Doubled to count by nibbles rather than bytes.
		
		if widgetSettingID == 'damageRatioSetting': value = int( dol.data[offset:offset+2], 16 ) / 10.0
		elif widgetSettingID == 'stageToggleSetting' or widgetSettingID == 'itemToggleSetting': value = dol.data[offset:offset+8]
		elif widgetSettingID == 'itemFrequencySetting':
			value = dol.data[offset:offset+2]
			if value.upper() == 'FF': value = 0
			else: value = int( value, 16 ) + 1 # Accounts for skipping 'None'
		else: value = int( dol.data[offset:offset+2], 16 )

	elif settingsSource == 'vMeleeDefaults': value = gameSettingsTable[widgetSettingID][1]
	else: value = gameSettingsTable[widgetSettingID][2]

	# If the value needs to be one of the strings, use the provided value to get the position of the needed string.
	if len( gameSettingsTable[widgetSettingID] ) > 3: value = gameSettingsTable[widgetSettingID][3+value]

	return str( value )


def updateMeleeToVanillaGameSettings():
	updateDefaultGameSettingsTab( 'vMeleeDefaults' )
	checkForPendingChanges()
	playSound( 'menuChange' )


def updateMeleeToTournamentGameSettings():
	updateDefaultGameSettingsTab( 'tourneyDefaults' )
	checkForPendingChanges()
	playSound( 'menuChange' )


def updateDefaultGameSettingsTab( settingsSource ):

	""" Called when an ISO/DOL is loaded, or a set of default settings are selected, also 
		called by checkForEnabledCodes or the buttons for loading default setting presets.
		"settingsSource" may be 'fromDOL', 'vMeleeDefaults', or 'tourneyDefaults'. """

	for widgetSettingID in gameSettingsTable:
		value = getGameSettingValue( widgetSettingID, settingsSource )

		# Update the textvariable that will be used to track changes (both internally, and for the GUI)
		currentGameSettingsValues[widgetSettingID].set( value ) # Will be converted to a string if it was an int

		# Update the control widget's appearance.
		if settingsSource != 'fromDOL':
			widgetControlID = widgetSettingID[:-7] + 'Control' # Each of these strings corresponds to a widget
			updateDefaultGameSettingWidget( widgetControlID, value, False )
	
	# Update the elements in the stage/item selections windows.
	if settingsSource == 'fromDOL': fromDOL = True
	else: fromDOL = False
	if root.stageSelectionsWindow: root.stageSelectionsWindow.updateStates( currentGameSettingsValues['stageToggleSetting'].get(), fromDOL, False )
	if root.itemSelectionsWindow: root.itemSelectionsWindow.updateStates( currentGameSettingsValues['itemToggleSetting'].get(), fromDOL, False )


def getVanillaHex( offset, byteCount=4, revision='', suppressWarnings=True ):

	""" Gets the original game code at a specified offset, based on the given game region and version (revision).
		The game code comes from the DOLs available in the "Original DOLs" folder. """

	if not revision:
		revision = dol.revision

	vanillaDol = loadVanillaDol( revision=revision, suppressWarnings=suppressWarnings )

	if vanillaDol and vanillaDol.data:
		vanillaCode = vanillaDol.data[offset*2:(offset+byteCount)*2] # Doubling offsets to count by nibbles (since it's a hex string)
	
	else: vanillaCode = ''

	return vanillaCode


def loadVanillaDol( revision='', suppressWarnings=False ):

	""" This will load and return the specified vanilla or "Original" DOL into memory (from those available in the "Original DOLs" folder), 
		used for various text/data section checks and/or vanilla code look-ups. May be called multiple times, but will only load the 
		initial DOL once. The revision of the DOL currently loaded for editing is the default revision to load if one is not specified. """

	if not revision:
		revision = dol.revision

	if 'ALL' in revision and len( originalDols ) > 0: # DOL loading not required, as the code request should be the same for any revision (so we can use any already loaded).
		return next( originalDols.itervalues() ) # Just get any, doesn't matter which

	elif revision in originalDols: # originalDols is a global dictionary, containing DOL data for vanilla code lookups
		return originalDols[revision]

	else:
		if 'ALL' in revision:
			# Grab any valid DOL found, or actually look for ALL.dol if none were found (latter case not really expected)
			validDols = listValidOriginalDols()
			if validDols: filename = listValidOriginalDols()[0] + '.dol'
			else: filename = revision + '.dol'
			dolPath = dolsFolder + '\\' + filename

		else:
			filename = revision + '.dol'
			dolPath = dolsFolder + '\\' + filename
		
		if not os.path.exists( dolPath ):
			if not suppressWarnings: 
				msg( 'An original DOL for the DOL revision of ' + revision + ' was not found in the original DOLs folder. '
					 'In order for the program to restore regions and look up vanilla code or properties, you must place an original copy of the '
					 'DOL here:\n\n' + dolsFolder + '\n\nThe filename should be "[region] [version].dol", for example, "NTSC 1.02.dol"', 'Unable to find original DOL' )
			return None

		originalDols[revision] = dolInitializer()
		originalDols[revision].load( dolPath )

		return originalDols[revision]


def listValidOriginalDols():
	
	""" Returns a list of what original DOLs are available in the "Original DOLs" folder. """
	
	dolVariations = []

	for file in os.listdir( dolsFolder ):
		filenameWithExt = os.path.basename( file )
		filename, ext = os.path.splitext( filenameWithExt )

		if ext.lower() == '.dol':
			regionInfo = filename.split() # splits on whitespace by default

			if len( regionInfo ) > 1:
				region, version = regionInfo[0].upper(), regionInfo[1]

				# Validate the name to make sure it's something the program is familiar with.
				if region == 'NTSC' or region == 'PAL' and version.startswith( '1.' ):
					dolVariations.append( region + ' ' + version )

	return dolVariations


def problemWithDol():

	""" Makes sure there is a DOL (or disc) file loaded, and that the path to it
		is still valid. Returns True if a problem is encountered. """

	if not dol.path or not dol.data:
		msg( 'No ISO or DOL file has been loaded.' )
		return True

	elif not os.path.exists( dol.path ):
		msg( 'Unable to locate the '+ dol.type.upper() + '! Be sure that it has not been moved or deleted.' )
		return True

	else: return False


def regionsOverlap( regionList ):

	""" Checks selected custom code regions to make sure they do not overlap one another. """

	overlapDetected = False

	# Compare each region to every other region.
	for i, regionEndPoints in enumerate( regionList, start=1 ):
		regionStart, regionEnd = regionEndPoints

		# Loop over the remaining items in the list (starting from second entry on first iteration, third entry from second iteration, etc),
		# so as not to compare to itself, or make any repeated comparisons.
		for nextRegionStart, nextRegionEnd in regionList[i:]:
			# Check if these two regions overlap by any amount
			if nextRegionStart < regionEnd and regionStart < nextRegionEnd: # The regions overlap by some amount.
				overlapDetected = True

				# Determine the names of the overlapping regions, and report this to the user
				msg( 'Warning! One or more regions enabled for use overlap each other. The first overlapping areas detected are (' + hex(regionStart) + ', ' + hex(regionEnd) + ') and '
					 '(' + hex(nextRegionStart) + ', ' + hex(nextRegionEnd) + '). (There may be more; resolve this case and try again to find others.) '
					 '\n\nThese regions cannot be used in tandem. In the Code-Space Options window, please choose other regions, or deselect one of '
					 'the regions that uses one of the areas shown above.', 'Region Overlap Detected' )
				break

		if overlapDetected: break

	return overlapDetected

																		 #=================================#
																		# ~ ~ Mod Analysis & Processing ~ ~ #
																		 #=================================#

def modModuleClicked( event ):

	""" Handles click events on mod modules, and toggles their install state 
		(i.e. whether or not it should be installed when the user hits save). """

	# Get the widget of the main frame for the module (i.e. the modModule frame, "self")
	modState = None
	mod = event.widget
	failsafe = 0
	while not modState:
		mod = mod.master # Move upward through the GUI heirarchy until the mod module is found
		modState = getattr( mod, 'state', None )
		assert failsafe < 3, 'Unable to process click event on modModule; no mod module found.'
		failsafe += 1

	# Toggle the state of the module
	if modState and modState != 'unavailable':

		# Offer a warning if the user is trying to disable the crash printout code
		if settingsFile.alwaysEnableCrashReports and mod.name == "Enable OSReport Print on Crash" and (modState == 'pendingEnable' or modState == 'enabled'):
			if not tkMessageBox.askyesno( 'Confirm Disabling Crash Printout', 'This mod is very useful for debugging crashes '
										  'and is therefore enabled by default. You can easily disable this behavior by opening the '
										  '"settings.py" file in a text editor and setting the option "alwaysEnableCrashReports" '
										  'to False, or by removing the "Enable OSReport Print on Crash" code from your library '
										  "(or comment it out so it's not picked up by MCM).\n\nAre you sure you'd like to disable this mod?" ):
				return # Return if the user hit "No" (they don't want to disable the mod)

		if modState == 'pendingEnable': state = 'disabled'
		elif modState == 'pendingDisable':
			if mod.type == 'gecko' and not overwriteOptions[ 'EnableGeckoCodes' ].get():
				msg( 'This mod includes a Gecko code, which are disabled.' )
				return # Exits now; don't change the state or check for changes
			else: state = 'enabled'
		elif modState == 'enabled': state = 'pendingDisable'
		elif modState == 'disabled': state = 'pendingEnable'
		else: state = 'disabled' # Failsafe reset.
		
		playSound( 'menuChange' )

		mod.setState( state )
		checkForPendingChanges()


def selectAllMods( event ):

	""" Called by the 'Select All' button on the GUI. Only applies to the current tab. """

	currentTab = getCurrentModsLibraryTab()
	
	if currentTab != 'emptyNotebook':
		frameForBorder = currentTab.winfo_children()[0]
		scrollingFrame = frameForBorder.winfo_children()[0]
		geckoCodesEnabled = overwriteOptions[ 'EnableGeckoCodes' ].get()

		for mod in scrollingFrame.interior.winfo_children():
			if mod.state == 'pendingDisable':
				if geckoCodesEnabled or mod.type != 'gecko': # Skips Gecko codes if they're disabled.
					mod.setState( 'enabled' )
			elif mod.state == 'disabled': mod.setState( 'pendingEnable' )

		playSound( 'menuChange' )
		checkForPendingChanges()


def deselectAllMods( event ):

	""" Called by the 'Deselect All' button on the GUI. Only applies to the current tab. """

	currentTab = getCurrentModsLibraryTab()
	
	if currentTab != 'emptyNotebook':
		frameForBorder = currentTab.winfo_children()[0]
		scrollingFrame = frameForBorder.winfo_children()[0]

		for mod in scrollingFrame.interior.winfo_children():
			if mod.state == 'pendingEnable': mod.setState( 'disabled' )
			elif mod.state == 'enabled': mod.setState( 'pendingDisable' )

		playSound( 'menuChange' )
		checkForPendingChanges()


def selectWholeLibrary( event ):

	""" Recursively scans all Mods Library tabs (notebook widgets), and selects all
		mods that are not currently 'unavailable'. """

	geckoCodesEnabled = overwriteOptions[ 'EnableGeckoCodes' ].get()

	for mod in genGlobals['allMods']:
		if mod.state == 'pendingDisable':
			if geckoCodesEnabled or mod.type != 'gecko': # Skips Gecko codes if they're disabled.
				mod.setState( 'enabled' )
		if mod.state == 'disabled': mod.setState( 'pendingEnable' )

	playSound( 'menuChange' )
	checkForPendingChanges()


def deselectWholeLibrary( event ):

	""" Recursively scans all Mods Library tabs (notebook widgets), and deselects all
		mods that are not currently 'unavailable'. """

	for mod in genGlobals['allMods']:
		if mod.state == 'pendingEnable': mod.setState( 'disabled' )
		elif mod.state == 'enabled': mod.setState( 'pendingDisable' )

	playSound( 'menuChange' )
	checkForPendingChanges()


def offsetInEnabledRegions( dolOffset ):
	
	""" Checks if a DOL offset falls within an area reserved for custom code. 
		Returns tuple( bool:inEnabledRegion, string:regionNameFoundIn ) """
		
	inEnabledRegion = False
	regionNameFoundIn = ''

	for regionName, regions in dol.customCodeRegions.items():
		# Scan the regions for the offset
		for regionStart, regionEnd in regions:
			if dolOffset < regionEnd and dolOffset >= regionStart: # Target region found

				if not inEnabledRegion:
					inEnabledRegion = overwriteOptions[regionName].get()
					regionNameFoundIn = regionName
				# In a perfect world, we could break from the loop here, but it may still 
				# be in another region that is enabled (i.e. there's some region overlap).

	return ( inEnabledRegion, regionNameFoundIn )


def getModCodeChanges( mod, forAllRevisions=False ):

	""" Gets all code changes required for a mod to be installed. """

	codeChanges = []

	if forAllRevisions:
		for changes in mod.data.values():
			codeChanges.extend( changes )
	else:
		# Get code changes that are applicable to all revisions, as well as those applicable to just the currently loaded revision
		codeChanges.extend( mod.data.get('ALL', []) )
		codeChanges.extend( mod.data.get(dol.revision, []) )

	return codeChanges


def codeIsAssembly( codeLines ):

	""" For purposes of final code processing (resolving custom syntaxes), special syntaxes
		will be resolved to assembly, so they will also count as assembly here. """

	isAssembly = False
	onlySpecialSyntaxes = True

	for wholeLine in codeLines:
		# Strip off and ignore comments
		line = wholeLine.split( '#' )[0].strip()
		if line == '': continue

		elif isSpecialBranchSyntax( line ) or containsPointerSymbol( line ):
			continue # These will later be resolved to assembly
		
		onlySpecialSyntaxes = False

		if not validHex( ''.join(line.split()) ): # Whitespace is excluded from the check
			isAssembly = True

	if onlySpecialSyntaxes:
		isAssembly = True

	return isAssembly


def getCustomCodeLength( customCode, preProcess=False, includePaths=None ):

	""" Returns a byte count for custom code, though it is first calculated here in terms of nibbles. Custom syntaxes may be included.
		Processing is easiest with hex strings (without whitespace), though input can be ASM if preProcess=True.

		Example inputs:
			'3C60801A60634340'
				or
			'3C60801A60634340|S|sbs__b <someFunction>|S|3C60801A48006044' <- includes some special branch syntax. """

	if preProcess: # The input is assembly and needs to be assembled into hexadecimal, or it has whitespace that needs removal
		customCode = customCodeProcessor.preAssembleRawCode( customCode, includePaths )[1]

	if '|S|' in customCode: # Indicates a special syntax is present
		length = 0
		for section in customCode.split( '|S|' ):
			if section.startswith( 'sbs__' ) or section.startswith( 'sym__' ): length += 8 # expected to be 4 bytes once assembled
			else: length += len( section )
	else:
		length = len( customCode )

	return length / 2


def collectAllStandaloneFunctions( forAllRevisions=False ): # depricate forAllRevisions arg?

	""" Gets all standalone functions in the mods library (across all codes).

		This is dependent on the Mods Library as well as the currently loaded DOL's revision.
		Storage is in the form of a dictionary, as key=functionName, value=(offset, customCode, preProcessedCustomCode) """

	functionsDict = {}

	for mod in genGlobals['allMods']:
		if mod.type == 'standalone': # Has at least one SF; skip mods that aren't of this type
			for codeChange in getModCodeChanges( mod, forAllRevisions ):
				if codeChange[0] == 'standalone': # codeChange = ( changeType, customCodeLength, offset, originalCode, customCode, preProcessedCustomCode )
					functionName = codeChange[2]

					if not functionName in functionsDict:
						functionsDict[ functionName ] = ( -1, codeChange[4], codeChange[5] )

					# If the function is already in the dictionary, make sure any copies found are identical (because the first copy found will be used for all mods calling it)
					elif functionsDict[ functionName ][2] != codeChange[5]:
						msg( 'Warning! Differing versions of the standalone function, "' + functionName + '", have been detected! '
							 'Only the first variation found will be used. '
							 '\n\nIf these are meant to be different functions, they must have different names. If they are meant to be the same function, '
							 'they must have the same code. (Note that as few as only one of the enabled mods requiring this funtion needs to define it.) ' )

	genGlobals['allStandaloneFunctions'] = functionsDict


def parseCodeForStandalones( preProcessedCode, requiredFunctions, missingFunctions ):

	""" Recursive helper function for getRequiredStandaloneFunctionNames(). Checks 
		one particular code change (injection/overwrite) for standalone functions. """

	if '|S|' in preProcessedCode:
		for section in preProcessedCode.split( '|S|' ):

			if section.startswith( 'sbs__' ) and '<' in section and '>' in section: # Special Branch Syntax; one name expected
				newFunctionNames = ( section.split( '<' )[1].split( '>' )[0], ) # Second split prevents capturing comments following on the same line.

			elif section.startswith( 'sym__' ): # Assume could have multiple names
				newFunctionNames = []
				for fragment in section.split( '<<' ):
					if '>>' in fragment: # A symbol (function name) is in this string segment.
						newFunctionNames.append( fragment.split( '>>' )[0] )
			else: continue

			for functionName in newFunctionNames:
				if functionName in requiredFunctions: continue # This function has already been analyzed

				requiredFunctions.append( functionName )

				# Recursively check for more functions that this function may reference
				if functionName in genGlobals['allStandaloneFunctions']:
					parseCodeForStandalones( genGlobals['allStandaloneFunctions'][functionName][2], requiredFunctions, missingFunctions )
				elif functionName not in missingFunctions:
					missingFunctions.append( functionName )

	return requiredFunctions, missingFunctions


def getRequiredStandaloneFunctionNames( mod ):
	
	""" Gets the names of all standalone functions a particular mod requires. 
		Returns a list of these function names, as well as a list of any missing functions. """

	functionNames = []
	missingFunctions = []

	# This loop will be over a list of tuples (code changes) for a specific game version.
	for codeChange in getModCodeChanges( mod ):
		if codeChange[0] != 'gecko': #todo allow gecko codes to have SFs
			parseCodeForStandalones( codeChange[5], functionNames, missingFunctions ) # codeChange[5] is preProcessedCustomCode

	return functionNames, missingFunctions # functionNames will also include those that are missing


def checkGeckoInfrastructure():

	""" While gecko.environmentSupported reveals whether MCM is properly configured to process/install Gecko codes (within the
		settings file), this function checks whether a DOL has Gecko code parts installed within it, by checking for the Gecko
		codehandler hook and the codelist. """

	installed = False
	codelistArea = ''

	if gecko.environmentSupported:
		# Get the hex at the codehandler hook location currently in the DOL
		hexAtHookOffset = dol.data[gecko.hookOffset*2:gecko.hookOffset*2+8]

		# Get the vanilla/default hex at that same location for this DOL
		vanillaHexAtHookOffset = getVanillaHex( gecko.hookOffset )

		if not vanillaHexAtHookOffset: # Unable to retrieve the hex
			msg( 'Unable to confirm the installation of Gecko codes. To do so, you must place an original copy of the DOL here:\n'
				 '(Filename should be "[region] [version].dol", for example, "NTSC 1.02.dol")\n\n' + dolsFolder, 'Unable to find an original copy of the DOL' )

		elif hexAtHookOffset != vanillaHexAtHookOffset: # If these are different, the gecko codehandler hook must be installed.
			codelistRegionData = dol.data[gecko.codelistRegionStart*2:gecko.codelistRegionEnd*2].lower()

			# Check for the codelist wrapper
			if '00d0c0de00d0c0de' in codelistRegionData and 'f000000000000000' in codelistRegionData:
				codelistArea = codelistRegionData.split('00d0c0de00d0c0de')[1].split('f000000000000000')[0]
				installed = True
				addToInstallationSummary( geckoInfrastructure=True )

	return ( installed, codelistArea )
	

def customCodeInDOL( startingOffset, customCode, freeSpaceCodeArea, excludeLastCommand=False, startOffsetUnknown=False ):

	""" Essentially tries to mismatch any of a code change's custom code with the custom code in the DOL. Besides simply
		checking injection site code, this can check custom injection code, even if it includes unknown special branch syntaxes.

		This is much more reliable than simply checking whether the hex at an injection site is vanilla or not because it's 
		possible that more than one mod could target the same location (so we have to see which mod the installed custom code 
		belongs to). If custom code is mostly or entirely composed of custom syntaxes, we'll give it the benefit of the doubt 
		and assume it's installed (since at this point there is no way to know what bytes a custom syntax may resolve into). """

	matchOffset = startingOffset
	offset = startingOffset
	if excludeLastCommand: customCode = customCode[:-8] # Excludes the branch back on injection mods.

	# Map each code section to the code in the DOL to see if they match up.
	for section in customCode.lower().split( '|s|' ): # Need to use lowercase s instead of |S| here
		if section == '': continue

		# Ignore custom syntaxes
		elif section.startswith( 'sbs__' ) or section.startswith( 'sym__' ):
			offset += 4
			continue
	
		sectionLength = len( section ) / 2

		if startOffsetUnknown: # Occurs with Gecko codes & standalone functions, since we have no branch to locate them.
			# This is the first normal (non-special-branch) section for this code. Since the offset is unknown,
			# use this section to find all possible locations/matches for this code within the region.
			matches = findAll( freeSpaceCodeArea.lower(), section, charIncrement=2 ) # charIncrement set to 2 so we increment by byte rather than by nibble
			matchOffset = -1

			# Iterate over the possible locations/matches, and check if each may be the code we're looking for (note that starting offsets will be known in these checks)
			for matchingOffset in matches:
				subMatchOffset = customCodeInDOL( (matchingOffset/2) - offset, customCode, freeSpaceCodeArea ) # "- offset" accomodates for potential preceding special branches

				if subMatchOffset != -1: # The full code was found
					matchOffset = subMatchOffset
					break
			break

		else:
			codeInDol = freeSpaceCodeArea[offset*2:(offset+sectionLength)*2].lower()

			if section != codeInDol:
				matchOffset = -1
				break # Mismatch detected, meaning this is not the same (custom) code in the DOL.
			else:
				offset += sectionLength

	return matchOffset


def checkForEnabledCodes( userPromptedForGeckoUsage=False ):

	""" Checks the currently loaded DOL file for which mods are installed, and sets their states accordingly.
		'userPromptedForGeckoUsage' will only come into play if there are Gecko codes detected as installed. """

	loadRegionOverwriteOptions()
	clearSummaryTab() # Clears the summary tab's lists of installed mods/SFs.
	allEnabledCodeRegions = getCustomCodeRegions()

	# Preliminary checks for Gecko codes
	geckoInfrastructureInstalled, codelistArea = checkGeckoInfrastructure()

	standaloneFunctionsInstalled = Set()
	functionOnlyModules = [] # Remember some info on modules composed of only standalone functions
	geckoCodesAllowed = overwriteOptions[ 'EnableGeckoCodes' ].get()
	requiredDisabledRegions = []

	# Primary Mod-Detection pass. Set the state (highlighting & notes) of each module based on whether its codes are found in the DOL.
	for mod in genGlobals['allMods']:
		# Cancel this scan if a new scan of the Mods Library is queued
		if modsLibraryNotebook.stopToRescan: 
			break

		# Skip unavailable non-gecko mods (gecko mods are a special case, to be re-evaluated)
		elif mod.state == 'unavailable' and mod.type != 'gecko':
			continue

		# Disable mods that are not applicable to the currently loaded DOL
		elif dol.revision not in mod.data:
			mod.setState( 'unavailable' )
			continue

		# Determine if the mod is in the DOL, and set the state of the module respectively.
		included = True
		functionsOnly = True
		functionsIncluded = []
		summaryReport = [] # Used to track and report installation locations/offsets to the Summary tab

		for changeType, customCodeLength, offsetString, originalCode, _, preProcessedCustomCode in getModCodeChanges( mod ):
			if functionsOnly and not changeType == 'standalone': functionsOnly = False

			# Convert the offset to a DOL Offset integer (even if it was a RAM Address)
			if changeType != 'standalone' and changeType != 'gecko':
				offset = normalizeDolOffset( offsetString )

				# Validate the offset
				if offset == -1:
					msg( 'A problem was detected with the mod "' + mod.name + '"; an offset for one of its code changes (' + offsetString + ') could '
							"not be parsed or processed. If you're sure it's written correctly, it appears to fall out of range of this game's DOL." )
					included = False
					break

				# Validate the original game code, removing whitespace if necessary
				elif not validHex( originalCode ):
					# Get rid of whitepace and try it again
					originalCode = ''.join( originalCode.split() )

					if not validHex( originalCode ):
						msg( 'A problem was detected with the mod "' + mod.name + '"; it appears that one of its static overwrites '
							'or injection points contains invalid hex (or could not be assembled). It will be assumed that this mod is disabled.' )
						included = False
						break # Even though there is "if not included: break" at the end of this loop, this is still needed here to prevent checking the next if block

			if changeType == 'static':
				# Check whether the vanilla hex for this code change matches what's in the DOL
				matchOffset = customCodeInDOL( offset, preProcessedCustomCode, dol.data )
				if matchOffset == -1: included = False
				else:
					# Check whether this overwrite would land in an area reserved for custom code. If so, assume it should be disabled.
					for codeRegion in allEnabledCodeRegions:
						if offset >= codeRegion[0] and offset < codeRegion[1]: 
							included = False
							break
					else: # loop above didn't break; all checks out
						summaryReport.append( ('Code overwrite', changeType, offset, customCodeLength) ) # changeName, changeType, dolOffset, customCodeLength

			elif changeType == 'injection':
				# Test the injection point against the original, vanilla game code.
				injectionPointCode = dol.data[offset*2:offset*2+8]
				commandByte = injectionPointCode[:2].lower()

				if injectionPointCode.lower() == originalCode.lower():
					included = False

				elif not ( commandByte == '48' or commandByte == '49' or commandByte == '4a' or commandByte == '4b' ): 
					included = False # Not a branch added by MCM! Something else must have changed this location.

				else: # There appears to be a branch at the injection site (and isn't original hex). Check to see if it leads to the expected custom code.
					customCodeOffset = getBranchTargetDolOffset( offset, injectionPointCode )

					inEnabledRegion, regionNameFoundIn = offsetInEnabledRegions( customCodeOffset )

					if inEnabledRegion:
						matchOffset = customCodeInDOL( customCodeOffset, preProcessedCustomCode, dol.data, excludeLastCommand=True ) #todo narrow search field to improve performance

						# If there was a good match on the custom code, remember where this code change is for a summary on this mod's installation
						if matchOffset == -1: included = False
						else:
							summaryReport.append( ('Branch', 'static', offset, 4) ) # changeName, changeType, dolOffset, customCodeLength
							summaryReport.append( ('Injection code', changeType, customCodeOffset, customCodeLength) )

					else:
						included = False
						print '\nPossible phantom mod;', mod.name, 'may have custom code installed to a disabled region: "' + regionNameFoundIn + '"'
						print 'it was led to by an injection point hex of', injectionPointCode, 'at', hex(offset), 'which points to DOL offset', hex(customCodeOffset)

						if regionNameFoundIn != '':
							if regionNameFoundIn not in requiredDisabledRegions:
								requiredDisabledRegions.append( regionNameFoundIn )
						else:
							print 'Custom code at', hex(offset), 'seems to be pointing to a region not defined for custom code!'

			elif changeType == 'gecko':
				if not gecko.environmentSupported: # These aren't available for this DOL
					included = False
				elif not geckoInfrastructureInstalled: # Not installed
					included = False

				else: # Check if the code is installed (present in the codelist area)
					matchOffset = customCodeInDOL( 0, preProcessedCustomCode, codelistArea, startOffsetUnknown=True )

					if matchOffset == -1: # Code not found in the DOL
						included = False

					else: # Code found to be installed!
						# If using the Gecko regions is not enabled, ask the user if they'd like to allow Gecko codes.
						if not geckoCodesAllowed and not userPromptedForGeckoUsage: # The second boolean here ensure this message only appears once throughout all of these loops.
							userPromptedForGeckoUsage = True

							# If this is Melee, add some details to the message
							if dol.isMelee and ( gecko.codelistRegion == 'DebugModeRegion' or gecko.codehandlerRegion == 'DebugModeRegion' 
												or gecko.codelistRegion == 'Debug Mode Region' or gecko.codehandlerRegion == 'Debug Mode Region' ):
								meleeDetails = ( "Mostly, this just means that you wouldn't be able to use the vanilla Debug Menu "
													"(if you're not sure what that means, then you're probably not using the Debug Menu, and you can just click yes). " )
							else: meleeDetails = ''

							promptToUser = ( 'Gecko codes have been found to be installed, however the "Enable Gecko Codes" option is not selected.'
								'\n\nEnabling Gecko codes means that the regions defined for Gecko codes, ' + gecko.codelistRegion + ' and ' + gecko.codehandlerRegion + ', will be reserved '
								"(i.e. may be partially or fully overwritten) for custom code. " + meleeDetails + 'Regions that you have '
								'enabled for use can be viewed and modified by clicking on the "Code-Space Options" button. '
								'\n\nIf you do not enable Gecko codes, those that are already installed will be removed upon saving! Would you like to enable '
								'these regions for overwrites in order to use Gecko codes?' )

							geckoCodesAllowed = willUserAllowGecko( promptToUser, False, root )

							if geckoCodesAllowed: # This option has been toggled! Re-run this function to ensure all Gecko mod states are properly set
								print 'performing gecko codes re-scan'
								checkForEnabledCodes( True )
								return

						if geckoCodesAllowed:
							dolOffset = gecko.codelistRegionStart + 8 + matchOffset
							summaryReport.append( ('Gecko code', changeType, dolOffset, customCodeLength) )
						else:
							included = False

			elif changeType == 'standalone':
				functionsIncluded.append( offsetString )

			if not included:
				break

		# Prepare special processing for the unique case of this module being composed of ONLY standalone functions (at least for this dol revision)
		if included and functionsOnly:
			functionOnlyModules.append( (mod, functionsIncluded) )
			continue

		# Check that all standalone functions this mod requires are present.
		elif included:
			requiredStandaloneFunctions, missingFunctions = getRequiredStandaloneFunctionNames( mod )

			if missingFunctions:
				included = False
				msg( 'These standalone functions required for "' + mod.name + '" could not be found in the Mods Library:\n\n' + grammarfyList(missingFunctions) )

			else:
				# First, check whether the required SFs can be found in the enabled custom code regions
				for functionName in requiredStandaloneFunctions:
					preProcessedFunctionCode = genGlobals['allStandaloneFunctions'][ functionName ][2]

					for areaStart, areaEnd in allEnabledCodeRegions:
						matchOffset = customCodeInDOL( 0, preProcessedFunctionCode, dol.data[areaStart*2:areaEnd*2], startOffsetUnknown=True )

						if matchOffset != -1: # Function found
							summaryReport.append( ('SF: ' + functionName, 'standalone', areaStart + matchOffset, getCustomCodeLength( preProcessedFunctionCode )) )
							break

					else: # The loop scanning through the free code regions above didn't break; SF was not found.
						# Check whether the function is in a disabled region
						found = False
						for regionName, regions in dol.customCodeRegions.items():
							if regionName in overwriteOptions and not overwriteOptions[regionName].get():
								# Scan the regions for the offset
								for regionStart, regionEnd in regions:
									matchOffset = customCodeInDOL( 0, preProcessedFunctionCode, dol.data[regionStart*2:regionEnd*2], startOffsetUnknown=True )

									if matchOffset != -1: # Function found (in a disabled region!)
										print 'SF for', mod.name + ', "' + functionName + '", found in a disabled region.'
										if not regionName in requiredDisabledRegions: requiredDisabledRegions.append( regionName )
										found = True
										break
							if found: break

						# Even if found in a disabled region, consider not installed for now. User will be prompted for a rescan if custom code is in disabled regions
						included = False
						break

		if included:
			mod.setState( 'enabled' )
			standaloneFunctionsInstalled.update( requiredStandaloneFunctions ) # This is a set, so only new names are added.
			addToInstallationSummary( mod.name, mod.type, summaryReport )

		elif changeType == 'gecko' and not geckoCodesAllowed:
			mod.setState( 'unavailable' )

		elif settingsFile.alwaysEnableCrashReports and mod.name == "Enable OSReport Print on Crash":
			# Queue this to be installed
			if mod.state != 'pendingEnable':
				mod.setState( 'pendingEnable' )
		else:
			mod.setState( 'disabled' )

	# Finished checking for mods (end of allMods loop).

	# Ask to enable regions that appear to have custom code
	if requiredDisabledRegions:
		if len( requiredDisabledRegions ) == 1:
			enableDisabledRegionsMessage = ( "It looks like mods may be installed to the " + requiredDisabledRegions[0] 
												+ ", which is currently disabled.\n\nWould you like to enable it?" )
		else:
			enableDisabledRegionsMessage = ( "It looks like mods may be installed to the following custom code regions, which "
								'are currently disabled:\n\n' + ', '.join(requiredDisabledRegions) + '\n\nWould you like to enable them?' )

		# Prompt with the above message and wait for an answer
		enableSuspectRegions = tkMessageBox.askyesno( 'Enable Custom Code Regions?', enableDisabledRegionsMessage )

		if enableSuspectRegions:
			# Enable the required regions and re-scan
			for regionName in requiredDisabledRegions:
				overwriteOptions[regionName].set( True )

			# Save these region options to file (since this file is read before scanning for codes), and then re-scan
			saveOptions()

			# Re-scan the Mods Library if that's what this function call was a result of, or if not, just re-check for mods
			if modsLibraryNotebook.isScanning:
				modsLibraryNotebook.stopToRescan = True
			else:
				checkForEnabledCodes()

	# Check modules that ONLY have standalone functions. Check if they have any functions that are installed
	for mod, functionsThisModIncludes in functionOnlyModules:
		for functionName in functionsThisModIncludes:
			if functionName in standaloneFunctionsInstalled: # This module contains a used function!
				mod.setState( 'enabled' ) # Already automatically added to the Standalone Functions table in the Summary Tab
				break # only takes one to make it count
		else: # loop didn't break; no functions for this mod used
			mod.setState( 'disabled' )

	# Make sure a new scan isn't queued before finalizing
	if not modsLibraryNotebook.stopToRescan:
		updateSummaryTabTotals()

		# If this is SSBM, enable the Default Game Settings tab and update it with what is currently set in this DOL
		if dol.isMelee:
			if not dol.revision in settingsTableOffset: 
				msg( '"' + dol.revision + '" is an unrecognized SSBM revision.' )
				return

			else:
				mainNotebook.tab( 2, state='normal' ) # The Default Game Settings tab
				updateDefaultGameSettingsTab( 'fromDOL' )

		else: # Default Game Settings can't be set
			mainNotebook.tab( 2, state='disabled' ) # The Default Game Settings tab
			mainNotebook.select( 0 )

		checkForPendingChanges()


def checkForPendingChanges( changesArePending=False, playAudio=False ):

	""" Checks for total code space usage (and updates that information on the GUI), 
		and makes sure that mods do not attempt to write into space (i.e. via static 
		overwrite or injection site branch) reserved for custom code. Also checks to 
		make sure that any standalone functions a mod requires can be found. """

	if dol.data:
		spaceUsed = 0 # In bytes
		geckoSpaceUsed = 0 # Starts at 16 to account for the required 16 byte codelist wrapper
		requiredStandaloneFunctions = set([]) # Unordered, unique entries only
		toolTipColor = colorBank['freeSpaceIndicatorGood']
		geckoToolTipColor = colorBank['freeSpaceIndicatorGood']
		customCodeRegions = getCustomCodeRegions()

		# Scan through the mods to check for pending changes and get the total required space, not counting standalone functions.
		for mod in genGlobals['allMods']:

			if mod.state == 'pendingEnable' or mod.state == 'pendingDisable': changesArePending = True

			# Total how much space will be required, and remember the standalone functions needed.
			if mod.state == 'pendingEnable' or mod.state == 'enabled':
				spaceUsedByThisMod = 0
				geckoSpaceUsedByThisMod = 0

				for codeChange in getModCodeChanges( mod ):
					changeType, customCodeLength, offset, _, _, _ = codeChange

					if changeType == 'gecko': # Shouldn't be possible to have these enabled or pendingEnable if the environment doesn't support them.
						geckoSpaceUsedByThisMod += customCodeLength

					elif changeType == 'static' or changeType == 'injection':
						offsetInt = normalizeDolOffset( offset )

						# Make sure this code change isn't attempting to write to an area reserved for custom code (injection code/gecko stuff)
						for rangeStart, rangeEnd in customCodeRegions:
							if offsetInt >= rangeStart and offsetInt < rangeEnd:
								if changeType == 'static': typeOfChange = 'a static overwrite'
								else: typeOfChange = 'an injection point'

								cmsg( '\nThe mod "' + mod.name + '" includes ' + typeOfChange + ' that is made to write into '
									  "a region that is currently reserved for custom code.\n\nThe offending change's offset "
									  'is ' + hex(offsetInt) + ', \nwhich falls into the reserved range of ' + hex(rangeStart) + ', ' + hex(rangeEnd) + '.'
									  "\n\nIf you want to use this mod, you'll need to open the 'Code-Space Options' menu, disable use of this region, "
									  "and restore it to the game's vanilla code (via the 'Restore' button found there).", 'Overwrite Conflict Detected!' )

								mod.setState( 'disabled' )
								break
						else: # Loop above didn't break; no conflicts
							if changeType == 'injection':
								spaceUsedByThisMod += customCodeLength

					if mod.state == 'disabled': break # A conflict was detected

				# If this mod's state has changed, an overwrite conflict was detected. So skip it.
				if mod.state == 'disabled': continue
				else:
					spaceUsed += spaceUsedByThisMod
					geckoSpaceUsed += geckoSpaceUsedByThisMod

					standaloneFunctionsRequired, missingFunctions = getRequiredStandaloneFunctionNames( mod )

					if missingFunctions:
						msg( 'These standalone functions required for "' + mod.name + '" could not be found in the Mods Library:\n\n' + grammarfyList(missingFunctions) )
					else:
						requiredStandaloneFunctions.update( standaloneFunctionsRequired )

		# If there are any standalone functions used, calculate the total space required by them.
		if requiredStandaloneFunctions != set([]):
			for mod in genGlobals['allMods']:
				if mod.state != 'unavailable':
					for codeChange in getModCodeChanges( mod ):
						if codeChange[0] == 'standalone' and codeChange[2] in requiredStandaloneFunctions:
							spaceUsed += codeChange[1]
							requiredStandaloneFunctions.difference_update( [codeChange[2]] ) # Removes this function name from the set.
				if requiredStandaloneFunctions == set([]): break # Stop searching if all functions have been assessed.

			else: # This loop wasn't broken, meaning there are standalone functions that weren't found.
				msg( 'These standalone functions appear to be missing from the library:\n\n' + '\n'.join(requiredStandaloneFunctions) )

		# If gecko codes will be used, make sure there is enough space for them, and add the codehandler and codelist wrapper to the total used space
		if geckoSpaceUsed > 0:
			spaceTakenByCodehandler = gecko.codehandlerLength
			if geckoSpaceUsed + 16 > gecko.spaceForGeckoCodelist:
				geckoToolTipColor = colorBank['freeSpaceIndicatorBad']
				msg( 'Warning! There is not enough space for all of the Gecko codes selected. These are currently assigned to go '
					 "into the " + gecko.codelistRegion + ", which provides " + hex( gecko.spaceForGeckoCodelist ) + " bytes of "
					 "free space. The codes you've selected (plus the list wrapper of 16 bytes) amounts to " + hex( geckoSpaceUsed + 16 ) + ' bytes.' )
		else:
			geckoSpaceUsed = 0
			spaceTakenByCodehandler = 0

		# Get the total space available and enabled in the DOL for custom code
		maxNonGeckoCustomCodeSpace = 0
		for codeArea in getCustomCodeRegions( codelistStartPosShift=geckoSpaceUsed, codehandlerStartPosShift=spaceTakenByCodehandler ):
			maxNonGeckoCustomCodeSpace += codeArea[1] - codeArea[0]

		# Update the standard free space indicator to reflect the current available DOL space.
		freeSpaceIndicator['maximum'] = maxNonGeckoCustomCodeSpace
		freeSpaceUsage.set( spaceUsed )

		# Ensure there is enough space for the [non-Gecko] custom code for the selected mods
		if spaceUsed > maxNonGeckoCustomCodeSpace:
			toolTipColor = colorBank['freeSpaceIndicatorBad']
			msg( 'Warning! There is not enough space for all of the codes selected. The DOL regions currently enabled for custom code '
				 'amount to ' + hex(maxNonGeckoCustomCodeSpace) + ' bytes. The codes currently selected require at least ' + hex(spaceUsed) + ' bytes. '
				 'Not all of these will be able to be saved to your game.' )

		# Calculate % used
		if maxNonGeckoCustomCodeSpace == 0: percentSpaceUsed = ''
		else: percentSpaceUsed = ' (' + str( round( (float(spaceUsed) / maxNonGeckoCustomCodeSpace) * 100, 2 ) ) + '%)' # last number equates to number of decimal places to show

		# Add hover messages to the storage fill bars, to show exactly how much space is used
		freeSpaceIndicator.toolTip.configure( text='  :: Standard Codes Free Space -\n'
											'Total Available: \t' + uHex(maxNonGeckoCustomCodeSpace) + ' bytes\n'
											'Total Used: \t' + uHex(spaceUsed) + ' bytes' + percentSpaceUsed + '\n'
											'Remaining: \t' + uHex(maxNonGeckoCustomCodeSpace - spaceUsed) + ' bytes', bg=toolTipColor, justify='left' )

		# Update the Gecko free space indicator
		if 'EnableGeckoCodes' in overwriteOptions and overwriteOptions[ 'EnableGeckoCodes' ].get():
			freeGeckoSpaceUsage.set( geckoSpaceUsed ) # Excludes space required by the codelist wrapper (16 bytes).

			if not geckoSpaceUsed > 0:
				freeGeckoSpaceIndicator.toolTip.configure( text='No Gecko codes\nare installed', bg='#cccccc', justify='center' )
			else:
				# Calculate % used
				percentGeckoSpaceUsed = str( round(( float(geckoSpaceUsed) / (gecko.spaceForGeckoCodelist - 16) ) * 100, 2) )

				# Add hover messages to the storage fill bars, to show exactly how much space is used
				freeGeckoSpaceIndicator.toolTip.configure( text='  :: Gecko Codes Free Space -\n'
													'Total Available: \t' + uHex(gecko.spaceForGeckoCodelist - 16) + ' bytes\n'
													'Total Used: \t' + uHex(geckoSpaceUsed) + ' bytes (' + percentGeckoSpaceUsed + '%)\n'
													'Remaining: \t' + uHex(gecko.spaceForGeckoCodelist - 16 - geckoSpaceUsed) + ' bytes', bg=geckoToolTipColor, justify='left' )
		else: # No Gecko codes; disable the meter.
			freeGeckoSpaceUsage.set( 0 )
			freeGeckoSpaceIndicator.toolTip.configure( text='Gecko codes\nare disabled', bg='#cccccc', justify='center' )

		# If this is SSBM, check if there are any unsaved changes on the Default Game Settings tab
		if dol.isMelee and dol.revision in settingsTableOffset:
			for widgetSettingID in gameSettingsTable:
				newValue = currentGameSettingsValues[widgetSettingID].get()
				existingValue = getGameSettingValue( widgetSettingID, 'fromDOL' )

				if newValue != existingValue:
					changesArePending = True
					break

		# Enable/disable the buttons for saving changes
		if changesArePending: 
			saveChangesBtn.config( state='normal' )
			saveChangesBtn2.config( state='normal' )

		else: # No changes to save; disable the save buttons
			saveChangesBtn.config( state='disabled' )
			saveChangesBtn2.config( state='disabled' )

	if playAudio: playSound( 'menuChange' )

	updateInstalledModsTabLabel()


def willUserAllowGecko( promptToUser, toggleModStates, parent ):

	""" Prompts the user to see if they'd like to enable Gecko codes. The usage-status in 
		overwriteOptions (the dictionary describing whether or not custom code regions 
		should be used) is also updated, as well as the options window GUI if it is open. 
		
		If toggleModStates is True, mod states will be reevaluated based on the new gecko setting. """

	# Check whether gecko codes are allowed, either by checking the option or by prompting the user
	if promptToUser:
		geckoRegionsEnabled = tkMessageBox.askyesno( '', promptToUser, parent=parent )
		overwriteOptions[ 'EnableGeckoCodes' ].set( geckoRegionsEnabled )

	else: # The promptToUser string is empty; no message, so default to what the option is already set as
		geckoRegionsEnabled = overwriteOptions[ 'EnableGeckoCodes' ].get()

	# Set the global region overwrite options. If the options window is open, its checkboxes will change on/off automatically
	if geckoRegionsEnabled:
		overwriteOptions[ gecko.codelistRegion ].set( True )
		overwriteOptions[ gecko.codehandlerRegion ].set( True )

	saveOptions()

	# If the Code-Space Options window is open, select or deselect the required Gecko region checkboxes
	if root.optionsWindow: # The region overwrite options window is currently open
		# The checkboxes for Gecko code regions should be disabled and selected if gecko codes are allowed
		if geckoRegionsEnabled: widgetsState = 'disabled'
		else: widgetsState = 'normal'

		# Change the overwriteOption and checkboxes states (these share BooleanVars), and restore button states
		for checkbox in root.optionsWindow.checkboxes:
			if checkbox.regionName == gecko.codelistRegion or checkbox.regionName == gecko.codehandlerRegion:
				checkbox['state'] = widgetsState
				checkbox.restoreBtn.config( state=widgetsState )

	# Update the GUI for mod states and enabled status.
	if toggleModStates:
		if geckoRegionsEnabled and dol.data: # Installed mods may already have their states altered, so mod installation needs reevaluation.
			checkForEnabledCodes()

		else: # The user declined enabling Gecko codes. Disable all Gecko mod modules.
			for mod in genGlobals['allMods']:
				if mod.type == 'gecko': mod.setState( 'unavailable' )
					
			checkForPendingChanges() # If an installed mod was disabled, re-enable the 'save' buttons so that the user can save changes.

	return geckoRegionsEnabled


def updateDefaultGameSettingWidget( widgetControlID, currentValue, checkForChanges=True ):

	""" Updates the appearance of an input/button widget used for default game settings. 
	
		Called from updateDefaultGameSettingsTab, the save function, and from the 
		'set to game setting defaults' functions. The checkForChanges variable is used 
		to moderate a few things in cases where this function is called multiple times in succession. """

	# Play a sound effect.
	if checkForChanges == True and (widgetControlID == 'stageToggleControl' or widgetControlID == 'itemToggleControl'): # or 'Rumble' in widgetControlID
		# This condition only occurs by the stage/item selection window confirm() methods.
		playSound( 'menuSelect' )
	elif checkForChanges:
		playSound( 'menuChange' )

	# Nothing more to do if there's no file loaded
	if not dol.data:
		return

	# Get the widget that this is updating
	if widgetControlID == 'itemFrequencyDisplay': 
		widget = root.itemSelectionsWindow.window.winfo_children()[0].winfo_children()[-3].winfo_children()[1] # Window object -> itemFrame -> cellFrame -> OptionMenu
	elif 'Rumble' in widgetControlID:
		if not root.rumbleSelectionWindow: return
		else: widget = root.rumbleSelectionWindow.buttons[widgetControlID]
	else: widget = globals()[widgetControlID]

	# Get the default value of the widget (within the DOL)
	default = getGameSettingValue( widgetControlID[:-7] + 'Setting', 'fromDOL' )

	# Color the widget, based on whether its values have been updated.
	if str( currentValue ).lower() == default.lower():
		if widget.winfo_class() == 'Menubutton': # The dropdown boxes
			widget['bg'] = 'SystemButtonFace'
			widget['activebackground'] = 'SystemButtonFace'
			if widgetControlID == 'itemFrequencyDisplay': itemToggleControl.configure(style='TButton')
		elif widget.winfo_class() == 'TButton':
			widget.configure(style='TButton')
		else: widget['bg'] = 'SystemWindow' # likely is a 'Spinbox'

	else: # The setting is new/different
		if widget.winfo_class() == 'Menubutton': # The dropdown boxes
			widget['bg'] = '#aaffaa'
			widget['activebackground'] = '#aaffaa'
			if widgetControlID == 'itemFrequencyDisplay': itemToggleControl.configure(style='pendingSave.TButton')
		elif widget.winfo_class() == 'TButton':
			widget.configure(style='pendingSave.TButton')
		else: widget['bg'] = '#aaffaa' # likely is a 'Spinbox'

	# Update the rumble options window button
	if 'Rumble' in widgetControlID and root.rumbleSelectionWindow:
		for button in root.rumbleSelectionWindow.buttons.values():
			if button['style'] == 'pendingSave.TButton':
				rumbleToggleControl.configure(style='pendingSave.TButton')
				break
		else: rumbleToggleControl.configure(style='TButton')

	if checkForChanges: checkForPendingChanges()

																			 #=============================#
																			# ~ ~ Saving & File Writing ~ ~ #
																			 #=============================#

def saveOptions():
	
	""" Syncs the overwriteOptions (bools for whether or not each custom code region should be used) to 
		the "settings" object, and then saves these settings to file, i.e. the options.ini file. """

	if not settings.has_section( 'Region Overwrite Settings' ):
		settings.add_section( 'Region Overwrite Settings' )

	# Update settings with the currently selected checkbox variables.
	for regionName, boolvar in overwriteOptions.items():
		settings.set( 'Region Overwrite Settings', regionName, str(boolvar.get()) )

	# Save the above, and all other options currently saved to the settings object, to theOptionsFile.
	with open( genGlobals['optionsFilePath'], 'w') as theOptionsFile: 
		settings.write( theOptionsFile )


def exportDOL():

	""" Wrapper for the Export DOL button. """

	if dol.data != '':
		createNewDolFile( dol.data, isoFilepath=dol.path )


def createNewDolFile( externalDolData, isoFilepath ):

	""" Prompts the user for a new place to save the given DOL data, and saves it to file. 
		Also updates the default search directory for folder chosing operations, 
		and the default file format to use for various operations. """

	# Prompt for a place to save the file.
	isoFilename = os.path.split( isoFilepath )[1]
	savePath = tkFileDialog.asksaveasfilename(
		title="Where would you like to save the DOL file?", 
		initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
		initialfile='Start (from ' + isoFilename[:-4] + ')',
		defaultextension='.dol',
		filetypes=[ ("DOL files", ".dol"), ("All files", "*") ]
		)

	if not savePath: # User canceled the operation
		return False

	saveDirectory, dolFilename = os.path.split( savePath )
	settings.set( 'General Settings', 'defaultSearchDirectory', saveDirectory.encode('utf-8').strip() )
	settings.set( 'General Settings', 'defaultFileFormat', 'dol' )
	saveOptions()

	# Save the dol data to a new file.
	try:
		with open( savePath, 'wb') as newDol:
			newDol.write( bytearray.fromhex(externalDolData) )

		msg('Done! \n\nA new DOL file, "' + dolFilename + '", was successfully created.') # here:\n\n' + saveDirectory)
		return True

	except Exception as e:
		msg( "There was a problem while creating the DOL file: " + str(e) )
		return False


def askToBackupDOL( isoFilepath ):
	createBackup = tkMessageBox.askquestion( 'Create back-up?', 
		"Would you like to create a backup of the codes (the DOL file) \nalready in this game?", 
		icon='warning' )

	if createBackup == 'yes':
		# Get the data for the DOL currently in the disc.
		with open( isoFilepath, 'rb') as isoBinary:
			# Get the DOL ISO file offset, length, and data.
			isoBinary.seek( 0x0420 )
			thisDolOffset = toInt( isoBinary.read(4) ) # Should be 0x1E800 for v1.02
			tocOffset = toInt( isoBinary.read(4) )
			dolLength = tocOffset - thisDolOffset # Should be 0x438600 for vanilla v1.02
			isoBinary.seek( thisDolOffset )
			thisDolData = isoBinary.read( dolLength ).encode("hex")

		# Save the data collected above
		return createNewDolFile( thisDolData, isoFilepath )

	else: return True


def importIntoISO():

	""" Wrapper for the "Import into ISO" button. Prompts the user for a disc to import the currently 
		loaded DOL file into, asks if they'd like to back-up the DOL that's currently loaded in that 
		disc, and then saves the currently loaded DOL file to that disc. """

	# Do nothing if no DOL is loaded
	if not dol.data:
		return

	# Prompt for a disc image to import the DOL into.
	filepath = tkFileDialog.askopenfilename(
		title="Choose a disc image file to open.", 
		initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
		filetypes=[ ('Disc image files', '*.iso *.gcm'), ('all files', '*.*')] )

	# Do nothing if the user canceled the above prompt
	if not filepath:
		return

	# Save default search directory setting
	settings.set( 'General Settings', 'defaultSearchDirectory', os.path.split(filepath)[0].encode('utf-8').strip() )
	saveOptions()
	normalizedPath = os.path.normpath( filepath ).replace('{', '').replace('}', '')
	
	# Validate the normalized path
	if not os.path.exists( normalizedPath ): 
		msg( 'There was a problem while attemtping to import. Possibly due to the file being deleted or moved.' )
		return

	if askToBackupDOL( normalizedPath ):
		try:
			with open( normalizedPath, 'r+b') as isoBinary:
				# Get the DOL ISO file offset and length for this disc
				isoBinary.seek( 0x0420 )
				dolOffset = toInt( isoBinary.read(4) )
				tocOffset = toInt( isoBinary.read(4) )
				dolLength = tocOffset - dolOffset

				if len( dol.data )/2 <= dolLength:
					# Save the DOL currently in memory to the target ISO.
					isoBinary.seek( dolOffset )
					isoBinary.write( bytearray.fromhex(dol.data) )
					msg("Done! \n\nThe currently loaded DOL and any changes you've saved have \nbeen added to the selected game.")
				else:
					msg('Unable to import the DOL. \n\nThe DOL file is larger than the DOL space provided \nin the ISO!', 'Critical Error')
		except:
			msg("Unable to import the DOL. \n\nBe sure that the file is not being used by another \nprogram (like Dolphin :P).")


def saveAs():

	""" Creates a new file (via dialog prompt to user), and then saves the currently 
		loaded DOL data to it, with the currently selected mods installed. """

	originalFilename = os.path.basename( dol.path )
	fileNameWithoutExt = originalFilename.rsplit( '.', 1 )[0]
	newFilenameSuggestion = fileNameWithoutExt + ' - Copy.dol'

	targetFile = tkFileDialog.asksaveasfilename(
		title="Where would you like to save the DOL file?", 
		initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
		initialfile=newFilenameSuggestion,
		defaultextension='.dol',
		filetypes=[ ("DOL files", ".dol"), ("All files", "*") ]
		)
	if targetFile == '': return # User canceled the operation

	# Validate and normalize the path input
	targetFile = os.path.normpath( targetFile )
	targetDir = os.path.split( targetFile )[0].encode('utf-8').strip()
	if not os.path.exists( targetDir ): # Failsafe
		msg( '"{}" seems to be an invalid folder path!'.format(targetFile) )
		return

	# Remember current settings
	settings.set( 'General Settings', 'defaultSearchDirectory', targetDir )
	settings.set( 'General Settings', 'defaultFileFormat', 'dol' )
	saveOptions()

	# Redirect the path and file extension for the save operation
	dol.path = targetFile
	dol.type = 'dol'

	# Create a new file and save the currently loaded dol data to it
	open( targetFile, 'a' ).close() # Creates an empty file to write to
	saveSuccessful = saveCodes()

	# Reinitialize with this new file
	if saveSuccessful:
		readRecievedFile( targetFile, defaultProgramStatus='Changes Saved', checkForCodes=False )


def modifyDol( offsetOfChange, code, modName='' ):

	""" This is used by the primary save function. It handles making changes (excluding some reversions) 
		to the DOL in order to track changes made to it, and notify the user of conflicts. 
		"Free space" regions for injection code are organized independently and not considered by this."""

	newCodeLength = len( code ) / 2 # in bytes
	injectionEnd = offsetOfChange + newCodeLength
	conflictDetected = False

	for regionStart, codeLength, modPurpose in genGlobals['modifiedRegions']:
		regionEnd = regionStart + codeLength

		if offsetOfChange < regionEnd and regionStart < injectionEnd: # The regions overlap by some amount.
			conflictDetected = True
			break

	if conflictDetected:
		if modName: # Case to silently fail when uninstalling a mod previously detected to have a problem
			cmsg( '\nA conflict (writing overlap) was detected between these two changes:\n\n"' + \
				  modPurpose + '"\n\tOffset: ' + hex(regionStart) + ',  Code End: ' + hex(regionEnd) + '\n\n"' + \
				  modName + '"\n\tOffset: ' + hex(offsetOfChange) + ',  Code End: ' + hex(injectionEnd) + \
				  '\n\nThese cannot both be enabled. "' + modName + '" will not be enabled. "' + \
				  modPurpose + '" may need to be reinstalled.', 'Conflicting Changes Detected' )
	else:
		# No problems; save the code change to the DOL and remember this change
		replaceHex( offsetOfChange, code )
		genGlobals['modifiedRegions'].append( (offsetOfChange, newCodeLength, modName) )
	
	return conflictDetected


def saveCodes(): # (i.e. the magic)

	""" The primary save function, which scans through all mods for mods that should be enabled and 
		makes their code changes in the DOL's data. This is done in two passes; the first pass restores 
		vanilla code from disabled mods and collects Gecko codes, and the second pass modifies the DOL 
		for enabled mods."""

	tic = time.clock()
	
	# Validate the loaded DOL file (make sure one was loaded and its file path is still good)
	if not dol.path or not dol.data:
		msg( 'It appears that no file is loaded, good sir or madam.' )
		return False
	elif not os.path.exists( dol.path ):
		msg( 'The given file could not be found. Possibly due to it being deleted or moved.' )
		return False

	genGlobals['modifiedRegions'] = [] # Used to track static overwrites and to watch for conflicts
	defaultGameSettingsInstalled = False

	if not onlyUpdateGameSettings.get():
		# Check for conflicts among the code regions selected for use
		allCodeRegions = getCustomCodeRegions()
		if regionsOverlap( allCodeRegions ):
			return False

		# Notify the user of incompatibility between the crash printout code and the Aux Code Regions, if they're both enabled
		if settingsFile.alwaysEnableCrashReports and overwriteOptions[ 'Aux Code Regions' ].get():
			for mod in genGlobals['allMods']:
				if mod.name == "Enable OSReport Print on Crash":
					msg( 'The Aux Code Regions are currently enabled for custom code, however this area is required for the "Enable '
							'OSReport Print on Crash" code to function, which is very useful for debugging crashes and is therefore '
							'enabled by default. \n\nYou can easily resolve this by one of three ways: 1) disable use of the Aux Code '
							'Regions (and restore that area to vanilla code), 2) Open the "settings.py" file in a text editor and set '
							'the option "alwaysEnableCrashReports" to False, or 3) remove the "Enable OSReport Print on Crash" code '
							"from your library (or comment it out so it's not picked up by MCM).", 'Aux Code Regions Conflict' )
					return

		# Update the GUI
		clearSummaryTab() # Clears the summary tab's lists of installed mods/SFs.
		programStatus.set( 'Gathering Preliminary Data...' )
		programStatusLabel.update()

		standaloneFunctionsUsed = []	# Tracks functions that actually make it into the DOL
		spaceForGeckoCodelist = gecko.spaceForGeckoCodelist *2 # This is the max number of characters (nibbles) available in the region designated for the codelist (in settings.py)
		geckoCodelistRegionFull = False
		removingSomeGeckoCodes = False
		geckoCodes = ''
		totalModsToInstall = 0
		geckoSummaryReport = [] # Same as other summaryReports, but with the mod object added
		
		# Prelimanary code-saving pass; restore code from disabled mods, and collect Gecko codes
		for mod in genGlobals['allMods']:
			if mod.state == 'unavailable': continue

			# Revert code for all disabled mods to normal vanilla Melee, to prevent possibilities of them conflicting with mods that will be enabled.
			elif mod.state == 'disabled' or mod.state == 'pendingDisable':

				# Process each code change tuple (each representing one change in the file) given for this mod for the current game version.
				for changeType, customCodeLength, offsetString, originalCode, _, preProcessedCustomCode in getModCodeChanges( mod ):
					if changeType == 'static' or changeType == 'injection':
						dolOffset = normalizeDolOffset( offsetString )
						originalHex = ''.join( originalCode.split() ) # Removes all line breaks & spaces. (Comments should already be removed.)

						if validHex( originalHex ): replaceHex( dolOffset, originalHex )
						else:
							vanillaCode = getVanillaHex( dolOffset, byteCount=customCodeLength )
							if not vanillaCode:
								msg( 'Warning! Invalid hex was found in the original code for "' + mod.name + '", and no vanilla DOL was found in the Original DOLs folder! ' 
									 'Unable to refer to original code, which means that this mod could not be properly uninstalled.' )
							else:
								replaceHex( dolOffset, vanillaCode )
								msg( 'Warning! Invalid hex was found in the original code for "' + mod.name + '". The original code from a vanilla DOL was used instead.')
						
					elif changeType == 'gecko' and mod.state == 'pendingDisable': 
						removingSomeGeckoCodes = True # This state means they were previously enabled, which also means gecko.environmentSupported = True

				# Make sure Gecko mod states are correct
				if mod.state == 'pendingDisable':
					if mod.type == 'gecko' and not overwriteOptions[ 'EnableGeckoCodes' ].get(): 
						mod.setState( 'unavailable' )
					else: mod.setState( 'disabled' )

			# Collect the gecko codes into a string
			elif mod.state == 'enabled' or mod.state == 'pendingEnable':
				
				if mod.type == 'gecko' and gecko.environmentSupported:
					if not geckoCodelistRegionFull: 
						for changeType, customCodeLength, _, _, _, preProcessedCustomCode in getModCodeChanges( mod ):
							if changeType != 'gecko': continue

							if preProcessedCustomCode != '' and validHex( preProcessedCustomCode ): # latter check will currently fail with custom syntaxes. #todo?
								# Confirm that there is enough space for the Gecko codes selected.
								if len( geckoCodes ) + ( customCodeLength * 2 ) + 32 <= spaceForGeckoCodelist: # 32 (i.e. 16 bytes; but counting in nibbles here) added for codelist wrapper.
									geckoCodes += preProcessedCustomCode
									mod.setState( 'enabled' )
									dolOffset = gecko.codelistRegionStart + 8 + len( geckoCodes )/2
									geckoSummaryReport.append( (mod.name, mod.type, 'Gecko code', 'gecko', dolOffset, customCodeLength) )
								else:
									geckoCodelistRegionFull = True
									msg( "There's not enough free space for all of the Gecko codes you've selected; "
											"there is currently a region of " + uHex(spaceForGeckoCodelist/2) + " bytes designated "
											"for Gecko codes.", "The Region for Gecko Codes is Full" )
									mod.setState( 'pendingEnable' )
									break
							else: 
								msg( 'There was an error while processing the code for "' + mod.name + '" (invalid hex or unable to process custom code).' )
								break

				totalModsToInstall += 1
		# End of preliminary pass.
				
		# Save the selected Gecko codes to the DOL, and determine the adjusted code regions to use for injection/standalone code.
		if geckoCodes:
			# Ensure that the codelist length will be a multiple of 4 bytes (so that injection code after it doesn't crash from bad branches).
			wrappedGeckoCodes = '00D0C0DE00D0C0DE' + geckoCodes + 'F000000000000000'
			finalGeckoCodelistLength = roundTo32( len(wrappedGeckoCodes)/2, base=4 ) # Rounds up to closest multiple of 4 bytes
			paddingLength = finalGeckoCodelistLength - len(wrappedGeckoCodes)/2 # in bytes
			padding = '00' * paddingLength
			wrappedGeckoCodes += padding

			# Need to get a new list of acceptable code regions; one that reserves space for the Gecko codelist/codehandler
			allCodeRegions = getCustomCodeRegions( codelistStartPosShift=finalGeckoCodelistLength, codehandlerStartPosShift=gecko.codehandlerLength )

		else: # No Gecko codes to be installed
			wrappedGeckoCodes = ''

			if removingSomeGeckoCodes: # Then the regions that were used for them should be restored.
				if overwriteOptions[ 'EnableGeckoCodes' ].get(): 
					restoreGeckoParts = True # If they've already enabled these regions, the following changes should be fine and we don't need to ask.
				else:
					restoreGeckoParts = tkMessageBox.askyesno( 'Gecko Parts Restoration', 'All Gecko codes have been removed. '
						'Would you like to restore the regions used for the Gecko codehandler and codelist ({} and {}) to vanilla Melee?'.format(gecko.codehandlerRegion, gecko.codelistRegion) )

				if restoreGeckoParts:
					if not gecko.environmentSupported: # Failsafe; if removingSomeGeckoCodes, gecko.environmentSupported should be True
						msg( 'The configuration for Gecko codes seems to be incorrect; unable to uninstall Gecko codes and restore the Gecko code regions.' )
					else:
						vanillaHexAtHookOffset = getVanillaHex( gecko.hookOffset )

						vanillaCodelistRegion = getVanillaHex( gecko.codelistRegionStart, byteCount=gecko.spaceForGeckoCodelist )
						vanillaCodehandlerRegion = getVanillaHex( gecko.codehandlerRegionStart, byteCount=gecko.spaceForGeckoCodehandler )

						if not vanillaHexAtHookOffset or not vanillaCodelistRegion or not vanillaCodehandlerRegion:
							msg( 'Unable to restore the original hex at the location of the codehandler hook, or the areas for the Gecko codelist and codehandler. '
								 'This is likely due to a missing original copy of the DOL, which should be here:\n\n' + dolsFolder + '\n\nThe filename should be "[region] [version].dol", '
								 'for example, "NTSC 1.02.dol". Some mods may have been uninstalled, however you will need to reselect and save the new [non-Gecko] codes that were to be installed.',
								 'Unable to find an original copy of the DOL' )

							# Unexpected failsafe scenario. We'll be ignoring the areas occupied by most of the Gecko stuff (hook and codehandler); it will remain in-place. 
							# Inefficient, but what're ya gonna do. Should at least be functional.
							wrappedGeckoCodes = '00D0C0DE00D0C0DEF000000000000000' # Empty codelist; still need this; maybe? #totest
							allCodeRegions = getCustomCodeRegions( codelistStartPosShift=16, codehandlerStartPosShift=gecko.codehandlerLength )
							addToInstallationSummary( geckoInfrastructure=True )
						else:
							# Remove the branch to the codehandler and return this point to the vanilla code instruction.
							replaceHex( gecko.hookOffset, vanillaHexAtHookOffset)

							# Restore the free space regions designated for the Gecko codelist and codehandler
							replaceHex( gecko.codelistRegionStart, vanillaCodelistRegion )
							replaceHex( gecko.codehandlerRegionStart, vanillaCodehandlerRegion )

		# Zero-out the regions that will be used for custom code.
		for regionStart, regionEnd in allCodeRegions:
			regionLength = regionEnd - regionStart # in bytes
			replaceHex( regionStart, '00' * regionLength )

		# If this is Melee, nop branches required for using the USB Screenshot regions, if those regions are used.
		if dol.isMelee and ( ('ScreenshotRegions' in overwriteOptions and overwriteOptions['ScreenshotRegions'].get())
							or ('Screenshot Regions' in overwriteOptions and overwriteOptions['Screenshot Regions'].get()) ):
			screenshotRegionNopSites = { 'NTSC 1.03': (0x1a1b64, 0x1a1c50), 'NTSC 1.02': (0x1a1b64, 0x1a1c50), 'NTSC 1.01': (0x1a151c, 0x1a1608),
										 'NTSC 1.00': (0x1a0e1c, 0x1a0f08), 'PAL 1.00':  (0x1a2668, 0x1a2754) }
			problemWithNop = modifyDol( screenshotRegionNopSites[dol.revision][0], '60000000', 'Screenshot Region NOP' )
			problemWithNop2 = modifyDol( screenshotRegionNopSites[dol.revision][1], '60000000', 'Screenshot Region NOP' )
			if problemWithNop or problemWithNop2: 
				msg( 'One or more NOPs for the Screenshot Region could not be added, most likely due to a conflicting mod.' )
			else:
				nopSummaryReport = []
				nopSummaryReport.append( ('Code overwrite', 'static', screenshotRegionNopSites[dol.revision][0], 4) )
				nopSummaryReport.append( ('Code overwrite', 'static', screenshotRegionNopSites[dol.revision][1], 4) )
				addToInstallationSummary( 'USB Screenshot Region NOP', 'static', nopSummaryReport, isMod=False ) # , iid='screenshotRegionNops'

		# Install any Gecko codes that were collected
		if geckoCodes: # gecko.environmentSupported must be True
			# Replace the codehandler's codelist RAM address
			codelistAddress = offsetInRAM( gecko.codelistRegionStart, dol.sectionInfo ) + 0x80000000
			codelistAddrBytes = struct.pack( '>I', codelistAddress ) # Packing to bytes as a big-endian unsigned int (4 bytes)
			codehandlerCodelistAddr = gecko.codehandler.find( b'\x3D\xE0' ) # Offset of the first instruction to load the codelist address
			gecko.codehandler[codehandlerCodelistAddr+2:codehandlerCodelistAddr+4] = codelistAddrBytes[:2] # Update first two bytes
			gecko.codehandler[codehandlerCodelistAddr+6:codehandlerCodelistAddr+8] = codelistAddrBytes[2:] # Update last two bytes

			# Calculate branch distance from the hook to the destination of the Gecko codehandler's code start
			geckoHookDistance = calcBranchDistance( gecko.hookOffset, gecko.codehandlerRegionStart )

			# Look for the first instruction in the codehandler, to offset the hook distance, if needed
			codehandlerStartOffset = gecko.codehandler.find( b'\x94\x21' )
			if codehandlerStartOffset != -1:
				geckoHookDistance += codehandlerStartOffset

			# Add the Gecko codehandler hook
			geckoHook = assembleBranch( 'b', geckoHookDistance )
			modifyDol( gecko.hookOffset, geckoHook, 'Gecko Codehandler Hook' )

			# Add the codehandler and codelist to the DOL
			modifyDol( gecko.codelistRegionStart, wrappedGeckoCodes, 'Gecko codes list' )
			modifyDol( gecko.codehandlerRegionStart, hexlify(gecko.codehandler), 'Gecko Codehandler' )

		else:
			geckoSummaryReport = [] # May have been added to. Clear it.

		def allocateSpaceInDol( dolSpaceUsedDict, customCodeLength ):
			customCodeOffset = -1

			for i, ( areaStart, areaEnd ) in enumerate( allCodeRegions ):
				areaName = 'area' + str(i + 1) + 'used'
				spaceUsed = dolSpaceUsedDict[areaName] # value in bytes
				spaceRemaining = areaEnd - areaStart - spaceUsed

				# If there's space remaining in this area, assign the code to here
				if customCodeLength <= spaceRemaining:
					customCodeOffset = areaStart + spaceUsed

					# If this code isn't a multiple of 4 bytes, add some padding to ensure the next code will be aligned
					if customCodeLength % 4 != 0:
						customCodeLength += 4 - (customCodeLength % 4)

					dolSpaceUsedDict[areaName] += customCodeLength # Updates the used area reference.
					break

			return customCodeOffset # In bytes

		# Create a dictionary to keep track of space in the dol that's available for injection codes
		dolSpaceUsed = {}
		for i in range( len(allCodeRegions) ):
			# Add a key/value pair to keep track of how much space is used up for each code range.
			key = 'area' + str(i + 1) + 'used'
			dolSpaceUsed[key] = 0

		# Primary code-saving pass.
		standaloneFunctions = genGlobals['allStandaloneFunctions'] # Dictionary. Key='functionName', value=( functionOffset, functionCustomCode, functionPreProcessedCustomCode )
		modInstallationAttempt = 0
		noSpaceRemaining = False

		for mod in genGlobals['allMods']:
			if mod.state == 'unavailable' or mod.type == 'gecko': continue # Gecko codes have already been processed.

			elif mod.state == 'enabled' or mod.state == 'pendingEnable':
				modInstallationAttempt += 1
				programStatus.set( 'Installing Mods (' + str( round( (float(modInstallationAttempt) / totalModsToInstall) * 100, 1 ) ) + '%)' )
				programStatusLabel.update()

				problemWithMod = False
				dolSpaceUsedBackup = dolSpaceUsed.copy() # This copy is used to revert changes in case there is a problem with saving this mod.
				newlyMappedStandaloneFunctions = [] # Tracked so that if this mod fails any part of installation, the standalone functions dictionary can be restored (installation offsets restored to -1).
				summaryReport = []

				# Allocate space for required standalone functions
				if not noSpaceRemaining:
					# SFs are not immediately added to the DOL because they too may reference unmapped functions.
					requiredStandaloneFunctions, missingFunctions = getRequiredStandaloneFunctionNames( mod )

					# Now that the required standalone functions for this mod have been assigned space, add them to the DOL.
					if missingFunctions:
						msg( mod.name + ' cannot not be installed because the following standalone functions are missing:\n\n' + grammarfyList(missingFunctions) )
						problemWithMod = True

					else:
						# Map any new required standalone functions to the DOL if they have not already been assigned space.
						for functionName in requiredStandaloneFunctions:
							functionOffset, functionCustomCode, functionPreProcessedCustomCode = standaloneFunctions[functionName]

							if functionName not in standaloneFunctionsUsed: # Has not been added to the dol. Attempt to map it.
								customCodeLength = getCustomCodeLength( functionPreProcessedCustomCode )
								customCodeOffset = allocateSpaceInDol( dolSpaceUsed, customCodeLength )

								if customCodeOffset == -1:
									# No more space in the DOL. (Mods requiring custom code space up until this one will be still be saved.)
									noSpaceRemaining = True
									problemWithMod = True
									msg( "There's not enough free space for all of the codes you've selected. "
										 "\n\nYou might want to try again after selecting fewer Injection Mods and/or Gecko codes. "
										 "\n\nThe regions currently designated as free space can be configured and viewed via the 'Code-Space Options' "
										 'button, and the "settings.py" file.', "The DOL's regions for custom code are full" )
									break
								else:
									# Storage location determined; update the SF dictionary with an offset for it
									standaloneFunctions[functionName] = ( customCodeOffset, functionCustomCode, functionPreProcessedCustomCode )
									newlyMappedStandaloneFunctions.append( functionName )

							else: # This mod uses one or more functions that are already allocated to go into the DOL
								sfLength = getCustomCodeLength( functionPreProcessedCustomCode )
								summaryReport.append( ('SF: ' + functionName, 'standalone', functionOffset, sfLength) )

						if newlyMappedStandaloneFunctions:
							# Add this mod's SFs to the DOL
							for functionName in newlyMappedStandaloneFunctions:
								functionOffset, functionCustomCode, functionPreProcessedCustomCode = standaloneFunctions[functionName]

								# Process the function code to remove comments/whitespace, assemble it into bytecode if necessary, and replace custom syntaxes
								returnCode, finishedCode = customCodeProcessor.resolveCustomSyntaxes( functionOffset, functionCustomCode, functionPreProcessedCustomCode, mod.includePaths )

								if returnCode != 0 and returnCode != 100:
									specifics = 'An error occurred while processing this custom code:\n\n' + functionCustomCode + '\n\n'
									cmsg( specifics + finishedCode, 'Error 01 Resolving Custom Syntaxes' )
								elif finishedCode == '' or not validHex( finishedCode ):
									problemWithMod = True
									msg( 'There was an error while processing the standalone function "' + functionName + '" for "' + mod.name + '" (missing '
										 'standalone function code, or invalid hex after processing). This mod will not be installed.\n\n' + finishedCode )
								else: 
									problemWithMod = modifyDol( functionOffset, finishedCode, mod.name + ' standalone function' )

								if problemWithMod: break
								else: summaryReport.append( ('SF: ' + functionName, 'standalone', functionOffset, len(finishedCode)/2) )
				
				# Add this mod's code changes & custom code (non-SFs) to the dol.
				if not problemWithMod:
					for codeChange in getModCodeChanges( mod ):
						changeType, customCodeLength, offsetString, originalCode, customCode, preProcessedCustomCode = codeChange

						if ( changeType == 'standalone' or changeType == 'injection' ) and noSpaceRemaining:
							problemWithMod = True
							break

						if changeType == 'static':
							dolOffset = normalizeDolOffset( offsetString )
							returnCode, finishedCode = customCodeProcessor.resolveCustomSyntaxes( dolOffset, customCode, preProcessedCustomCode, mod.includePaths )

							if returnCode != 0 and returnCode != 100:
								specifics = 'An error occurred while processing this custom code:\n\n' + customCode + '\n\n'
								cmsg( specifics + finishedCode, 'Error 02 Resolving Custom Syntaxes' )
							elif not finishedCode or not validHex( finishedCode ):
								msg( 'There was an error while processing code for "' + mod.name + '".' )
								problemWithMod = True
								break
							else:
								problemWithMod = modifyDol( dolOffset, finishedCode, mod.name )
								if problemWithMod: break
								else: summaryReport.append( ('Code overwrite', changeType, dolOffset, customCodeLength) )

						elif changeType == 'injection':
							injectionSite = normalizeDolOffset( offsetString )

							if injectionSite < 0x100 or injectionSite > dol.maxDolOffset:
								problemWithMod = True
								msg('The injection site, ' + offsetString + ', for "' + mod.name + '" is out of range of the DOL.\n\nThis code will be omitted from saving.')
								break
							else:
								if preProcessedCustomCode == '':
									msg( 'There was an error while processing an injection code for "' + mod.name + '".' )
									problemWithMod = True
									break
								else:
									# Find a place for the custom code.
									customCodeOffset = allocateSpaceInDol( dolSpaceUsed, customCodeLength )
								
									if customCodeOffset == -1:
										# No more space in the DOL. Injection codes up to this one (and all other changes) will be still be saved.
										noSpaceRemaining = True
										usedSpaceString = ''
										for i, regionRange in enumerate( allCodeRegions ):
											( start, end ) = regionRange
											if i != ( len(allCodeRegions) - 1 ): usedSpaceString = usedSpaceString + hex(start) + ' to ' + hex(end) + ', '
											else: usedSpaceString = usedSpaceString + ' and ' + hex(start) + ' to ' + hex(end) + '.'
										msg( "There's not enough free space for all of the codes you've selected. "
											 "\n\nYou might want to try again after selecting fewer Injection Mods. "
											 "\n\n               -         -         -      \n\nThe regions currently designated as "
											 "free space in the DOL are " + usedSpaceString, "The DOL's regions for custom code are full" )
										break
									else:
										# Calculate the initial branch from the injection site
										branch = assembleBranch( 'b', calcBranchDistance( injectionSite, customCodeOffset) )

										# If the calculation above was successful, write the created branch into the dol file at the injection site
										if branch == -1: problemWithMod = True
										else: problemWithMod = modifyDol( injectionSite, branch, mod.name + ' injection site' )
										if problemWithMod: break
										else: summaryReport.append( ('Branch', 'static', injectionSite, 4) ) # changeName, changeType, dolOffset, customCodeLength

										returnCode, preProcessedCustomCode = customCodeProcessor.resolveCustomSyntaxes( customCodeOffset, customCode, preProcessedCustomCode, mod.includePaths )

										if returnCode != 0 and returnCode != 100:
											specifics = 'An error occurred while processing this custom code:\n\n' + customCode + '\n\n'
											cmsg( specifics + preProcessedCustomCode, 'Error 03 Resolving Custom Syntaxes' )
											problemWithMod = True
											break
										elif preProcessedCustomCode == '' or not validHex( preProcessedCustomCode ):
											msg( 'There was an error while replacing custom branch syntaxes in an injection code for "' + mod.name + '".' )
											problemWithMod = True
											break
										else:
											# If the return code was 100, the last instruction was created by a custom branch syntax, which was deliberate and we don't want it replaced.
											if returnCode == 0:
												# Check if the last instruction in the custom code is a branch or zeros. If it is, replace it with a branch back to the injection site.
												commandByte = preProcessedCustomCode[-8:][:-6].lower()
												if commandByte == '48' or commandByte == '49' or commandByte == '4a' or commandByte == '4b' or commandByte == '00':
													branchBack = assembleBranch( 'b', calcBranchDistance( (customCodeOffset + len(preProcessedCustomCode)/2 - 0x8), injectionSite) )

													if branchBack == -1:
														problemWithMod = True
														break
													else: # Success; replace the instruction with the branch created above
														preProcessedCustomCode = preProcessedCustomCode[:-8] + branchBack

											# Add the injection code to the DOL.
											problemWithMod = modifyDol( customCodeOffset, preProcessedCustomCode, mod.name + ' injection code' )
											if problemWithMod: break
											else: summaryReport.append( ('Injection code', changeType, customCodeOffset, customCodeLength) )

				if problemWithMod:
					# Revert all changes associated with this mod to the game's vanilla code.
					for codeChange in getModCodeChanges( mod ):
						if codeChange[0] == 'static' or codeChange[0] == 'injection':
							offset = normalizeDolOffset( codeChange[2] )
							originalCode = codeChange[3]

							modifyDol( offset, originalCode ) # Should silently fail if attempting to overrite what was already changed by another mod (changes existing in modifiedRegions)
						# Any extra code left in the 'free space' regions will just be overwritten by further mods or will otherwise not be used.

					# Restore the dictionary used for tracking free space in the DOL to its state before making changes for this mod.
					dolSpaceUsed = dolSpaceUsedBackup

					# Restore the standalone functions dictionary to as it was before this mod (set offsets back to -1).
					for functionName in newlyMappedStandaloneFunctions:
						functionOffset, functionCustomCode, functionPreProcessedCustomCode = standaloneFunctions[functionName]

						standaloneFunctions[functionName] = ( -1, functionCustomCode, functionPreProcessedCustomCode )
					
					# Update the GUI to reflect changes.
					mod.setState( 'disabled' )
				else:
					# Remember that the standalone functions used for this mod were added to the dol.
					standaloneFunctionsUsed.extend( newlyMappedStandaloneFunctions )

					# Update the GUI to reflect changes.
					mod.setState( 'enabled' )
					addToInstallationSummary( mod.name, mod.type, summaryReport )

					if mod.name == 'Default Game Settings': # Prevent updates from the Default Game Settings tab
						defaultGameSettingsInstalled = True

		# End of primary code-saving pass. Finish updating the Summary tab.
		if geckoSummaryReport:
			addToInstallationSummary( geckoInfrastructure=True )

			for geckoReport in geckoSummaryReport:
				summaryReport = [ geckoReport[2:] ]
				addToInstallationSummary( geckoReport[0], geckoReport[1], summaryReport )

	# Check for modules composed of only standalone functions; these won't be set as enabled by the above code
	if standaloneFunctionsUsed:
		for mod in genGlobals['allMods']:
			if mod.state == 'unavailable': continue

			# Check if this is a SF-only module
			functionsOnly = True
			functionNames = []
			for codeChange in getModCodeChanges( mod ):
				if not codeChange[0] == 'standalone': 
					functionsOnly = False
					break
				else:
					functionNames.append( codeChange[2] )

			if functionsOnly:
				# Check if this module is used
				for funcName in functionNames:
					if funcName in standaloneFunctionsUsed:
						print 'SF-only module', mod.name, 'is detected in save routine'
						mod.setState( 'enabled' ) # Already automatically added to the Standalone Functions table in the Summary Tab
						break # only takes one to make it count
				else: # loop didn't break; no functions for this mod used
					print 'SF-only module', mod.name, 'not detected in save routine'
					mod.setState( 'disabled' )

	toc = time.clock()
	print '\nMod library save time:', toc-tic

	# End of the 'not onlyUpdateGameSettings' block
	updateSummaryTabTotals()

	# If this is SSBM, check the Default Game Settings tab for changes to save. (function execution skips to here if onlyUpdateGameSettings=True)
	if dol.isMelee and dol.revision in settingsTableOffset and not defaultGameSettingsInstalled:
		for widgetSettingID in gameSettingsTable:
			selectedValue = currentGameSettingsValues[widgetSettingID].get()
			valueInDOL = getGameSettingValue( widgetSettingID, 'fromDOL' )
			if selectedValue != valueInDOL:
				tableOffset = gameSettingsTable[widgetSettingID][0]
				fileOffset = settingsTableOffset[dol.revision] + tableOffset

				# If the game settings tuple is greater than 3, it means there are strings that need to be attributed to a number that the game uses.
				if widgetSettingID == 'damageRatioSetting': newHex = toHex( round(float(selectedValue) * 10, 1), 2 )
				elif widgetSettingID == 'stageToggleSetting' or widgetSettingID == 'itemToggleSetting': newHex = selectedValue
				elif widgetSettingID == 'itemFrequencySetting':
					if selectedValue == 'None': newHex = 'FF'
					else:
						for i, item in enumerate( gameSettingsTable['itemFrequencySetting'][4:] ):
							if item == selectedValue:
								newHex = toHex( i, 2 )
								break
				elif len( gameSettingsTable[widgetSettingID] ) > 3: # For cases where a string is used, get the index of the current value.
					for i, item in enumerate( gameSettingsTable[widgetSettingID][3:] ):
						if item == selectedValue: 
							newHex = toHex( i, 2 )
							break
				else: newHex = toHex( selectedValue, 2 ) 

				# Set the new values in the DOL and update the gui to show that this has been saved.
				decameledName = convertCamelCase( widgetSettingID )
				modifyDol( fileOffset, newHex, decameledName + ' (from the Default Game Settings tab)' )
				widgetControlID = widgetSettingID[:-7]+'Control'
				updateDefaultGameSettingWidget( widgetControlID, selectedValue, False )

				# Update the stage and items selections windows (if they're open) with the new values.
				if widgetSettingID == 'stageToggleSetting' and root.stageSelectionsWindow: root.stageSelectionsWindow.updateStates( selectedValue, True, False )
				elif widgetSettingID == 'itemToggleSetting' and root.itemSelectionsWindow: root.itemSelectionsWindow.updateStates( selectedValue, True, False )

	saveSuccessStatus = saveDolToFile()

	return saveSuccessStatus


def formatAsGecko( mod, dolRevision, createForGCT ):

	""" Formats a mod's code into Gecko code form. If this is for an INI file, human-readable mod-name/author headers and 
		whitespace are included. If this is for a GCT file, it'll just be pure hex data (though returned as a string). """

	# def resolveSfReferences( preProcessedCode ): #todo finish allowing SFs in Gecko codes
	# 	# Check for special syntaxes; only one kind can be adapted to use by Gecko codes (references to SFs)
	# 	if '|S|' not in preProcessedCustomCode: # Contains no special syntaxes
	# 		return preProcessedCustomCode

	# 	for section in preProcessedCustomCode.split( '|S|' ):
	# 		if section.startswith( 'sym__' ): # Contains a function symbol; something like 'lis r3, (<<function>>+0x40)@h'
	# 			resolvedCode = ''
	# 			break
	# 		elif section.startswith( 'sbs__' ): # Something of the form 'bl 0x80001234' or 'bl <function>'; replace the latter with the function code
	# 			if '<' in section and section.endswith( '>' ): # The syntax references a standalone function
	# 				targetFunctionName = section.split( '<' )[1].replace( '>', '' )
	# 				preProcessedSfCode = genGlobals['allStandaloneFunctions'][targetFunctionName][2]
	# 				resolvedSfCode = resolveSfReferences( preProcessedSfCode )

	# 				if 
	# 			else: break # Must be a special branch syntax using a RAM address (can't be used since we don't know where this code will be)
	# 	else: # Success; loop above did not break

	containsSpecialSyntax = False
	codeChanges = []

	for changeType, customCodeLength, offset, _, _, preProcessedCustomCode in mod.data[dolRevision]:
		# Check for special syntaxes; only one kind can be adapted for use by Gecko codes (references to SFs)
		if '|S|' in preProcessedCustomCode:
			containsSpecialSyntax = True
			break
		elif changeType != 'gecko':
			ramAddress = normalizeRamAddress( offset, dolObj=originalDols[dolRevision] )
			sRamAddress = toHex( ramAddress, 6 ) # Pads a hex string to 6 characters long (extra characters added to left side)
		
		if changeType == 'standalone': # Not supported for Gecko codes
			containsSpecialSyntax = True
			break

		elif changeType == 'static':

			if createForGCT:
				if customCodeLength == 1:
					codeChanges.append( '00{}000000{}'.format(sRamAddress, preProcessedCustomCode) )
				elif customCodeLength == 2:
					codeChanges.append( '02{}0000{}'.format(sRamAddress, preProcessedCustomCode) )
				elif customCodeLength == 4:
					codeChanges.append( '04{}{}'.format(sRamAddress, preProcessedCustomCode) )
				else:
					sByteCount = toHex( customCodeLength, 8 ) # Pads a hex string to 8 characters long (extra characters added to left side)
					codeChanges.append( '06{}{}{}'.format(sRamAddress, sByteCount, preProcessedCustomCode) )

			else: # Creating a human-readable INI file
				if customCodeLength == 1:
					codeChanges.append( '00{} 000000{}'.format(sRamAddress, preProcessedCustomCode) )
				elif customCodeLength == 2:
					codeChanges.append( '02{} 0000{}'.format(sRamAddress, preProcessedCustomCode) )
				elif customCodeLength == 4:
					codeChanges.append( '04{} {}'.format(sRamAddress, preProcessedCustomCode) )
				else:
					sByteCount = toHex( customCodeLength, 8 ) # Pads a hex string to 8 characters long (extra characters added to left side)
					beautifiedHex = customCodeProcessor.beautifyHex( preProcessedCustomCode )
					codeChanges.append( '06{} {}\n{}'.format(sRamAddress, sByteCount, beautifiedHex) )

		elif changeType == 'injection':
			opCode = preProcessedCustomCode[-8:][:-6].lower() # Of the last instruction

			if createForGCT:
				# Check the last instruction; it may be a branch placeholder, which should be replaced
				if opCode in ( '48', '49', '4a', '4b', '00' ):
					preProcessedCustomCode = preProcessedCustomCode[:-8]
					customCodeLength -= 4

				# Determine the line count and the final bytes that need to be appended
				quotient, remainder = divmod( customCodeLength, 8 ) # 8 represents the final bytes per line
				sLineCount = toHex( quotient + 1, 8 )
				if remainder == 0: # The remainder is how many bytes extra there will be after the 'quotient' number of lines above
					preProcessedCustomCode += '6000000000000000'
				else:
					preProcessedCustomCode += '00000000'

				codeChanges.append( 'C2{}{}{}'.format(sRamAddress, sLineCount, preProcessedCustomCode) )

			else: # Creating a human-readable INI file
				# Check the last instruction; it may be a branch placeholder, which should be replaced
				if opCode in ( '48', '49', '4a', '4b', '00' ):
					beautifiedHex = customCodeProcessor.beautifyHex( preProcessedCustomCode[:-8] )
					customCodeLength -= 4
				else:
					beautifiedHex = customCodeProcessor.beautifyHex( preProcessedCustomCode )

				# Determine the line count and the final bytes that need to be appended
				quotient, remainder = divmod( customCodeLength, 8 ) # 8 represents the final bytes per line
				sLineCount = toHex( quotient + 1, 8 )
				if remainder == 0: # The remainder is how many bytes extra there will be after the 'quotient' number of lines above
					beautifiedHex += '\n60000000 00000000'
				else:
					beautifiedHex += ' 00000000'

				codeChanges.append( 'C2{} {}\n{}'.format(sRamAddress, sLineCount, beautifiedHex ) )

		elif changeType == 'gecko': # Not much going to be needed here!
			if createForGCT:
				codeChanges.append( preProcessedCustomCode )
			else: # Creating a human-readable INI file
				codeChanges.append( customCodeProcessor.beautifyHex( preProcessedCustomCode ) )

	if containsSpecialSyntax:
		return ''
	elif createForGCT:
		return ''.join( codeChanges )
	else:
		return '${} [{}]\n{}'.format( mod.name, mod.auth, '\n'.join(codeChanges) )


def saveGctFile():

	""" Simple wrapper for the 'Save GCT' button. Creates a Gecko Code Type file
		using a tweak of the function used for creating INI files. """

	saveIniFile( createForGCT=True )


def saveIniFile( createForGCT=False ):
	# Check that there are any mods selected
	for mod in genGlobals['allMods']:
		if mod.state == 'enabled' or mod.state == 'pendingEnable': break
	else: # The loop above didn't break, meaning there are none selected
		msg( 'No mods are selected!' )
		return

	# Come up with a default file name for the GCT file
	if dol.gameId: initialFilename = dol.gameId
	else: initialFilename = 'Codes'

	# Set the file type & description
	if createForGCT:
		fileExt = '.gct'
		fileTypeDescription = "Gecko Code Type files"
	else:
		fileExt = '.ini'
		fileTypeDescription = "Code Initialization files"

	# Get a save filepath from the user
	targetFile = tkFileDialog.asksaveasfilename(
		title="Where would you like to save the {} file?".format( fileExt[1:].upper() ),
		initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
		initialfile=initialFilename,
		defaultextension=fileExt,
		filetypes=[ (fileTypeDescription, fileExt), ("All files", "*") ]
		)
	if targetFile == '': return # No filepath; user canceled

	# Get the revision for this codeset
	if dol.revision:
		dolRevision = dol.revision
	else: # Not yet known; prompt the user for it
		revisionWindow = RevisionPromptWindow( 'Choose the region and game version that this codeset is for:', 'NTSC', '02' )

		# Check the values gained from the user prompt (empty strings mean they closed or canceled the window)
		if not revisionWindow.region or not revisionWindow.version: return
		else: 
			dolRevision = revisionWindow.region + ' ' + revisionWindow.version

	# Load the DOL for this revision (if one is not already loaded).
	# This may be needed for formatting the code, in order to calculate RAM addresses
	vanillaDol = loadVanillaDol( dolRevision )
	if not vanillaDol: return

	# Remember current settings
	targetFileDir = os.path.split(targetFile)[0].encode('utf-8').strip()
	settings.set( 'General Settings', 'defaultSearchDirectory', targetFileDir )
	saveOptions()

	# Get and format the individual mods
	geckoFormattedMods = []
	missingTargetRevision = []
	containsSpecialSyntax = []
	for mod in genGlobals['allMods']:
		if mod.state == 'enabled' or mod.state == 'pendingEnable':
			if dolRevision in mod.data:
				geckoCodeString = formatAsGecko( mod, dolRevision, createForGCT )

				if geckoCodeString == '':
					containsSpecialSyntax.append( mod.name )
				else:
					geckoFormattedMods.append( geckoCodeString )

					# Update the mod's status (appearance) so the user knows what was saved
					mod.setState( 'enabled', 'Saved to ' + fileExt[1:].upper() )
			else:
				missingTargetRevision.append( mod.name )

	# Save the text string to a GCT/INI file if any mods were able to be formatted
	if geckoFormattedMods:
		if createForGCT:
			# Save the hex code string to the file as bytes
			hexString = '00D0C0DE00D0C0DE' + ''.join( geckoFormattedMods ) + 'F000000000000000'
			with open( targetFile, 'wb' ) as newFile:
				newFile.write( bytearray.fromhex(hexString) )
		else:
			# Save as human-readable text
			with open( targetFile, 'w' ) as newFile:
				newFile.write( '\n\n'.join(geckoFormattedMods) )
		programStatus.set( fileExt[1:].upper() + ' File Created' )

	# Notify the user of any codes that could not be included
	warningMessage = ''
	if missingTargetRevision:
		warningMessage = ( "The following mods could not be included, because they do not contain "
					"code changes for the DOL revision you've selected:\n\n" + '\n'.join(missingTargetRevision) )
	if containsSpecialSyntax:
		warningMessage += ( "\n\nThe following mods could not be included, because they contain special syntax (such as Standalone Functions or "
					"RAM symbols) which are not currently supported in " + fileExt[1:].upper() + " file creation:\n\n" + '\n'.join(containsSpecialSyntax) )

	if warningMessage:
		cmsg( warningMessage.lstrip() )


def saveDolToFile():
	programStatus.set( '' )
	operationSucceded = False

	# Encode the file data from a hex string to a bytearray
	try:
		dol.writeSig()
		newDolData = bytearray.fromhex( dol.data )

	except:
		msg( 'The new DOL data could not be encoded.', 'Data Encoding Error' ) # Likely due to an invalid hex character.
		return operationSucceded

	# Save the data to disc
	if (dol.type == 'iso' or dol.type == 'gcm') and dol.offset != 0:
		try:
			with open( dol.path, 'r+b') as isoBinary:
				isoBinary.seek( dol.offset  )
				isoBinary.write( newDolData )
			operationSucceded = True

		except: msg( "Unable to save. \n\nBe sure that the file is not being used by another \nprogram (like Dolphin :P)." )

	# Save the data to an external dol file
	elif dol.type == 'dol':
		try:
			with open( dol.path, 'wb') as newDol:
				newDol.write( newDolData )
			operationSucceded = True

		except: msg( "Unable to save. \n\nBe sure that the file is not being used by another program." )

	else: msg( "The filepath doesn't seem to be a DOL, ISO or GCM file, or the DOL's offset in the disc could not be determined.", 'Error.' )

	# If the process above succeeded, perform one final check for pending changes (in this case, this will mostly just handle various GUI updates)
	if operationSucceded:
		playSound( 'menuSelect' )
		programStatus.set( 'Changes Saved' )

		checkForPendingChanges()
	else:
		programStatus.set( 'Changes Not Saved' )

	return operationSucceded


def replaceHex( offset, newHex ):

	""" Simple function to replace hex at a specific offset with new hex. 
		Inputs should be an int and a string, respectively. """

	offset = offset * 2 # Doubled to count by nibbles rather than bytes, since the data is just a string.
	codeEndPoint = offset + len( newHex )
	dol.data = dol.data[:offset] + newHex + dol.data[codeEndPoint:]


def saveCurrentWork( event ):

	""" Global program save function for the CTRL-S hotkey. Determines what to save based on the currently selected tab; 
		if on the Mods Library tab or Game Settings tab, save all current enabled or pending enabled mods and settings to 
		the currently loaded DOL file, or else if on the Mod Construction tab, just save work on the currently selected mod. """

	currentMainNotebookTabSelected = root.nametowidget( mainNotebook.select() )

	if currentMainNotebookTabSelected == modsLibraryTab or currentMainNotebookTabSelected == settingsTab: 
		saveCodes() # Saves current mod selection to the disc or DOL

	elif currentMainNotebookTabSelected == constructionTab and len( constructionNotebook.tabs() ) != 0:
		# Get the mod constructor object for the currently selected mod, and save its changes to the Mods Library
		modConstructor = root.nametowidget( constructionNotebook.select() ).winfo_children()[0]
		modConstructor.saveModToLibrary()


def viewDolHex():
	# Check/ask for a specified hex editor to open the file in.
	if not os.path.exists( settings.get( 'General Settings', 'hexEditorPath' ) ):
		popupWindow = PopupEntryWindow( root, message='Please specify the full path to your hex editor. '
			'(Specifying this path only needs to\nbe done once, and can be changed at any time in the settings.ini file.\nIf you have already set this, '
			"the path seems to have broken.)\n\nNote that this feature only shows you a copy of the data;\nany changes made will not be saved to the file or disc."
			'\n\nPro-tip: In Windows, if you hold Shift while right-clicking on a file, there appears a context menu \n'
			"""option called "Copy as path". This will copy the file's full path into your clipboard. Or if it's\na shortcut, """
			"""you can quickly get the full file path by right-clicking on the icon and going to Properties.""", title='Set hex editor path' )
		hexEditorPath = popupWindow.entryText.replace('"', '')

		if hexEditorPath != '':
			# Update the path in the settings file and global variable.
			settings.set( 'General Settings', 'hexEditorPath', hexEditorPath.encode('utf-8').strip() )
			with open( genGlobals['optionsFilePath'], 'w') as theOptionsFile: settings.write( theOptionsFile ) # Updates a pre-existing settings file entry, or just creates a new file.

	else:
		hexEditorPath = settings.get( 'General Settings', 'hexEditorPath' )
	
	if hexEditorPath != '':
		if problemWithDol(): return

		try:
			filename = os.path.splitext( os.path.basename(dol.path) )[0]
			tempFilePath = scriptHomeFolder + '\\bin\\tempFiles\\' + filename + '_temp.dol'
			createFolders( os.path.split(tempFilePath)[0] )
			
			# Save the current file data to a temporary file.
			with open( tempFilePath, 'wb' ) as newFile:
				newFile.write( bytearray.fromhex(dol.data) )

			# Open the temp file in the user's editor of choice.
			if os.path.exists( hexEditorPath ) and os.path.exists( tempFilePath ):
				command = '"{}" "{}"'.format( hexEditorPath, tempFilePath )
				subprocess.Popen( command, shell=False, stderr=subprocess.STDOUT, creationflags=0x08000000 ) # shell=True gives access to all shell features.

			else:
				msg( "Unable to find the specified hex editor program (or new DOL temporary file). You may want to double check the path saved in the options.ini file." )
		except Exception as err:
			msg( 'There was an unknown problem while creating the DOL temp file.' )
			print err

																				 #========================#
																				# ~ ~ Mods Library Tab ~ ~ #
																				 #========================#

class LabelButton( Label ):

	""" Basically a label that acts as a button, using an image and mouse click/hover events. 
		Used for the edit button and web links. """

	def __init__( self, parent, imageName, callback, hovertext='' ):
		# Get the images needed
		self.nonHoverImage = imageBank.get( imageName + 'Gray' )
		self.hoverImage = imageBank.get( imageName )
		assert self.nonHoverImage, 'Unable to get the {} web link image.'.format( imageName )
		assert self.hoverImage, 'Unable to get the {}Gray web link image.'.format( imageName )

		# Initialize the label with one of the above images
		Label.__init__( self, parent, image=self.nonHoverImage, borderwidth=0, highlightthickness=0, cursor='hand2' )

		# Bind click and mouse hover events
		self.bind( '<1>', callback )
		self.bind( '<Enter>', self.darken )
		self.bind( '<Leave>', self.lighten )

		if hovertext:
			ToolTip( self, hovertext, delay=700, wraplength=800, justify='center' )
		
	def darken( self, event ): self['image'] = self.hoverImage
	def lighten( self, event ): self['image'] = self.nonHoverImage


class ModModule( Frame ):

	""" Serves as both a GUI element, and a container for all of the information on a given mod. """

	def __init__( self, parent, modName, modDesc, modAuth, modData, modType, webLinks, *args, **kw ):
		Frame.__init__( self, parent, *args, **kw )

		self.name = modName
		self.desc = modDesc
		self.auth = modAuth
		self.data = modData  		# A dictionary populated by lists of "codeChange" tuples
		self.type = modType
		self.state = 'disabled'
		self.statusText = StringVar()
		self.highlightFadeAnimationId = None # Used for the border highlight fade animation
		self.webLinks = []

		moduleWidth = 520 			# Mostly just controls the wraplength of text areas.

		# Set the mod "Length" string
		if self.type == 'static':
			lengthString = ''
		else:
			arbitraryGameVersions = []
			for revision, codeChanges in modData.items():
				if revision != 'ALL':
					arbitraryGameVersions.extend( codeChanges )
					break
			if 'ALL' in modData: arbitraryGameVersions.extend( modData['ALL'] )

			length = 0
			for codeChange in arbitraryGameVersions:
				if codeChange[0] != 'static': length += codeChange[1]
			lengthString = '                 Space' + unichr(160) + 'required:' + unichr(160) + uHex(length) # unichr(160) = no-break space

		# Construct the GUI framework.
		self.config( relief='groove', borderwidth=3, takefocus=True )

		# Row 1: Title, author(s), type, and codelength.
		row1 = Frame( self )
		Label( row1, text=modName, font=("Times", 11, "bold"), wraplength=moduleWidth-140, anchor='n' ).pack( side='top', padx=(0,36), pady=2 ) # Right-side horizontal padding added for module type image
		Label( row1, text=' - by ' + modAuth + lengthString, font=("Verdana", 8), wraplength=moduleWidth-160 ).pack( side='top', padx=(0,36) ) #Helvetica
		row1.pack( side='top', fill='x', expand=1 )

		# Row 2: Description.
		row2 = Frame( self )
		Label( row2, text=modDesc, wraplength=moduleWidth-110, padx=8, justify='left' ).pack( side='left', pady=0 )
		row2.pack( side='top', fill='x', expand=1 )

		# Row 3: Status text and buttons
		row3 = Frame( self )

		Label( row3, textvariable=self.statusText, wraplength=moduleWidth-90, padx=35, justify='left' ).pack( side='left' )

		# Set a background image based on the mod type (indicator on the right-hand side of the mod)
		typeIndicatorImage = imageBank.get( self.type + 'Indicator' )
		if typeIndicatorImage:
			bgImage = Label( self, image=typeIndicatorImage, borderwidth=0, highlightthickness=0 )
			bgImage.place( relx=1, x=-10, rely=0.5, anchor='e' )
		else:
			print 'No image found for "' + self.type + 'Indicator' + '"!'

		# Set up a left-click event to all current parts of this module (to toggle the code on/off), before adding any of the other clickable elements.
		# All of these widgets are "tagged" to trigger a single event. Binding for the tag is then done in the scanModsLibrary function via 'root.bind_class'
		for frame in self.winfo_children():
			frame.bindtags( ('moduleClickTag',) + frame.bindtags() )
			for label in frame.winfo_children():
				label.bindtags( ('moduleClickTag',) + label.bindtags() )

		# Add the edit button
		LabelButton( row3, 'editButton', inspectMod, 'Edit or configure this mod' ).pack( side='right', padx=(5, 55), pady=6 )

		# Validate web page links and create buttons for them
		for origUrlString, comments in webLinks: # Items in this list are tuples of (urlString, comments)
			urlObj = self.parseUrl( origUrlString )
			if not urlObj: continue # A warning will have been given in the above method if this wasn't successfully parsed
			self.webLinks.append( (urlObj, comments) )

			# Build the button's hover text
			domain = urlObj.netloc.split('.')[-2] # The netloc string will be e.g. "youtube.com" or "www.youtube.com"
			url = urlObj.geturl()
			hovertext = 'Go to the {}{} page...\n{}'.format( domain[0].upper(), domain[1:], url ) # Capitalizes first letter of domain
			if comments:
				hovertext += '\n\n' + comments.lstrip( ' #' )

			# Add the button with its url attached
			icon = LabelButton( row3, domain + 'Link', self.openWebPage, hovertext )
			icon.url = url
			icon.pack( side='right', padx=5, pady=6 )

		row3.pack( side='top', fill='x', expand=1 )

	def openWebPage( self, event ):
		page = event.widget.url
		webbrowser.open( page )
		
	def parseUrl( self, origUrlString ):

		""" Validates a given URL (string), partly based on a whitelist of allowed domains. 
			Returns a urlparse object if the url is valid, or None (Python default) if it isn't. """

		try:
			potentialLink = urlparse( origUrlString )
		except Exception as err:
			print 'Invalid link detected for "{}": {}'.format( self.name, err )
			return

		# Check the domain against the whitelist. netloc will be something like "youtube.com" or "www.youtube.com"
		if potentialLink.scheme and potentialLink.netloc.split('.')[-2] in ( 'smashboards', 'github', 'youtube' ):
			return potentialLink

		elif not potentialLink.scheme:
			print 'Invalid link detected for "{}" (no scheme): {}'.format( self.name, potentialLink )
		else:
			print 'Invalid link detected for "{}" (domain not allowed): {}'.format( self.name, potentialLink )

	def setState( self, state, specialStatusText='' ):

		""" Sets the state of the selected module, by adding a label to the module's Row 3 and 
			changing the background color of all associated widgets. """

		stateColor = 'SystemButtonFace' # The default (disabled) colors.
		textColor = '#000'

		if state == 'pendingEnable':
			stateColor = '#aaffaa'
			self.statusText.set( 'Pending Save' )

		elif state == 'pendingDisable':
			stateColor = '#ee9999'
			self.statusText.set( 'Pending Removal' )

		elif state == 'enabled':
			stateColor = '#77cc77'
			self.statusText.set( '' )

		elif state == 'unavailable':
			stateColor = '#cccccc'
			textColor = '#707070'
			if self.type == 'gecko':
				if not gecko.environmentSupported:
					self.statusText.set( '(Gecko codes are unavailable)' )
				elif 'EnableGeckoCodes' in overwriteOptions and not overwriteOptions[ 'EnableGeckoCodes' ].get():
					self.statusText.set( '(Gecko codes are disabled)' )
				else:
					self.statusText.set( '' )
			elif self.data == {}:
				self.statusText.set( 'No code change data found!' )
			else:
				self.statusText.set( '(Unavailable for your DOL revision)' )

		elif state != 'disabled':
			self.statusText.set( '' )
			raise Exception( 'Invalid mod state given! "' + state + '"' )

		if specialStatusText:
			if state == 'unavailable':
				print self.name, 'made unavailable;', specialStatusText
			self.statusText.set( specialStatusText )

		# Change the overall background color of the module (adjusting the background color of all associated frames and labels)
		for i, frame in enumerate( self.winfo_children() ):
			frame['bg'] = stateColor
			for j, label in enumerate( frame.winfo_children() ):
				label['bg'] = stateColor
				if not (i == 2 and j == 0): # This will exclude the status label.
					label['fg'] = textColor

		self.state = state


def getCurrentModsLibraryTab():
	
	""" Returns the currently selected tab in the Mods Library tab. """

	if modsLibraryNotebook.tabs() == (): 
		return 'emptyNotebook'
	else:
		selectedTab = root.nametowidget( modsLibraryNotebook.select() ) # This will be the tab frame.
		childWidget = selectedTab.winfo_children()[0]

		# If the child widget is not a frame, it's a notebook, meaning this represents a directory, and contains more files/tabs within it.
		while childWidget.winfo_class() != 'Frame':
			if childWidget.tabs() == (): return 'emptyNotebook'
			selectedTab = root.nametowidget( childWidget.select() )
			childWidget = selectedTab.winfo_children()[0]
			
		return selectedTab


def getModsLibraryTabs():

	""" Returns a list of all tab widgets within the Mods Library tab (recusively includes sub-tabs). 
		Each Frame widget is parent to a Frame, which in turn contains a scrollingFrame (modsPanel), which may contain mods. """

	modsTabs = []

	def checkTabsInNotebook( notebook ): # Recursive function to check nested child notebooks
		for tabName in notebook.tabs():
			tabWidget = root.nametowidget( tabName ) # This will be the tab's frame widget
			childWidget = tabWidget.winfo_children()[0]

			if childWidget.winfo_class() == 'TNotebook': # If it's actually a tab full of mods (repping a file), the class will be "Frame"
				# Check whether this notebook is empty.
				if childWidget.tabs() == (): continue # Skip this tab
				else: checkTabsInNotebook( childWidget )

			else: # Found a Frame widget, potentially containing mods (could still be empty)
				modsTabs.append( tabWidget )

	checkTabsInNotebook( modsLibraryNotebook )

	return modsTabs


def realignControlPanel():

	""" Updates the alignment/position of the control panel (to the right of mod lists) and the global scroll target. """

	rootFrame.resizeTimer = None

	# Get the VerticalScrolledFrame of the currently selected tab.
	currentTab = getCurrentModsLibraryTab()

	if root.nametowidget( mainNotebook.select() ) == modsLibraryTab and currentTab != 'emptyNotebook':
		frameForBorder = currentTab.winfo_children()[0]
		scrollingFrame = frameForBorder.winfo_children()[0]

		# Get the new coordinates for the control panel frame.
		root.update() # Force the GUI to update in order to get correct new widget positions & sizes.
		root_X_Offset = scrollingFrame.winfo_rootx() - modsLibraryTab.mainRow.winfo_rootx() + scrollingFrame.winfo_width() + 2
		root_Y_Offset = scrollingFrame.winfo_rooty() - modsLibraryTab.mainRow.winfo_rooty()

		controlPanel.place( x=root_X_Offset, y=root_Y_Offset, width=currentTab.winfo_width() * .35 - 2, height=scrollingFrame.winfo_height() )
	else:
		controlPanel.place_forget() # Removes the control panel from GUI, without deleting it


def onTabChange( event ):
	realignControlPanel()
	updateInstalledModsTabLabel()


def updateInstalledModsTabLabel():
	currentTab = getCurrentModsLibraryTab()

	if root.nametowidget( mainNotebook.select() ) == modsLibraryTab and currentTab != 'emptyNotebook':
		frameForBorder = currentTab.winfo_children()[0]
		scrollingFrame = frameForBorder.winfo_children()[0] # i.e. modsPanel

		enabledMods = 0
		scrollingFrameChildren = scrollingFrame.interior.winfo_children()
		for mod in scrollingFrameChildren:
			if mod.state == 'enabled' or mod.state == 'pendingEnable': enabledMods += 1

		installedModsTabLabel.set( 'Enabled on this tab:  ' + str(enabledMods) + ' / ' + str(len( scrollingFrameChildren )) )


def selectModLibraryTab( targetTabWidget ):

	""" Recursively selects all tabs within the Mods Library required to ensure the given target tab is visible. """

	def selectTabInNotebook( notebook ): # Will recursively check child notebooks.
		found = False

		for tabName in notebook.tabs():
			tabWidget = root.nametowidget( tabName ) # This will be the tab's frame widget.

			# Check if this is the target tab, if not, check if the target tab is in a sub-tab of this tab
			if tabWidget == targetTabWidget: found = True
			else:
				childWidget = tabWidget.winfo_children()[0]

				if childWidget.winfo_class() == 'TNotebook': # If it's actually a tab full of mods (repping a file), the class will be "Frame".
					# Check whether this notebook is empty. If not, scan it.
					if childWidget.tabs() == (): continue # Skip this tab.
					else: found = selectTabInNotebook( childWidget )

			if found: # Select the current tab
				notebook.select( tabWidget )
				break

		return found

	return selectTabInNotebook( modsLibraryNotebook )


def findMod( nameFragment, matchOffset=0 ):
	
	""" Gets the tab widget and index/position of a mod among the mods library tabs, by mod name. 
		nameFragment may be just a partial match. matchOffset causes the first n matches to be skipped; 
		positive values denote searching forwards in the library, while negative values search backwards. 
		Returns: tabWidget, targetMod, index """

	tabWidget = None
	targetMod = None
	index = -1
	modsLibraryTabs = getModsLibraryTabs()

	# If searching through the mod library in reverse, simply reverse the tab and mod lists, and normalize the match offset
	if matchOffset < 0:
		modsLibraryTabs.reverse()
		reverseSearch = True
		matchOffset = abs( matchOffset ) - 1 # Normalizing to a positive value, so the following loop works as normal
	else:
		reverseSearch = False

	for tab in modsLibraryTabs:
		childWidget = tab.winfo_children()[0]
		scrollingFrame = childWidget.winfo_children()[0] # i.e. a modsPanel
		mods = scrollingFrame.interior.winfo_children()

		if reverseSearch: mods.reverse()

		# Search for a mod name containing the given string
		for i, mod in enumerate( mods ):
			if nameFragment.lower() in mod.name.lower():
				# Skip this match if we're looking ahead some number of matches
				if matchOffset > 0:
					matchOffset -= 1
					continue

				# Confirm this match
				targetMod = mod
				if not reverseSearch: index = i
				else: index = len( mods ) - i # Counting iterations from the end
				break

		if index != -1:
			tabWidget = tab
			break

	return tabWidget, targetMod, index


def prevModLibraryMatch():
	searchBar = modsLibraryTab.winfo_children()[1] # Second child, since this was created/added second
	searchBar.matchOffset -= 1
	found = searchForMod( None )

	# If not found, try wrapping around
	if not found:
		# Reset the matchOffset and try once more from the end
		searchBar.matchOffset = -1
		searchForMod( None )


def nextModLibraryMatch():
	searchBar = modsLibraryTab.winfo_children()[1] # Second child, since this was created/added second
	searchBar.matchOffset += 1
	found = searchForMod( None )

	# If not found, try wrapping around
	if not found:
		# Reset the matchOffset and try once more from the beginning
		searchBar.matchOffset = 0
		searchForMod( None )


def searchForMod( event ):
	
	""" Used by the GUI's CTRL-F / mod seach box feature. Called on each key-up event from the text entry field, 
		as well as the Prev./Next buttons. """

	searchBar = modsLibraryTab.winfo_children()[1]
	nameFragment = searchBar.winfo_children()[1].get() # Gets text from the Entry widget

	# Reset the match offset if this is a brand new string
	if not searchBar.lastFound in nameFragment:
		searchBar.matchOffset = 0
		searchBar.lastFound = ''

	# Seek out a matching mod, using the current search offset
	found = goToMod( nameFragment, searchBar.matchOffset ) # Returns True/False for whether the mod was found or not

	if found:
		searchBar.lastFound = nameFragment

	return found


def goToMod( modNameText, matchOffset=0 ):

	""" Searches for a mod among the Mods Library tabs, and if found, switches tabs and scrolls to it. 
		A highlight animation is then played on the target mod to indicate it to the user. 
		modNameText may be a full or partial mod name to search for. If matchOffset >= 0, the 
		search function will start from the beginning of the library (leftmost tab, topmost mod). 
		If matchOffset < 0, the search will be reversed, starting from the end of the library. Larger 
		offsets (positive or negative) skips that many mod matches, for next/previous functionality. """

	if not modNameText:
		return False

	tabWidget, targetMod, index = findMod( modNameText, matchOffset )

	if not tabWidget: # No matching mod found
		return False

	# Switch to the tab containing the mod
	selectModLibraryTab( tabWidget )

	# Scroll to the target mod
	modsPanel = tabWidget.winfo_children()[0].winfo_children()[0] # tab -> frameForBorder -> modsPanel (VerticalScrolledFrame)
	modsPanel.update_idletasks()
	yOffset = targetMod.winfo_y() # Relative to the mod's parent, the modsPanel's ".interior" frame
	if index != 0: yOffset -= 90 # For aesthetics (centers the mod slightly)
	relativeScrollbarOffset = yOffset / float(  modsPanel.interior.winfo_height() )
	modsPanel.canvas.yview_moveto( relativeScrollbarOffset ) # sliderYPos

	# Highlight the mod
	targetMod['background'] = 'yellow'

	# Stop the fade animation if it's already in-progress
	if targetMod.highlightFadeAnimationId:
		targetMod.after_cancel( targetMod.highlightFadeAnimationId )

	# Start a new fade animation on this mod
	targetMod.highlightFadeAnimationId = targetMod.after( 1500, lambda mod=targetMod: updateHighlightAnimation(mod) )

	return True


def updateHighlightAnimation1( modModule ): # Depricate in favor of the polynomial function?

	""" Fades a color into another color by reducing each of its RGB color channels by an amount proportional to its initial value.
		Each channel is reduced by 1 / [stepSize] of its original starting value, thus all values will reach their respective target values at the same time. 
		
			i.e. 	Example starting color of 20, 40, 40 (RGB), with 5 steps.
					Step size will then be 4, 8, 8 for the respective channels.
				Step 0:		Step 1:		Step 2:		etc...
					R: 20		R: 16		R: 12
					G: 40		G: 32		G: 24
					B: 40		B: 32		B: 24
	"""
	# tic=time.clock()

	steps = 5.0 # This will shift each color channel by 1 / x, for the current iteration (therefore this exponentially decreases)

	# Convert the current color (a name or hex string) to an RGB tuple
	encodedCurrentColor = modModule['background']
	#print 'updating highlight for "' + modModule.name + '".', 'current color:', encodedCurrentColor
	if not encodedCurrentColor.startswith( '#' ): 
		currentColor = name2rgb( encodedCurrentColor )
	else: 
		currentColor = hex2rgb( encodedCurrentColor )

	targetColor = name2rgb( 'SystemButtonFace' )

	#print 'current color RGB:', currentColor, '  target color RGB:', targetColor

	step_R = ( targetColor[0] - currentColor[0] ) / steps
	step_G = ( targetColor[1] - currentColor[1] ) / steps
	step_B = ( targetColor[2] - currentColor[2] ) / steps

	#print 'step sizes:', step_R, step_G, step_B

	# Check if all color channels are similar
	colorsCloseInColor = True
	newChannelValues = []
	for i, colorStep in enumerate( (step_R, step_G, step_B) ):
		#if (colorStep <= 0 and colorStep > -3) or (colorStep >= 0 and colorStep < 3):
		#print 'iteration', i, ':', abs( targetColor[i] - currentColor[i] )
		if abs( targetColor[i] - currentColor[i] ) < steps:
			# These color channels are close
			newChannelValues.append( targetColor[i] )
			#continue
		else:
			colorsCloseInColor = False
			newChannelValues.append( int(round( currentColor[i] + colorStep )) )
			#break

	if colorsCloseInColor:
		modModule['background'] = 'SystemButtonFace'
		modModule.highlightFadeAnimationId = None
	else:
		# One of the color channels didn't match above (it's too different between "from" and "to" colors)
		# newR = int(round( currentColor[0] + step_R ))
		# newG = int(round( currentColor[1] + step_G ))
		# newB = int(round( currentColor[2] + step_B ))
		#modModule['background'] = rgb2hex( (currentColor[0] + step_R, currentColor[1] + step_G, currentColor[2] + step_B) )
		#modModule['background'] = rgb2hex( (newR, newG, newB) )
		modModule['background'] = rgb2hex( newChannelValues )
		modModule.highlightFadeAnimationId = modModule.after( 170, lambda mod=modModule: updateHighlightAnimation(mod) )
		# toc=time.clock()
		# print 'time to update color (method 1):', toc-tic


def updateHighlightAnimation( modModule, x=2 ):
	
	""" Fades a color into another using a polynomial function. Each channel of the color is gradually changed
		by a percentage of its initial value, so each color follow the same rate of change. """

	# tic=time.clock()

	initialColor = getattr( modModule, 'initColor', None )
	if not initialColor:
		# Convert the current color (a name or hex string) to an RGB tuple
		encodedCurrentColor = modModule['background'] # May be a hex string or text color string
		if encodedCurrentColor.startswith( '#' ):
			initialColor = modModule.initColor = hex2rgb( encodedCurrentColor ) # It's a hex string like "#rrggbb"
		else:
			initialColor = modModule.initColor = name2rgb( encodedCurrentColor ) # A color name string like "blue"

	targetColor = name2rgb( 'SystemButtonFace' )

	# Determine the difference between the original color and the target color (i.e. the range of change), for each color channel
	diff_R = targetColor[0] - initialColor[0]
	diff_G = targetColor[1] - initialColor[1]
	diff_B = targetColor[2] - initialColor[2]

	#print 'diffs:', diff_R, diff_G, diff_B

	# Determine the percentage/progress to apply to the range of color (this formula plots a nice curve that starts fast, but then slows exponentially)
	percentChange = ( -0.0123*x**4 + 0.4865*x**3 - 7.3018*x**2 + 50.747*x - 43.45 ) / 100
	#print 'percentage of diffs:', diff_R * percentChange, diff_G * percentChange, diff_B * percentChange

	# Determine what to change each color channel to (its initial color plus a percentage of the range of change)
	new_R = int(round( initialColor[0] + (diff_R * percentChange) ))
	new_G = int(round( initialColor[1] + (diff_G * percentChange) ))
	new_B = int(round( initialColor[2] + (diff_B * percentChange) ))

	#print 'percent change:', percentChange, '   new color channel values:', ( new_R, new_G, new_B )

	# End after 13 iterations (this is just before the peak of the polynomial plot above)
	if x == 13:
		modModule['background'] = 'SystemButtonFace'
		modModule.highlightFadeAnimationId = None
	else:
		x += 1
		modModule['background'] = rgb2hex( ( new_R, new_G, new_B ) )
		modModule.highlightFadeAnimationId = modModule.after( 170, lambda mod=modModule, iteration=x: updateHighlightAnimation(mod, iteration) )
		# toc=time.clock()
		# print 'time to update color:', toc-tic


def enterSearchMode( event=None ):
	
	""" Called by the CTRL-F keyboard shortcut; adds a search bar to the GUI so a user may search for mods by name. """

	# This function may be called from tabs other than the Mod Library tab. So switch to it if we're not there.
	currentTab = root.nametowidget( mainNotebook.select() )
	if currentTab != modsLibraryTab: mainNotebook.select( modsLibraryTab )

	modsLibraryTabRows = modsLibraryTab.winfo_children()

	if len( modsLibraryTabRows ) == 1: # No search bar has been added yet.
		paddingY = ( 20, 0 ) # First value = above bar, second value = below bar
		searchBar = ttk.Frame( modsLibraryTab, padding=paddingY, height=0 )
		searchBar.pack_propagate( False ) # So that the children will not determine/force the widget's size.
		ttk.Label( searchBar, image=imageBank['searchIcon'] ).pack( side='left', padx=(11, 10) ) #, text='Search:'
		entry = ttk.Entry( searchBar )
		entry.pack( side='left', fill='x', expand=True, pady=(1,0) )
		closeButton = ttk.Button( searchBar, text='X', width=2, command=lambda: exitSearchMode(None) )
		closeButton.pack( side='right', padx=(37, 15), ipadx=3 )
		ttk.Button( searchBar, text='Next', width=5, command=nextModLibraryMatch ).pack( side='right', padx=(4, 15), ipadx=3 )
		ttk.Button( searchBar, text='Prev.', width=5, command=prevModLibraryMatch ).pack( side='right', padx=(15, 4), ipadx=3 )
		searchBar.pack( side='top', fill='x' )
		searchBar.matchOffset = 0
		searchBar.lastFound = ''
		searchBar.update_idletasks()
		requestedHeight = closeButton.winfo_reqheight() + paddingY[0] + paddingY[1] # Asking the tallest widget in the bar

		# Open the search bar with an animation
		try:
			totalSteps = 3
			stepSize = requestedHeight / totalSteps
			searchBarHeight = 0
			while searchBarHeight < requestedHeight:
				searchBarHeight += stepSize
				searchBar.configure( height=searchBarHeight )
				realignControlPanel()
		except:
			pass

	else: # Seems there's already a search bar available
		# Get the entry widget (iterates over the search bar's widgets)
		potentialSearchBar = modsLibraryTabRows[1]
		searchBar = potentialSearchBar
		entry = None
		if not getattr( potentialSearchBar, 'matchOffset', None ) == None:
			for widget in potentialSearchBar.winfo_children():
				if widget.winfo_class() == 'TEntry':
					entry = widget
					break

	# Move keyboard focus to the entry widget, and bind the event handler
	if entry: # Failsafe; should be found in all cases
		entry.focus()
		entry.bind( '<KeyRelease>', searchForMod )


def exitSearchMode( event ):
	
	""" Triggered by pressing ESC or the 'X' button in the search bar, which then closes and removes the search bar. """

	modsLibraryTabRows = modsLibraryTab.winfo_children()

	if len( modsLibraryTabRows ) > 1: # The search bar is present
		root.update_idletasks() # Make sure the dimentions that will be reported below are correct
		searchBar = modsLibraryTabRows[1] # Children are in order that they were attached to parent.
		searchBar.winfo_children()[1].unbind( '<KeyRelease>' ) # Unbinded (even though the widget is deleted soon) to prevent this from queuing
		searchBarHeight = searchBar.winfo_height()

		# Close the search bar with an animation
		try:
			totalSteps = 3
			stepSize = searchBarHeight / totalSteps
			while searchBarHeight > 0:
				searchBarHeight -= stepSize
				searchBar.configure( height=searchBarHeight )
				searchBar.update_idletasks()
				realignControlPanel()
		except: pass

		searchBar.destroy()
		realignControlPanel()


class ModsLibrarySelector( basicWindow ):

	""" Presents a non-modal pop-up window where the user can select a directory to load mods from. """

	def __init__( self, rootWindow ):
		basicWindow.__init__( self, rootWindow, 'Mods Library Selection', offsets=(160, 100) )
		
		pathsList = getModsFolderPath( getAll=True )
		pathIndex = int( settings.get('General Settings', 'modsFolderIndex') )
		if pathIndex >= len( pathsList ): pathIndex = 0 # Failsafe/default
		self.pathIndexVar = IntVar( value=pathIndex )
		self.initialLibraryPath = ''

		# Add Radio buttons for each library path option
		self.pathsFrame = ttk.Frame( self.window )
		for i, path in enumerate( pathsList ):
			self.addLibraryOption( i, path )
			if i == pathIndex:
				self.initialLibraryPath = path
		self.pathsFrame.pack( padx=20, pady=(20, 10), expand=True, fill='x' )

		ttk.Button( self.window, text='Add Another Library Path', command=self.addPath ).pack( pady=5, ipadx=10 )

		buttonsFrame = ttk.Frame( self.window )
		self.okButton = ttk.Button( buttonsFrame, text='Ok', command=self.submit )
		self.okButton.pack( side='left', padx=10 )
		ttk.Button( buttonsFrame, text='Cancel', command=self.cancel ).pack( side='left', padx=10 )
		buttonsFrame.pack( pady=10 )

		# Done creating window. Pause execution of the calling function until this window is closed.
		rootWindow.wait_window( self.window ) # Pauses execution of the calling function until this window is closed.

	def addLibraryOption( self, buttonIndex, path ):

		""" Adds a library option (radio button and label) to the GUI. """

		path = os.path.normpath( path ).replace( '"', '' )
		emptyWidget = Frame( self.window, relief='flat' ) # This is used as a simple workaround for the labelframe, so we can have no text label with no label gap.
		optionFrame = ttk.Labelframe( self.pathsFrame, labelwidget=emptyWidget, padding=(20, 4) )

		# Disable the radiobutton if the path is invalid
		if os.path.exists( path ): state = 'normal'
		else: state = 'disabled'

		radioBtn = ttk.Radiobutton( optionFrame, text=os.path.basename(path), variable=self.pathIndexVar, value=buttonIndex, state=state )
		radioBtn.pack( side='left', padx=(0, 100) )
		removeBtn = ttk.Button( optionFrame, text='-', width=3, command=lambda w=optionFrame: self.removePath(w), style='red.TButton' )
		ToolTip( removeBtn, text='Remove library', delay=1000, bg='#ee9999' )
		removeBtn.pack( side='right' )

		optionFrame.path = path
		optionFrame.pack( expand=True, fill='x' )
		ToolTip( optionFrame, text=path, wraplength=600, delay=1000 )

	def addPath( self ):

		""" Prompts the user for a mod library directory, and adds it to the GUI. """

		# Prompt for a directory to load for the Mods Library.
		newSelection = tkFileDialog.askdirectory(
			parent=self.window,
			title=( 'Choose a folder from which to load your Mods Library.\n\n'
					'All mods you intend to save should be in the same library.' ),
			initialdir=settings.get( 'General Settings', 'defaultSearchDirectory' ),
			mustexist=True )

		if newSelection: # Could be an empty string if the user canceled the operation
			# Make sure this path isn't already loaded
			frameChildren = self.pathsFrame.winfo_children()
			for option in frameChildren:
				if option.path == os.path.normpath( newSelection ):
					return

			self.addLibraryOption( len(frameChildren), newSelection )

			# Select this library
			self.pathIndexVar.set( len(frameChildren) )

	def removePath( self, optionFrameToRemove ):

		""" Removes a library option from the GUI and updates the index values of the remaining radio buttons. """

		selectedIndex = self.pathIndexVar.get()
		passedButtonToRemove = False

		# If this library button was selected, reset the current selection (default to the first library)
		for optionFrame in self.pathsFrame.winfo_children():
			radioBtn = optionFrame.winfo_children()[0]
			btnIndex = radioBtn['value']

			if optionFrame == optionFrameToRemove:
				if btnIndex == selectedIndex:
					self.pathIndexVar.set( 0 )
				elif selectedIndex > btnIndex:
					self.pathIndexVar.set( selectedIndex - 1 ) # Decrement the selected index by 1, since there is one less library

				passedButtonToRemove = True
				continue

			# Update the radio button value for all buttons beyond the one being removed
			if passedButtonToRemove:
				radioBtn['value'] = btnIndex - 1
		
		optionFrameToRemove.destroy() # Should also destroys its children, including the radio button

	def submit( self ):
		# Validate the current selection
		index = self.pathIndexVar.get()
		if index >= len( self.pathsFrame.winfo_children() ):
			msg( 'Invalid Mods Library Selection!' )
			return

		# Collect the paths and combine them into one string
		libraryPaths = []
		for option in self.pathsFrame.winfo_children():
			libraryPaths.append( option.path )
		pathsString = '"' + '","'.join( libraryPaths ) + '"'
		
		# Save the new path(s) to the settings file
		settings.set( 'General Settings', 'modsFolderPath', pathsString )
		settings.set( 'General Settings', 'modsFolderIndex', str(index) )
		saveOptions()

		# Set the mod library selector button hover text, and close this window
		currentLibraryPath = getModsFolderPath()
		librarySelectionLabel.hoverText.set( 'Select Mods Library.\tCurrent library:\n' + currentLibraryPath )
		self.window.destroy()

		# Reload the Mods Library if a different one was selected
		if currentLibraryPath != self.initialLibraryPath:
			scanModsLibrary()

	def cancel( self, event='' ):
		self.window.destroy()
																			 #============================#
																			# ~ ~ Mod Construction tab ~ ~ #
																			 #============================#

def inspectMod( event, mod=None ):

	""" Load a mod from the Mods Library tab into the Mod Construction tab. """

	if not mod: # Was called by the button. Get the mod from the event object
		mod = event.widget.master.master

	# Select the Mod Construction tab and get the currently existing tabs
	mainNotebook.select( constructionTab )

	# Check if the selected mod already exists (and select that if it does)
	for tab in constructionNotebook.tabs():
		tabName = constructionNotebook.tab( tab, 'text' )
		if tabName != mod.name: continue

		tabWidget = root.nametowidget( tab )
		existingModConstructor = tabWidget.winfo_children()[0]

		if existingModConstructor.sourceFile == mod.sourceFile: # Make sure the library wasn't changed (and it's not just a mod by the same name)
			constructionNotebook.select( tab )
			break

	else: # Loop above didn't break; mod not found
		# Create a new tab for the Mod Construction tab, and create a new construction module within it.
		newTab = ttk.Frame( constructionNotebook )
		constructionNotebook.add( newTab, text=mod.name )
		ModConstructor( newTab, mod ).pack( fill='both', expand=1 )

		# Bring the new tab into view for the user.
		constructionNotebook.select( newTab )


class ModConstructor( Frame ):

	def __init__( self, parent, mod=None, *args, **kw ): # Prepare the GUI.
		Frame.__init__( self, parent, *args, **kw )
		
		self.saveStatus = StringVar()
		self.saveStatus.set( '' )
		self.dolVariations = []
		self.undoableChanges = False 		# Flipped for changes that 'undo' doesn't work on. Only reverted by save operation.
		self.gameVersionsNotebook = None

		if mod: # This mod is being added (edited) from the Mods Library tab.
			name = mod.name
			auth = mod.auth
			self.type = mod.type
			modDescription = mod.desc
			self.sourceFile = mod.sourceFile
			self.fileIndex = mod.fileIndex
			self.webLinks = mod.webLinks
			self.includePaths = mod.includePaths

		else: # This is a new mod.
			name = ''
			auth = ''
			self.type = ''
			modDescription = ''
			self.sourceFile = ''
			self.fileIndex = -1
			self.webLinks = []
			self.includePaths = [ os.path.join(getModsFolderPath(), '.include'), os.path.join(scriptHomeFolder, '.include') ]

		# Top buttons row
		self.buttonsFrame = Frame( self )
		self.saveStatusLabel = Label( self.buttonsFrame, textvariable=self.saveStatus )
		self.saveStatusLabel.pack( side='left', padx=12 )
		ttk.Button( self.buttonsFrame, text='Close', command=self.closeMod, width=6 ).pack( side='right', padx=6 )
		ttk.Button( self.buttonsFrame, text='Info', command=self.analyzeMod, width=6 ).pack( side='right', padx=6 )
		ttk.Button( self.buttonsFrame, text='Import Gecko Code', command=self.importGeckoCode ).pack( side='right', padx=6, ipadx=6 )
		self.buttonsFrame.pack( fill='x', expand=0, padx=20, pady=12, ipadx=6, anchor='ne' )

		# Title and Author
		row1 = Frame( self )
		Label( row1, text='Title:' ).pack( side='left', padx=3 )
		self.titleEntry = ttk.Entry( row1, width=56 )
		self.titleEntry.insert( 0, name )
		self.titleEntry.pack( side='left' )
		self.initUndoHistory( self.titleEntry, name )
		Label( row1, text='Author(s):' ).pack( side='left', padx=(22, 3) )
		self.authorsEntry = ttk.Entry( row1, width=36 )
		self.authorsEntry.insert( 0, auth )
		self.authorsEntry.pack( side='left' )
		self.initUndoHistory( self.authorsEntry, auth )
		row1.pack( padx=20, pady=0, anchor='n' )

		# Starting row 2, with Description
		row2 = Frame( self )
		descColumn = Frame( row2 ) # Extra frame so we can stack two items vertically in this grid cell in a unique way
		Label( descColumn, text='\t\tDescription:' ).pack( anchor='w' )
		self.descScrolledText = ScrolledText( descColumn, width=75, height=6, wrap='word', font='TkTextFont' )
		self.descScrolledText.insert( 'end', modDescription )
		self.descScrolledText.pack( fill='x', expand=True ) # todo: still not actually expanding. even removing width above doesn't help
		self.initUndoHistory( self.descScrolledText, modDescription )
		descColumn.grid( column=0, row=0 )

		# Add the mod-change adder
		lineAdders = ttk.Labelframe(row2, text='  Add a type of code change:  ', padding=5)
		ttk.Button( lineAdders, width=3, text='+', command=lambda: self.addCodeChangeModule( 'static' ) ).grid( row=0, column=0 )
		Label( lineAdders, width=21, text='Static Overwrite' ).grid( row=0, column=1 )
		ttk.Button( lineAdders, width=3, text='+', command=lambda: self.addCodeChangeModule( 'injection' ) ).grid( row=1, column=0 )
		Label( lineAdders, width=21, text='Injection Mod' ).grid( row=1, column=1 )
		ttk.Button(lineAdders, width=3, text='+', command=lambda: self.addCodeChangeModule( 'gecko' )).grid(row=2, column=0)
		Label(lineAdders, width=21, text='Gecko/WiiRD Code').grid(row=2, column=1)
		ttk.Button( lineAdders, width=3, text='+', command=lambda: self.addCodeChangeModule( 'standalone' ) ).grid( row=3, column=0 )
		Label( lineAdders, width=21, text='Standalone Function' ).grid( row=3, column=1 )
		lineAdders.grid( column=1, row=0 )

		# Add the web links
		if self.webLinks:
			self.webLinksFrame = ttk.Labelframe( row2, text='  Web Links:  ', padding=(0, 0, 0, 8) ) # padding = left, top, right, bottom
			for urlObj, comments in self.webLinks:
				self.addWebLink( urlObj, comments )

			# Add the "Edit" button
			# addBtn = ttk.Label( row2, text='Edit', foreground='#03f', cursor='hand2' )
			# addBtn.bind( '<1>', lambda e, frame=self.webLinksFrame: WebLinksEditor(frame) )
			# addBtn.place( anchor='s', relx=.937, rely=1.0, y=4 )

			self.webLinksFrame.grid( column=2, row=0 )

		row2.pack( fill='x', expand=True, padx=20, pady=(7, 0), anchor='n' )
		
		# Configure the description/code-changes row, so it centers itself and expands properly on window-resize
		row2.columnconfigure( 0, weight=3 )
		row2.columnconfigure( (1, 2), weight=1 )

		# Add the game version tabs and code changes to this module.
		if mod:
			for dolRevision in mod.data: # dolRevision should be a string like 'NTSC 1.00'
				for codeChange in mod.data[dolRevision]:
					changeType, customCodeLength, offset, originalCode, customCode, _ = codeChange

					self.addCodeChangeModule( changeType, customCodeLength, offset, originalCode, customCode, dolRevision )

	def initUndoHistory( self, widget, initialValue ):

		""" Adds several attributes and event handlers to the given widget, for undo/redo history tracking. """

		widget.undoStateTimer = None
		
		# Create the first undo state for this widget
		widget.undoStates = [initialValue]
		widget.savedContents = initialValue
		widget.undoStatesPosition = 0 # Index into the above list, for traversal of multiple undos/redos

		# Provide this widget with event handlers for CTRL-Z, CTRL-Y
		widget.bind( "<Control-z>", self.undo )
		widget.bind( "<Control-y>", self.redo )
		widget.bind( "<Control-Shift-y>", self.redo )

		widget.bind( '<KeyRelease>', self.queueUndoStatesUpdate )

	def initializeVersionNotebook( self ):
		
		""" Creates the notebook used to house code changes, with tabs for each game revision the mod may apply to. """

		def gotoWorkshop(): webbrowser.open( 'http://smashboards.com/forums/melee-workshop.271/' )
		def shareButtonClicked():
			modString = self.buildModString()
			thisModName = constructionNotebook.tab( self.master, option='text' )
			if modString != '': cmsg( '\n\n\t-==-\n\n' + modString, thisModName, 'left', (('Go to Melee Workshop', gotoWorkshop),) )

		# Show the Share / Submit buttons
		ttk.Button( self.buttonsFrame, text='Share', command=shareButtonClicked, width=7 ).pack( side='right', padx=6 )
		ttk.Button( self.buttonsFrame, text='Save As', command=self.saveModToLibraryAs, width=8 ).pack( side='right', padx=6 )
		ttk.Button( self.buttonsFrame, text='Save', command=self.saveModToLibrary, width=7 ).pack( side='right', padx=6 )
		offsetView = settings.get( 'General Settings', 'offsetView' ).lstrip()[0].lower()
		if offsetView.startswith( 'd' ): buttonText = 'Display RAM Addresses'
		else: buttonText = 'Display DOL Offsets'
		self.offsetViewBtn = ttk.Button( self.buttonsFrame, text=buttonText, command=self.switchOffsetDisplayType )
		self.offsetViewBtn.pack( side='right', padx=6, ipadx=6 )

		self.gameVersionsNotebook = ttk.Notebook( self )
		self.gameVersionsNotebook.pack( fill='both', expand=1, anchor='n', padx=12, pady=6 )

		# New hex field label
		self.gameVersionsNotebook.newHexLabel = StringVar()
		self.gameVersionsNotebook.newHexLabel.set( '' )
		Label( self.gameVersionsNotebook, textvariable=self.gameVersionsNotebook.newHexLabel ).place( anchor='e', y=9, relx=.84 )

		# Add the version adder tab.
		versionChangerTab = Frame( self.gameVersionsNotebook )
		self.gameVersionsNotebook.add( versionChangerTab, text=' + ' )

		# Check what original DOLs are available (in the "Original DOLs" folder)
		self.dolVariations = listValidOriginalDols()
		self.dolVariations.append( 'ALL' )

		if len( self.dolVariations ) == 1: # Only 'ALL' is present
			Label( versionChangerTab, text='No DOLs were found in the "Original DOLs" folder.\nRead the "ReadMe.txt" file found there for more information.' ).pack( pady=15, anchor='center' )

		else: # i.e. Some [appropriately named] dols were found in the dols folder
			Label( versionChangerTab, text='Choose the game revision you would like to add changes for:\n(These are based on what you have in the "Original DOLs" folder.)' ).pack( pady=15, anchor='center' )
			verChooser = StringVar()
			verChooser.set( self.dolVariations[0] )

			ttk.OptionMenu( versionChangerTab, verChooser, self.dolVariations[0], *self.dolVariations ).pack()

			def addAnotherVersion():
				tabName = 'For ' + verChooser.get()

				if getTabByName( self.gameVersionsNotebook, tabName ) == -1: # Tab not found.
					self.addGameVersionTab( verChooser.get(), True )

					# Select the newly created tab.
					self.gameVersionsNotebook.select( root.nametowidget(getTabByName( self.gameVersionsNotebook, tabName )) )
				else: msg( 'A tab for that game revision already exists.' )

			ttk.Button( versionChangerTab, text=' Add ', command=addAnotherVersion ).pack( pady=15 )

	def addGameVersionTab( self, dolRevision, codeChangesListWillBeEmpty ):
		# If this is the first code change, add the game version notebook.
		if not self.gameVersionsNotebook: self.initializeVersionNotebook()

		# Decide on a default revision if one is not set, and determine the game version tab name
		if not dolRevision:
			# This is an empty/new code change being added by the user. Determine a default tab (revision) to add it to.
			if len( self.gameVersionsNotebook.tabs() ) == 1: # i.e. only the version adder tab (' + ') exists; no code changes have been added to this notebook yet
				# Attempt to use the revision of the currently loaded DOL
				if dol.revision in self.dolVariations:
					gameVersionTabName = 'For ' + dol.revision

				else:
					# Attempt to use a default set in the settingsFile, or 'NTSC 1.02' if one is not set there.
					defaultRev = getattr( settingsFile, 'defaultRevision', 'NTSC 1.02' ) # Last arg = default in case defaultRevision doesn't exist (old settings file)

					if defaultRev in self.dolVariations:
						gameVersionTabName = 'For ' + defaultRev

					else: gameVersionTabName = 'For ' + self.dolVariations[0]

			else: # A tab for code changes already exists. Check the name of the currently selected tab and add to that.
				gameVersionTabName = self.gameVersionsNotebook.tab( self.gameVersionsNotebook.select(), "text" )

			dolRevision = gameVersionTabName[4:] # Removes 'For '

		else: # This code change is being populated automatically (opened from the Library tab for editing)
			gameVersionTabName = 'For ' + dolRevision

		# Add a new tab for this game version if not already present, and define its GUI parts to attach code change modules to.
		versionTab = getTabByName( self.gameVersionsNotebook, gameVersionTabName )

		if versionTab != -1: # Found an existing tab by that name. Add this code change to that tab
			codeChangesListFrame = versionTab.winfo_children()[0]

		else: # Create a new version tab, and add this code change to that
			versionTab = Frame( self.gameVersionsNotebook )
			indexJustBeforeLast = len( self.gameVersionsNotebook.tabs() ) - 1
			self.gameVersionsNotebook.insert( indexJustBeforeLast, versionTab, text=gameVersionTabName )
			
			# Attempt to move focus to the tab for the currently loaded DOL revision, or to this tab if that doesn't exist.
			tabForCurrentlyLoadedDolRevision = 'For ' + dol.revision
			if dol.revision and tabForCurrentlyLoadedDolRevision in getTabNames( self.gameVersionsNotebook ):
				self.gameVersionsNotebook.select( getTabByName(self.gameVersionsNotebook, tabForCurrentlyLoadedDolRevision) )
			else: self.gameVersionsNotebook.select( versionTab )

			# Add the left-hand column for the code changes
			codeChangesListFrame = VerticalScrolledFrame2( versionTab )
			codeChangesListFrame.pack( side='left', fill='both', expand=0, padx=3, pady=4 )

			# Add the right-hand column, the new hex field (shared for all code changes)
			newHexFieldContainer = Frame( versionTab )
			newHexFieldContainer['bg'] = 'orange'
			self.attachEmptyNewHexField( versionTab, codeChangesListWillBeEmpty )
			newHexFieldContainer.pack( side='left', fill='both', expand=1, padx=0 )

			# Load a dol for this game version, for the offset conversion function to reference max offsets/addresses, and for dol section info
			loadVanillaDol( dolRevision ) # Won't be repeatedly loaded; stored in memory once loaded for the first time

		return dolRevision, versionTab

	def attachEmptyNewHexField( self, versionTab, codeChangesListWillBeEmpty ):
		codeChangesListFrame, newHexFieldContainer = versionTab.winfo_children()

		self.clearNewHexFieldContainer( newHexFieldContainer )

		newHexField = ScrolledText( newHexFieldContainer, relief='ridge' )
		if codeChangesListWillBeEmpty:
			newHexField.insert( 'end', '\n\tStart by selecting a\n\t     change to add above ^.' )
		else:
			newHexField.insert( 'end', '\n\t<- You may select a code change\n\t     on the left, or add another\n\t       change from the list above ^.' )
		newHexField.pack( fill='both', expand=1, padx=2, pady=1 )

		# Add an event handler for the newHexField. When the user clicks on it, this will autoselect the first code change module if there is only one and it's unselected
		def removeHelpText( event, codeChangesListFrame ):
			#event.widget.unbind( '<1>' ) # Remove this event handler
			codeChangeModules = codeChangesListFrame.interior.winfo_children()

			# Check if there's only one code change module and it hasn't been selected
			if len( codeChangeModules ) == 1 and codeChangeModules[0]['bg'] == 'SystemButtonFace':
				innerFrame = codeChangeModules[0].winfo_children()[0]
				innerFrame.event_generate( '<1>' ) # simulates a click event on the module in order to select it
		newHexField.bind( '<1>', lambda e: removeHelpText( e, codeChangesListFrame ) )

	def addCodeChangeModule( self, changeType, customCodeLength=0, offset='', originalHex='', newHex='', dolRevision='' ):
		if not dolRevision: # This is a brand new (blank) code change being added.
			self.undoableChanges = True
			self.updateSaveStatus( True )

		# Create a new notebook for game versions, and/or a tab for this specific revision, if needed.
		dolRevision, versionTab = self.addGameVersionTab( dolRevision, False )
		codeChangesListFrame, newHexFieldContainer = versionTab.winfo_children()

		# Create the GUI's frame which will hold/show this code change
		codeChangeModule = Frame( codeChangesListFrame.interior, relief='ridge', borderwidth=3 )
		codeChangeModule.pack( fill='both', expand=1, padx=0, pady=0 )
		codeChangeModule['bg'] = 'SystemButtonFace'

		# Process the offset value, based on the type of code change and current File/RAM offset display mode
		processedOffset = offset.replace('<', '').replace('>', '') # Angle bracket removal for function names.
		if ( changeType == 'static' or changeType == 'injection' ) and processedOffset:
			vanillaDol = loadVanillaDol( dolRevision, False ) # This will report any errors it has

			if not validHex( processedOffset.replace( '0x', '' ) ):
				msg( 'Warning! Invalid hex was detected in the offset value, "' + offset + '".' )

			elif vanillaDol: # Applicable offset for further processing, and Original DOL reference successfully loaded
				# Convert the offset value based on the current offset view mode (to display offsets as DOL Offsets or RAM Addresses)
				offsetView = settings.get( 'General Settings', 'offsetView' ).lstrip()[0].lower()
				if offsetView.startswith( 'd' ): # d for 'dolOffset'; indicates that the value should be shown as a DOL Offset
					computedOffset = normalizeDolOffset( processedOffset, dolObj=vanillaDol, returnType='string' ) # Converts to a DOL Offset
				else: # The value should be shown as a RAM address
					computedOffset = normalizeRamAddress( processedOffset, dolObj=vanillaDol, returnType='string' )

				# If there was an error processing the offset, preserve the original value
				if computedOffset != -1: # Error output of normalization functions above should be an int regardless of returnType
					processedOffset = computedOffset

		# Add the passed arguments as properties for this code change [frame] object.
		codeChangeModule.changeType = changeType
		codeChangeModule.newHexLabelText = ''
		codeChangeModule.customCodeLength = StringVar()
		codeChangeModule.customCodeLength.set( '(' + uHex(customCodeLength) + ' bytes)' )

		# Begin creating the inner part of the module.
		innerFrame = Frame( codeChangeModule ) # Used to create a thicker, orange border.
		innerFrame.pack( fill='both', expand=0, padx=2, pady=1 )

		# Top row; Change type, custom code length, and remove button
		topRow = Frame( innerFrame )
		topRow.pack( fill='x', padx=6, pady=4 )
		Label( topRow, text='Type:' ).pack( side='left' )
		Label( topRow, text=presentableModType( changeType, changeType=True ), foreground='#03f' ).pack( side='left' )
		ttk.Button( topRow, text='Remove', command=lambda: self.removeCodeChange(codeChangeModule) ).pack( side='right' )
		updateBtn = ttk.Button( topRow, image=imageBank['updateArrow'], command=lambda: self.updateModule( codeChangesListFrame.master, codeChangeModule, userActivated=True ) )
		updateBtn.pack( side='right', padx=12 )
		ToolTip( updateBtn, 'Use this button to update the byte count of custom code, or, once an offset is given, use it to look up and set the original '
							'hex value. For static overwrites, both an offset and custom code must be provided to get the original hex value '
							'(so that it can be determined how many bytes to look up, since static overwrites can be any length).', delay=1000, wraplength=400, follow_mouse=1 )
		Label( topRow, textvariable=codeChangeModule.customCodeLength ).pack( side='left', padx=5 )

		# Bottom row; offset and orig hex / injection site / function name
		bottomRow = Frame( innerFrame )

		# The offset
		if changeType == 'static' or changeType == 'injection':
			Label( bottomRow, text='Offset:' ).pack( side='left', padx=7 )
			codeChangeModule.offset = ttk.Entry( bottomRow, width=11 )
			codeChangeModule.offset.insert( 0, processedOffset )
			codeChangeModule.offset.pack( side='left', padx=7 )
			self.initUndoHistory( codeChangeModule.offset, processedOffset )
			codeChangeModule.offset.offsetEntry = True # Flag used in undo history feature

		# The original hex, injection site, and function name fields (also labels for the shared new hex field)
		if changeType == 'static':
			Label( bottomRow, text='Original Hex:' ).pack( side='left', padx=7 )
			codeChangeModule.originalHex = ttk.Entry( bottomRow, width=11 )
			codeChangeModule.originalHex.insert( 0, originalHex )
			codeChangeModule.originalHex.pack( side='left', padx=7, fill='x', expand=1 )
			self.initUndoHistory( codeChangeModule.originalHex, originalHex )

			codeChangeModule.newHexLabelText = 'New Hex:'

		elif changeType == 'injection':
			Label( bottomRow, text='Original Hex at\nInjection Site:' ).pack( side='left', padx=7 )
			codeChangeModule.originalHex = ttk.Entry( bottomRow, width=11 )
			codeChangeModule.originalHex.insert( 0, originalHex )
			codeChangeModule.originalHex.pack( side='left', padx=7 )
			self.initUndoHistory( codeChangeModule.originalHex, originalHex )

			codeChangeModule.newHexLabelText = 'Injection Code:'

		elif changeType == 'standalone':
			Label( bottomRow, text='Function Name:' ).pack( side='left', padx=7 )
			codeChangeModule.offset = ttk.Entry( bottomRow )
			codeChangeModule.offset.insert( 0, processedOffset )
			codeChangeModule.offset.pack( side='left', fill='x', expand=1, padx=7 )
			self.initUndoHistory( codeChangeModule.offset, processedOffset )

			codeChangeModule.newHexLabelText = 'Function Code:'

		elif changeType == 'gecko':
			codeChangeModule.newHexLabelText = 'Gecko Code:'

		bottomRow.pack( fill='x', expand=1, pady=4 )

		# Attach a newHex entry field (this will be attached to the GUI on the fly when a module is selected)
		newHexValue = newHex.replace( '|S|', '' )
		codeChangeModule.newHexField = ScrolledText( newHexFieldContainer, relief='ridge' )
		codeChangeModule.newHexField.insert( 'end', newHexValue )
		self.initUndoHistory( codeChangeModule.newHexField, newHexValue )

		# Bind a left-click event to this module (for selecting it radio-button style).
		innerFrame.bind( '<1>', self.codeChangeSelected )
		for frame in innerFrame.winfo_children():
			frame.bind( '<1>', self.codeChangeSelected )
			for widget in frame.winfo_children():
				if widget.winfo_class() != 'TButton' and widget.winfo_class() != 'TEntry': # Exclude binding from the remove button and input fields.
					widget.bind( '<1>', self.codeChangeSelected )
		
	def removeCodeChange( self, codeChangeModule ):
		versionTab = root.nametowidget( self.gameVersionsNotebook.select() )

		# Reset the newHex field if it is set for use by the currently selected module.
		if codeChangeModule['bg'] == 'orange':
			# Detach the previously selected module's newHex field
			newHexFieldContainer = versionTab.winfo_children()[1]
			self.clearNewHexFieldContainer( newHexFieldContainer )

			self.attachEmptyNewHexField( versionTab, False )

		# Delete the code change module, and update the save status
		codeChangeModule.destroy()
		self.undoableChanges = True
		self.updateSaveStatus( True )

		# If this is the last code change, remove this version tab from the notebook
		codeChangesListFrame = codeChangeModule.master
		if codeChangesListFrame.winfo_children() == []:
			versionTab.destroy()

			# If this is the last version tab, remove the Share and Save buttons, and the code changes container (notebook)
			if len( self.gameVersionsNotebook.tabs() ) == 1:
				self.gameVersionsNotebook.destroy()
				self.gameVersionsNotebook = None
				for widget in self.buttonsFrame.winfo_children()[-4:]: # Selects only the last (left-most) 4 buttons added
					widget.destroy()
			else:
				self.gameVersionsNotebook.select( self.gameVersionsNotebook.tabs()[0] ) # Select the first tab.

	def importGeckoCode( self ):
		# Prompt the user to enter the Gecko code
		userMessage = "Copy and paste your Gecko code here.\nCurrently, only opCodes 04, 06, and C2 are supported."
		entryWindow = PopupScrolledTextWindow( root, title='Gecko Codes Import', message=userMessage, width=55, height=22, button1Text='Import' )
		if not entryWindow.entryText: return

		# Get the revision for this code
		if dol.revision:
			dolRevision = dol.revision
		else: # Prompt the user for it
			revisionWindow = RevisionPromptWindow( labelMessage='Choose the region and game version that this code is for.', regionSuggestion='NTSC', versionSuggestion='02' )

			# Check the values gained from the user prompt (empty strings mean they closed or canceled the window)
			if not revisionWindow.region or not revisionWindow.version: return
			else: 
				dolRevision = revisionWindow.region + ' ' + revisionWindow.version

		# Parse the gecko code input and create code change modules for the changes
		title, newAuthors, description, codeChanges = parseGeckoCode( dolRevision, entryWindow.entryText )

		# Set the mod's title and description, if they have not already been set
		if not self.getInput( self.titleEntry ): 
			self.titleEntry.insert( 0, title )
			self.updateTabName()
		if description:
			if self.getInput( self.descScrolledText ): # If there is already some content, add a line break before the new description text
				self.descScrolledText.insert( 'end', '\n' )
			self.descScrolledText.insert( 'end', description )

		# Add any authors not already added
		currentAuthors = [ name.strip() for name in self.getInput( self.authorsEntry ).split(',') if name != '' ]
		for name in newAuthors.split( ',' ):
			if name.strip() not in currentAuthors: 
				currentAuthors.append( name.strip() )
		self.authorsEntry.delete( 0, 'end' )
		self.authorsEntry.insert( 'end', ', '.join(currentAuthors) )

		# Add the new code change modules
		for changeType, customCodeLength, offset, originalCode, customCode, _ in codeChanges:
			self.addCodeChangeModule( changeType, customCodeLength, offset, originalCode, customCode, dolRevision )

		# Mark that these changes have not been saved yet, and update the status display
		self.undoableChanges = True
		self.updateSaveStatus( True )

		playSound( 'menuChange' )

	def getCurrentlySelectedModule( self, versionTab ):
		# Get the modules' parent frame widget for the currently selected version tab.
		codeChangesListFrame = versionTab.winfo_children()[0].interior

		# Loop over the child widgets to search for the currently selected code change module
		for codeChangeModule in codeChangesListFrame.winfo_children():
			if codeChangeModule['bg'] != 'SystemButtonFace': return codeChangeModule
		else: return None

	def clearNewHexFieldContainer( self, newHexFieldContainer ): # Ensures all newHex fields are detached from the GUI.
		for widget in newHexFieldContainer.winfo_children():
			if widget.winfo_manager(): widget.pack_forget()

	def codeChangeSelected( self, event ):
		# Get the modules (parent frames) for the current/previously selected code change modules.
		versionTab = root.nametowidget( self.gameVersionsNotebook.select() )

		# Deselect any previously selected module
		previouslySelectedModule = self.getCurrentlySelectedModule( versionTab )
		if previouslySelectedModule: previouslySelectedModule['bg'] = 'SystemButtonFace'

		# Get the frame widget of the code change module that was selected and change its border color.
		codeChangeModule = event.widget
		while not hasattr( codeChangeModule, 'changeType' ): codeChangeModule = codeChangeModule.master
		codeChangeModule['bg'] = 'orange'

		# Detach the previously selected module's newHex field
		newHexFieldContainer = versionTab.winfo_children()[1]
		self.clearNewHexFieldContainer( newHexFieldContainer )

		# Attach the newHex field of the newly selected code change module (all newHex widgets share the same parent)
		codeChangeModule.newHexField.pack( fill='both', expand=1, padx=2, pady=1 )
		codeChangeModule.newHexField.focus_set() # Ensures that keypresses will go to the newly attached text field, not the old one

	def updateTabName( self ):
		# The timeout above is done, update the tab for this mod.
		newTitle = self.titleEntry.get()

		# Get the tab containing this mod; move up the GUI heirarchy until the notebook's tab (a TFrame in this case) is found.
		tabFrame = self.titleEntry.master
		while tabFrame.winfo_class() != 'TFrame': tabFrame = tabFrame.master

		# Modify the tab's title
		if newTitle.strip() == '': newTitle = 'New Mod'
		if len( newTitle ) > 40: newTitle = newTitle[:40].rstrip() + '...'
		constructionNotebook.tab( tabFrame, text=newTitle )

	def updateModule( self, versionTab, codeChangeModule, userActivated=False ):

		""" Updates the module's code length and original hex values. """

		changeType = codeChangeModule.changeType

		# Update the module's code length display
		newHex = codeChangeModule.newHexField.get( '1.0', 'end' ).strip()
		customCodeLength = getCustomCodeLength( newHex, preProcess=True, includePaths=self.includePaths )
		codeChangeModule.customCodeLength.set( '(' + uHex(customCodeLength) + ' bytes)' )

		# Make sure there is something to update; Gecko modules and SFs don't have an 'originalHex' or 'offset' field to update.
		if changeType == 'gecko' or changeType == 'standalone':
			return

		offsetString = codeChangeModule.offset.get().replace( '0x', '' ).strip()

		# Update the original hex value
		codeChangeModule.originalHex.delete( 0, 'end' )
		if ( changeType == 'static' or changeType == 'injection' ) and offsetString != '':
			if not validHex( offsetString.replace( '0x', '' ) ): msg( 'Invalid offset hex.' )
			else:
				# Determine the length of data to get from the vanilla DOL.
				byteCountToRead = 0
				if changeType == 'injection': byteCountToRead = 4
				elif changeType == 'static' and newHex != '': byteCountToRead = customCodeLength

				if byteCountToRead > 0:
					# Load a dol for reference if one is not already loaded (there may be no dol currently loaded)
					revision = self.gameVersionsNotebook.tab( versionTab, "text" )[4:]
					vanillaDol = loadVanillaDol( revision )

					# If the given offset is a RAM address, convert it to a DOL offset
					dolOffset = -1
					if len( offsetString ) == 8 and offsetString.startswith('8'): # 0x has already been removed (always assumed to be a hex value)
						offset = int( offsetString[1:], 16 )
						if offset >= 0x3100:
							if offset < vanillaDol.maxRamAddress: dolOffset = offsetInDOL( offset, vanillaDol.sectionInfo )
							else: codeChangeModule.originalHex.insert( 0, 'Address is too big' )
						else: codeChangeModule.originalHex.insert( 0, 'Address is too small' )
					else: 
						offset = int( offsetString, 16 )
						if offset >= 0x100:
							if offset < vanillaDol.maxDolOffset: dolOffset = offset
							else: codeChangeModule.originalHex.insert( 0, 'Offset is too big' )
						else: codeChangeModule.originalHex.insert( 0, 'Offset is too small' )

					# Get the original hex data, and update the GUI with the value.
					if dolOffset != -1:
						codeChangeModule.originalHex.insert( 0, vanillaDol.data[dolOffset*2:(dolOffset+byteCountToRead)*2].upper() )

	def queueUndoStatesUpdate( self, event ):
		widget = event.widget

		# Ignore certain keys which won't result in content changes. todo: Could probably add some more keys to this
		if event.keysym in ( 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock', 'Left', 'Up', 'Right', 'Down', 'Home', 'End', 'Num_Lock' ):
			return

		# Cancel any pending undo state; instead, wait until there is a sizable state/chunk of data to save
		if widget.undoStateTimer: widget.after_cancel( widget.undoStateTimer )

		# Start a new timer, to grab all changes within a certain time for one undo state
		widget.undoStateTimer = widget.after( 800, lambda w=widget: self.addUndoState(w) )

	def addUndoState( self, widget ):

		""" This is responsible for adding new undo/redo states to the undoStates list.
			If this is called and the widget's contents are the same as the current history state,
			then non-editing keys were probably pressed, such as an arrow key or CTRL/SHIFT/etc, in
			which case this method will just exit without creating a new state. """

		if widget.undoStateTimer: # This method may have been called before this fired. Make sure it doesn't fire twice!
			widget.after_cancel( widget.undoStateTimer )
		widget.undoStateTimer = None

		# Get what's currently in the input field
		if widget.winfo_class() == 'Text': # Includes ScrolledText widgets
			currentContents = widget.get( '1.0', 'end' ).strip().encode( 'utf-8' )
		else: # Pulling from an Entry widget
			currentContents = widget.get().strip().encode( 'utf-8' )

		# Check if the widget's contents have changed since the last recorded undo state. If they haven't, there's nothing more to do here.
		if currentContents == widget.undoStates[widget.undoStatesPosition]: # Comparing against the current history state
			return

		# Discard any [potential redo] history beyond the current position
		widget.undoStates = widget.undoStates[:widget.undoStatesPosition + 1]

		# Add the new current state to the undo history, and set the current history position to it
		widget.undoStates.append( currentContents )
		widget.undoStatesPosition = len( widget.undoStates ) - 1

		# Limit the size of the undo list (commented out due to currently irreconcilable issues (index out of range) with savedContents/undoPosition) todo: fix?
		# if len( widget.undoStates ) > 10:
		# 	widget.undoStates = widget.undoStates[-10:] # Forgets the earliest states

		# Check if this is a code modification offset (DOL Offset or RAM Address); Adds some special processing
		if getattr( widget, 'offsetEntry', False ):
			versionTab = root.nametowidget( self.gameVersionsNotebook.select() )
			codeChangeModule = widget.master
			while not hasattr( codeChangeModule, 'changeType' ): codeChangeModule = codeChangeModule.master
			self.updateModule( versionTab, codeChangeModule )

		# If this is the mod title, also update the name of this tab
		elif widget == self.titleEntry: self.updateTabName()

		# Update the save status
		if currentContents != widget.savedContents:
			self.updateSaveStatus( True )
		else: # Can't be sure of changes, so perform a more thorough check
			self.updateSaveStatus( self.changesArePending() )

	def undo( self, event ):
		widget = event.widget

		# If changes are pending addition to the widget's undo history, process them immediately before proceeding
		if widget.undoStateTimer: self.addUndoState( widget )

		# Decrement the current position within the undo history
		if widget.undoStatesPosition > 0:
			widget.undoStatesPosition -= 1
			self.restoreUndoState( widget )

		return 'break' # Meant to prevent the keypresses that triggered this from propagating to other events

	def redo( self, event ):
		widget = event.widget

		# If changes are pending addition to the widget's undo history, process them immediately before proceeding
		if widget.undoStateTimer: self.addUndoState( widget )

		# Increment the current position within the undo history
		if widget.undoStatesPosition < len( widget.undoStates ) - 1:
			widget.undoStatesPosition += 1
			self.restoreUndoState( widget )

		return 'break' # Meant to prevent the keypresses that triggered this from propagating to other events

	def restoreUndoState( self, widget ):
		newContents = widget.undoStates[widget.undoStatesPosition]

		# Update the contents of the widget
		if widget.winfo_class() == 'Text':
			entryPoint = '1.0'
		else: entryPoint = 0
		widget.delete( entryPoint, 'end' )
		widget.insert( 'end', newContents )

		# If there's a difference between the current input and the saved state, there are certainly pending changes.
		if newContents != widget.savedContents:
			self.updateSaveStatus( True )
		else: # Can't be sure of changes, so perform a more thorough check
			self.updateSaveStatus( self.changesArePending() )

	def getInput( self, widget ): # Gets a text or entry widget's current input while forcing undo history updates.
		# If changes are pending addition to the widget's undo history, process them immediately before proceeding
		if widget.undoStateTimer: self.addUndoState( widget )

		if widget.winfo_class() == 'Text': # Includes ScrolledText widgets
			return widget.get( '1.0', 'end' ).strip().encode( 'utf-8' )
		else: # Pulling from an Entry widget
			return widget.get().strip().encode( 'utf-8' )

	def widgetHasUnsavedChanges( self, widget ):
		currentContents = self.getInput( widget )

		# Compare the current contents to what was last saved
		if currentContents != widget.savedContents:
			return True
		else:
			return False

	def changesArePending( self ):
		if self.undoableChanges: # This is a flag for changes that have been made which "undo" can't be used for
			return True

		# Check all current code change modules for changes
		if self.gameVersionsNotebook:
			for windowName in self.gameVersionsNotebook.tabs()[:-1]: # Ignores versionChangerTab.
				versionTab = root.nametowidget( windowName )
				codeChangesListFrame = versionTab.winfo_children()[0].interior
				for codeChangeModule in codeChangesListFrame.winfo_children():
					# Check the 'New Hex' (i.e. new asm/hex code) field
					if self.widgetHasUnsavedChanges( codeChangeModule.newHexField ):
						return True

					# Get module label and Entry input field widgets
					innerFrame = codeChangeModule.winfo_children()[0]
					bottomFrameChildren = innerFrame.winfo_children()[1].winfo_children()

					# Check widgets which have undo states for changes
					for widget in bottomFrameChildren:
						if getattr( widget, 'undoStates', False ) and self.widgetHasUnsavedChanges( widget ):
							return True

		# Check the title/author/description for changes
		for widget in ( self.titleEntry, self.authorsEntry, self.descScrolledText ):
			if self.widgetHasUnsavedChanges( widget ): return True

		return False

	def updateSaveStatus( self, changesPending, message='' ):
		if changesPending:
			if not message: message = 'Unsaved'
			self.saveStatusLabel['foreground'] = '#a34343' # Shade of red
		else:
			self.saveStatusLabel['foreground'] = '#292' # Shade of green

		self.saveStatus.set( message )

	def buildModString( self ):

		""" Builds a string to store/share this mod in MCM's usual code format. """

		# Get the text input for the title and author(s)
		title = self.getInput( self.titleEntry )
		if title == '': title = 'This Mod Needs a Title!'
		authors = self.getInput( self.authorsEntry )
		if authors == '': authors = '??'

		# Validate the text input to make sure it's only basic ASCII
		for subject in ('title', 'authors'):
			stringVariable = eval( subject ) # Basically turns the string into one of the variables created above
			if not isinstance( stringVariable, str ):
				typeDetected = str(type(stringVariable)).replace("<type '", '').replace("'>", '')
				msg('The input needs to be ASCII, however ' + typeDetected + \
					' was detected in the ' + subject + ' string.', 'Input Error')
				return ''

		# Add the description and any web links (basically parsed with descriptions, so they're included together)
		description = '\n' + self.getInput( self.descScrolledText ).encode( 'ascii', 'ignore' ) # The encode filters out any non-ascii characters. todo: warn user?
		webLinksLines = []
		for urlObj, comments in self.webLinks: # Comments should still have the '#' character prepended
			webLinksLines.append( '<{}>{}'.format(urlObj.geturl(), comments) )
		if webLinksLines: description += '\n' + '\n'.join( webLinksLines )
		if description == '\n': description = '' # Remove the line break if a description is not present.
		modString = ['\n' + title + description + '\n[' + authors + ']']

		codeChangesHeader = 'Revision ---- DOL Offset ---- Hex to Replace ---------- ASM Code -'
		addChangesHeader = False

		if self.gameVersionsNotebook:
			# Gather information from each game version tab
			for windowName in self.gameVersionsNotebook.tabs()[:-1]: # Ignores versionChangerTab.
				versionTab = root.nametowidget( windowName )
				codeChangesListFrame = versionTab.winfo_children()[0].interior
				revision = self.gameVersionsNotebook.tab( versionTab, option='text' )[4:]
				addVersionHeader = True

				# Iterate the codeChanges for this game version
				for codeChangeModule in codeChangesListFrame.winfo_children():
					changeType = codeChangeModule.changeType

					# Saves the new hex field (if this module is selected), and updates the module's code length and original hex values
					self.updateModule( versionTab, codeChangeModule )

					# Get the newHex input.
					newHex = self.getInput( codeChangeModule.newHexField )
					if newHex.startswith('0x'): newHex = newHex[2:] # Don't want to replace all instances

					if changeType == 'static' or changeType == 'injection':
						addChangesHeader = True

						# Get the offset and original (vanilla game code) hex inputs. Remove whitespace & hex identifiers.
						offset = ''.join( self.getInput(codeChangeModule.offset).split() ).replace('0x', '')
						originalHex = ''.join( self.getInput(codeChangeModule.originalHex).split() ).replace('0x', '')

						# Check that inputs have been given, and then convert the ASM to hex if necessary.
						if offset == '' or newHex == '':
							msg( 'There are offset or new code values missing\nfor some ' + revision + ' changes.' )
							self.gameVersionsNotebook.select( windowName )
							return ''
						elif originalHex == '' or not validHex( originalHex ):
							msg( 'There are Original Hex values missing or invalid among the ' + revision + ' changes, and new values could not be determined. An offset may be incorrect.' )
							return ''

						# Create the beginning of the line (revision header, if needed, with dashes).
						headerLength = 13
						if addVersionHeader:
							lineHeader = revision + ' ' + ('-' * ( headerLength - 1 - len(revision) )) # extra '- 1' for the space after revision
							addVersionHeader = False
						else: lineHeader = '-' * headerLength

						# Build a string for the offset portion
						numOfDashes = 8 - len( offset )
						dashes = '-' * ( numOfDashes / 2 ) # if numOfDashes is 1 or less (including negatives), this will be an empty string
						if numOfDashes % 2 == 0: # If the number of dashes left over is even (0 is even)
							offsetString = dashes + ' ' + '0x' + offset + ' ' + dashes
						else: # Add an extra dash at the end (the int division above rounds down)
							offsetString = dashes + ' ' + '0x' + offset + ' ' + dashes + '-'

						# Build a string for a standard (short) static overwrite
						if changeType == 'static' and len(originalHex) <= 16 and newHex.splitlines()[0].split('#')[0] != '': # Last check ensures there's actually code, and not just comments/whitespace
							modString.append( lineHeader + offsetString + '---- ' + originalHex + ' -> ' + newHex )

						# Long static overwrite
						elif changeType == 'static':
							modString.append( lineHeader + offsetString + '----\n\n' + customCodeProcessor.beautifyHex(originalHex) + '\n\n -> \n\n' + newHex + '\n' )

						# Injection mod
						else:
							modString.append( lineHeader + offsetString + '---- ' + originalHex + ' -> Branch\n\n' + newHex + '\n' )

					elif changeType == 'gecko':
						if addVersionHeader: modString.append( revision + '\n' + newHex + '\n' )
						else: modString.append( newHex + '\n' )

					elif changeType == 'standalone':
						functionName = self.getInput( codeChangeModule.offset )

						# Check that a function name was given, and then convert the ASM to hex if necessary.
						if functionName == '':
							msg( 'A standalone function among the ' + revision + ' changes is missing a name.' )
							self.gameVersionsNotebook.select( windowName )
							return ''
						elif ' ' in functionName:
							msg( 'Function names may not contain spaces. Please rename those for ' + revision + ' and try again.' )
							self.gameVersionsNotebook.select( windowName )
							return ''

						# Add the name wrapper and version identifier
						functionName = '<' + functionName + '> ' + revision

						# Assemble the line string with the original and new hex codes.
						modString.append( functionName + '\n' + newHex + '\n' )

		if addChangesHeader:
			modString.insert( 1, codeChangesHeader ) # Inserts right after the initial title/author/description string

		return '\n'.join( modString )

	def _getRequiredStandaloneFunctionNames( self ):
		
		""" Gets the names of all standalone functions this mod requires. """

		if not self.gameVersionsNotebook or not self.gameVersionsNotebook.tabs(): # Latter check is a failsafe; not expected
			return [], []

		functionNames = set()
		missingFunctions = set()

		# Iterate over each game revision
		for windowName in self.gameVersionsNotebook.tabs()[:-1]: # Ignores versionChangerTab.
			versionTab = root.nametowidget( windowName )
			codeChangesListFrame = versionTab.winfo_children()[0].interior

			# Iterate the codeChanges for this game version
			for codeChangeModule in codeChangesListFrame.winfo_children():
				# Get the code for this code change, and pre-process it
				newHex = self.getInput( codeChangeModule.newHexField )
				preProcessedCustomCode = customCodeProcessor.preAssembleRawCode( newHex, self.includePaths )[1]

				functionNames, missingFunctions = parseCodeForStandalones( preProcessedCustomCode, functionNames, missingFunctions )

				# If the current code change module is a standalone function, make sure it's not in the set of "missing" SFs
				if codeChangeModule.changeType == 'standalone' and missingFunctions:
					thisFunctionName = self.getInput( codeChangeModule.offset )
					missingFunctions.remove( thisFunctionName )

		return list( functionNames ), list( missingFunctions ) # functionNames will also include those that are missing

	def saveModToLibraryAs( self ):

		""" Saves a mod to a new location. Wrapper for the saveModToLibrary method. """

		# Remember the original values for save location (in case they need to be restored), and then clear them
		originalSourceFile = self.sourceFile
		originalFileIndex = self.fileIndex
		originalMajorChanges = self.undoableChanges

		# Clear the save location properties for this mod. This forces the save function to default to creating a new file
		self.sourceFile = ''
		self.fileIndex = -1
		self.undoableChanges = True

		# Attempt to save the mod
		saveSuccedded = self.saveModToLibrary()

		# If the save failed, restore the previous save location & status
		if not saveSuccedded:
			self.sourceFile = originalSourceFile
			self.fileIndex = originalFileIndex
			self.undoableChanges = originalMajorChanges

	def saveModToLibrary( self ):
		# Make sure there are changes to be saved
		if not self.changesArePending():
			self.updateSaveStatus( False, 'No Changes to be Saved' )
			self.saveStatusLabel['foreground'] = '#333' # Shade of gray
			return

		# Confirm that this mod (if this is something from the Mod Library tab) is not currently installed
		modInstalled = False
		if self.sourceFile and self.fileIndex != -1:

			for mod in genGlobals['allMods']:
				# Compare by file and file position
				if mod.fileIndex == self.fileIndex and mod.sourceFile == self.sourceFile:
					# Double-check that this is the correct mod by name
					if mod.name != self.getInput( self.titleEntry ):
						userConfirmedEquivalency = tkMessageBox.askyesno( 'Confirm Mod Equivalency', 'Is this the same mod as "' + mod.name + '" in the Mods Library? ', parent=root )

						if not userConfirmedEquivalency:
							# Mod save location lost; inform the user and prepare to save this as a new mod.
							msg( "The Mods Library reference to the mod being edited has been lost (likely due to a duplicate mod, or manual modification/reordering of "
								'the Mods Library after opening this mod in the Mod Construction tab). Without verification of this reference, the original '
								'save location of this mod cannot be certain. To prevent the overwrite of a different mod, this must be saved as a new mod.' )
							self.saveModToLibraryAs()
							return

					# Equivalent mod found. Check whether it's installed in a game disc/DOL
					if mod.state == 'enabled' or mod.state == 'pendingDisable':
						modInstalled = True
					
					break

		if modInstalled:
			msg( 'Mods must be uninstalled from your game before modifying them.' )
			self.updateSaveStatus( True, 'Unable to Save' )
			return False

		modString = self.buildModString() # This will also immediately update any pending undo history changes

		if not modString: # Failsafe, assuming the method above will report any possible errors
			self.updateSaveStatus( True, 'Unable to Save' )
			return False

		saveSuccessful = False
		userCanceled = False

		# Prompt for a file to save to if no source file is defined. (Means this was newly created in the GUI, or this is a 'SaveAs' operation)
		if self.sourceFile == '':
			targetFile = tkFileDialog.askopenfilename(
				title="Choose the file you'd like to save the mod to (it will be appended to the end).",
				initialdir=getModsFolderPath(),
				filetypes=[ ('Text files', '*.txt'), ('all files', '*.*') ]
				)

			if not targetFile:
				userCanceled = True
			else:
				# Append this mod to the end of the target Mod Library text file (could be a new file, or an existing one).
				try:
					if os.path.exists( targetFile ):
						# Set this mod's save location so that subsequent saves will automatically go to this same place, and check if a separator is needed.
						self.sourceFile = targetFile
						with open( targetFile, 'r') as modFile:
							fileContents = modFile.read()
						if fileContents:
							self.fileIndex = len( fileContents.split( '-==-' ) )
							modString = '\n\n\n\t-==-\n\n' + modString # Prepends a separator to this mod.
						else: self.fileIndex = 0

						# Save the mod to the file.
						with open( targetFile, 'a' ) as libraryFile:
							libraryFile.write( modString )
						saveSuccessful = True
				except Exception as err:
					print 'Unable to save the mod to the library file:'
					print err

				# Rebuild the include paths list, using this new file for one of the paths
				modsFolderIncludePath = os.path.join( getModsFolderPath(), '.include' )
				self.includePaths = [ os.path.dirname(targetFile), modsFolderIncludePath, os.path.join(scriptHomeFolder, '.include') ]

		else: # A source file is already defined.
			if self.fileIndex == -1: msg( "The index (file position) for this mod could not be determined. Try using 'Save As' to save this mod to the end of a file." )
			else:
				targetFile = self.sourceFile

				# Make sure the target file can be found, then replace the mod within it with the new version.
				if not os.path.exists( targetFile ):
					msg( 'Unable to locate the Library file:\n\n' + targetFile )

				else: 
					try:
						# Pull the mods from their library file, and separate them.
						with open( targetFile, 'r') as modFile:
							mods = modFile.read().split( '-==-' )

						# Replace the old mod, reformat the space in-between mods, and recombine the file's text.
						mods[self.fileIndex] = modString
						mods = [code.strip() for code in mods] # Removes the extra whitespace around mod strings.
						completedFileText = '\n\n\n\t-==-\n\n\n'.join( mods )

						with open( targetFile, 'w' ) as libraryFile:
							libraryFile.write( completedFileText )

						saveSuccessful = True
					except: pass

		if saveSuccessful:
			# Iterate over all code change modules to update their save state history (saved contents updated to match current undo history index)
			for windowName in self.gameVersionsNotebook.tabs()[:-1]: # Ignores versionChangerTab.
				versionTab = root.nametowidget( windowName )
				codeChangesListFrame = versionTab.winfo_children()[0].interior

				# Iterate the codeChanges for this game version
				for codeChangeModule in codeChangesListFrame.winfo_children():
					if getattr( codeChangeModule.newHexField, 'undoStates', None ): # May return an empty list, in which case the contents haven't been modified
						# Update the 'New Hex' (i.e. new asm/hex code) field
						codeChangeModule.newHexField.savedContents = codeChangeModule.newHexField.get( '1.0', 'end' ).strip().encode( 'utf-8' )

					# Get module label and Entry input field widgets
					innerFrame = codeChangeModule.winfo_children()[0]
					bottomFrameChildren = innerFrame.winfo_children()[1].winfo_children()

					# Update those widgets (which have undo states) with changes
					for widget in bottomFrameChildren:
						if getattr( widget, 'undoStates', False ):
							widget.savedContents = widget.get().strip().encode( 'utf-8' )

			# Update the saved contents for the standard input fields
			for widget in ( self.titleEntry, self.authorsEntry, self.descScrolledText ):
				if getattr( widget, 'undoStates', None ): # May return an empty list, in which case the contents haven't been modified
					if widget.winfo_class() == 'Text': # Includes ScrolledText widgets
						widget.savedContents = widget.get( '1.0', 'end' ).strip().encode( 'utf-8' )
					else: # Pulling from an Entry widget
						widget.savedContents = widget.get().strip().encode( 'utf-8' )

			# Update the flag used for tracking other undoable changes
			self.undoableChanges = False

			# Give an audio cue and update the GUI
			playSound( 'menuSelect' )
			self.updateSaveStatus( False, 'Saved To Library' )

			# Reload the library to get the new or updated codes.
			scanModsLibrary( playAudio=False )

		else:
			if userCanceled:
				self.updateSaveStatus( True, 'Operation Canceled' )
			else:
				self.updateSaveStatus( True, 'Unable to Save' )
		
		return saveSuccessful

	def analyzeMod( self ):

		""" Collects information on this mod, and shows it to the user in a pop-up text window. """ # todo: switch to joining list of strings for efficiency

		# Assemble the header text
		analysisText = 'Info for "' + self.getInput( self.titleEntry ) + '"'
		analysisText += '\nProgram Classification: ' + self.type
		if os.path.isdir( self.sourceFile ):
			analysisText += '\nSource Folder: ' + self.sourceFile
		elif os.path.exists( self.sourceFile ):
			analysisText += '\nSource File: ' + self.sourceFile
			analysisText += '\nPosition in file: ' + str( self.fileIndex )
		else:
			analysisText += '\nSource: Unknown! (The source path could not be found)'

		availability = []
		totalCodeChanges = 0
		changeTypeTotals = {}

		# Check for all code changes (absolute total, and totals per type).
		if self.gameVersionsNotebook:
			for windowName in self.gameVersionsNotebook.tabs()[:-1]: # Skips tab used for adding revisions
				versionTab = root.nametowidget( windowName ) # Gets the actual widget for this tab

				availability.append( self.gameVersionsNotebook.tab( versionTab, option='text' )[4:] )
				codeChangesListFrame = versionTab.winfo_children()[0].interior
				codeChangeModules = codeChangesListFrame.winfo_children()
				totalCodeChanges += len( codeChangeModules )

				# Count the number of changes for each change type, and get the standalone functions required
				for codeChange in codeChangeModules:
					if codeChange.changeType not in changeTypeTotals: changeTypeTotals[codeChange.changeType] = 1
					else: changeTypeTotals[codeChange.changeType] += 1
		
		# Construct strings for what code change types are present, and their counts
		analysisText += '\nCode changes available for ' + grammarfyList( availability ) + '\n\nCode Changes (across all game versions):'
		for changeType in changeTypeTotals:
			analysisText += '\n - ' + presentableModType( changeType ) + 's: ' + str( changeTypeTotals[changeType] )

		# Check for required SFs
		requiredStandaloneFunctions, missingFunctions = self._getRequiredStandaloneFunctionNames()
		if not requiredStandaloneFunctions: analysisText += '\n\nNo Standalone Functions required.'
		else:
			analysisText += '\n\nRequired Standalone Functions:\n' + '\n'.join( requiredStandaloneFunctions )

			if missingFunctions: 
				analysisText += '\n\nThese functions are required, but are not packaged with this mod:\n' + '\n'.join( missingFunctions )

		analysisText += '\n\n\tInclude Paths:\n' + '\n'.join( self.includePaths )

		# Present the analysis to the user in a new window
		cmsg( analysisText, 'Info for "' + self.getInput( self.titleEntry ) + '"', 'left' )

	def switchOffsetDisplayType( self ):

		""" Goes through each of the code changes, and swaps between displaying offsets as DOL offsets or RAM addresses. 
			These are still tracked as strings, so they will be saved in the chosen form in the library files as well. """

		# Toggle the saved variable and the button text (and normalize the string since this is exposed to users in the options.ini file)
		offsetView = settings.get( 'General Settings', 'offsetView' ).lstrip().lower()
		if offsetView.startswith( 'd' ):
			offsetView = 'ramAddress'
			buttonText = 'Display DOL Offsets'
		else:
			offsetView = 'dolOffset'
			buttonText = 'Display RAM Addresses'
		self.offsetViewBtn['text'] = buttonText

		# Iterate over the tabs for each game version
		for tabWindowName in self.gameVersionsNotebook.tabs()[:-1]: # Skips tab for adding revisions
			versionTab = root.nametowidget( tabWindowName )
			revision = self.gameVersionsNotebook.tab( versionTab, option='text' )[4:]
			codeChangesListFrame = versionTab.winfo_children()[0].interior
			codeChangeModules = codeChangesListFrame.winfo_children()

			# Iterate over the code change modules for this game version
			for i, module in enumerate( codeChangeModules, start=1 ):
				if module.changeType == 'static' or module.changeType == 'injection':
					# Get the current value
					origOffset = module.offset.get().strip().replace( '0x', '' )

					# Validate the input
					if not validHex( origOffset ):
						if len( self.gameVersionsNotebook.tabs() ) > 2: # Be specific with the revision
							msg( 'Invalid hex detected for the offset of code change {} of {}: "{}".'.format(i, revision, module.offset.get().strip()), 'Invalid Offset Characters' )
						else: # Only one revision to speak of
							msg( 'Invalid hex detected for the offset of code change {}: "{}".'.format(i, module.offset.get().strip()), 'Invalid Offset Characters' )
						continue

					# Convert the value
					if offsetView == 'dolOffset':
						newOffset = normalizeDolOffset( origOffset, dolObj=originalDols[revision], returnType='string' )
					else: newOffset = normalizeRamAddress( origOffset, dolObj=originalDols[revision], returnType='string' )

					# Validate the converted ouput value
					if newOffset == -1: continue # A warning would have been given to the user from the above normalization function

					# Display the value
					module.offset.delete( 0, 'end' )
					module.offset.insert( 0, newOffset )

		# Remember the current display option
		settings.set( 'General Settings', 'offsetView', offsetView )
		saveOptions()

	def closeMod( self ):
		# If there are unsaved changes, propt whether the user really wants to close.
		if self.saveStatusLabel['foreground'] == '#a34343':
			sureToClose = tkMessageBox.askyesno( 'Unsaved Changes', "It looks like this mod may have some changes that haven't been saved to your library. Are you sure you want to close it?" )
			if not sureToClose: return

		self.master.destroy()

	def addWebLink( self, urlObj, comments, modChanged=True ):
		
		url = urlObj.geturl()
		domain = urlObj.netloc.split( '.' )[-2] # i.e. 'smashboards' or 'github'
		destinationImage = imageBank[ domain + 'Link' ]
		
		# Add an image for this link
		imageLabel = ttk.Label( self.webLinksFrame, image=destinationImage )
		imageLabel.urlObj = urlObj
		imageLabel.comments = comments
		imageLabel.pack()

		# Add hover tooltips
		hovertext = 'The {}{} page...\n{}'.format( domain[0].upper(), domain[1:], url )
		if comments: hovertext += '\n\n' + comments
		ToolTip( imageLabel, hovertext, delay=700, wraplength=800, justify='center' )

		# if modChanged: # If false, this is being called during initialization
		# 	self.undoableChanges = True


class WebLinksEditor( basicWindow ):

	""" Tool window to add/remove web links in the Mod Construction tab. """

	def __init__( self, webLinksFrame ):
		basicWindow.__init__( self, root, 'Web Links Editor', offsets=(160, 100), resizable=True, topMost=False )

		Label( self.window, text=('Web links are useful sources of information, or links to places of discussion.'
			'\nCurrent valid destinations are SmashBoards, GitHub, and YouTube.'), wraplength=480 ).grid( columnspan=3, column=0, row=0, padx=40, pady=10 )

		# Iterate over the widgets in the 'Web Links' frame in the other window, to create new widgets here based on them
		row = 1
		for label in webLinksFrame.winfo_children():
			# Get info from this label widget
			url = label.urlObj.geturl()
			domain = label.urlObj.netloc.split( '.' )[-2] # i.e. 'smashboards' or 'github'
			destinationImage = imageBank[ domain + 'Link' ]

			# Can't clone the label, so make a new one
			imageLabel = ttk.Label( self.window, image=destinationImage )
			imageLabel.grid( column=0, row=row )

			# Add a text field entry for the URL
			urlEntry = ttk.Entry( self.window, width=70 )
			urlEntry.insert( 0, url )
			urlEntry.grid( column=1, row=row, sticky='ew' )

			# Add the comment below this, if there is one, and the button to add/edit them
			if label.comments:
				# Add the add/edit comment button
				commentsBtn = Button( self.window, text='Edit Comment', anchor='center' )
				commentsBtn.grid( column=2, row=row, padx=14, pady=5 )

				# Add the comment
				commentLabel = ttk.Label( self.window, text=label.comments.lstrip(' #') )
				commentLabel.grid( column=1, row=row+1, sticky='new' )

				# Add the remove button
				removeBtn = Button( self.window, text='-', width=2 )
				ToolTip( removeBtn, 'Remove', delay=700 )
				removeBtn.grid( column=3, row=row, padx=(0, 14) )
				row += 2
			else:
				# Add the add/edit comment button
				commentsBtn = Button( self.window, text='Add Comment', anchor='center' )
				commentsBtn.grid( column=2, row=row, padx=14, pady=5 )

				# Add the remove button
				removeBtn = Button( self.window, text='-', width=2 )
				ToolTip( removeBtn, 'Remove', delay=700 )
				removeBtn.grid( column=3, row=row, padx=(0, 14) )
				row += 1
		
		# Add the 'Add' and 'OK / Cancel' buttons
		buttonsFrame = ttk.Frame( self.window )
		ttk.Button( buttonsFrame, text='OK' ).pack( side='left', padx=(0, 15) )
		ttk.Button( buttonsFrame, text='Cancel', command=self.close ).pack( side='right' )
		buttonsFrame.grid( columnspan=4, column=0, row=row, pady=14 )
		addBtn = Button( self.window, text='Add Link', width=12 )
		addBtn.grid( columnspan=2, column=2, row=row )

		# Allow the grid to resize
		self.window.columnconfigure( 0, weight=1, minsize=46 )
		self.window.columnconfigure( 1, weight=3 )
		#self.window.columnconfigure( (2, 3), weight=1 )
		self.window.columnconfigure( 2, weight=1, minsize=120 )
		self.window.columnconfigure( 3, weight=1, minsize=35 )
		self.window.rowconfigure( 'all', weight=1 )


class AsmToHexConverter( basicWindow ):

	""" Tool window to convert assembly to hex and vice-verca. """

	def __init__( self ):
		basicWindow.__init__( self, root, 'ASM <-> HEX Converter', offsets=(160, 100), resizable=True, topMost=False )
		self.window.minsize( width=480, height=350 )

		Label( self.window, text=('This assembles PowerPC assembly code into raw hex,\nor disassembles raw hex into PowerPC assembly.'
			"\n\nNote that this functionality is also built into the entry fields for new code in the 'Add New Mod to Library' interface. "
			'So you can use your assembly source code in those fields and it will automatically be converted to hex during installation. '
			'\nComments preceded with "#" will be ignored.'), wraplength=480 ).grid( column=0, row=0, padx=40 )

		# Create the header row
		headersRow = Frame( self.window )
		Label( headersRow, text='ASM' ).grid( row=0, column=0, sticky='w' )
		self.lengthString = StringVar()
		self.lengthString.set( '' )
		Label( headersRow, textvariable=self.lengthString ).grid( row=0, column=1 )
		Label( headersRow, text='HEX' ).grid( row=0, column=2, sticky='e' )
		headersRow.grid( column=0, row=1, padx=40, pady=(7, 0), sticky='ew' )

		# Configure the header row, so it expands properly on window-resize
		headersRow.columnconfigure( 'all', weight=1 )

		# Create the text entry fields and center conversion buttons
		entryFieldsRow = Frame( self.window )
		self.sourceCodeEntry = ScrolledText( entryFieldsRow, width=30, height=20 )
		self.sourceCodeEntry.grid( rowspan=2, column=0, row=0, padx=5, pady=7, sticky='news' )
		ttk.Button( entryFieldsRow, text='->', command=self.asmToHexCode ).grid( column=1, row=0, pady=20, sticky='s' )
		ttk.Button( entryFieldsRow, text='<-', command=self.hexCodeToAsm ).grid( column=1, row=1, pady=20, sticky='n' )
		self.hexCodeEntry = ScrolledText( entryFieldsRow, width=30, height=20 )
		self.hexCodeEntry.grid( rowspan=2, column=2, row=0, padx=5, pady=7, sticky='news' )
		entryFieldsRow.grid( column=0, row=2, sticky='nsew' )
		
		# Configure the above columns, so that they expand proportionally upon window resizing
		entryFieldsRow.columnconfigure( 0, weight=6 )
		entryFieldsRow.columnconfigure( 1, weight=1 ) # Giving much less weight to this row, since it's just the buttons
		entryFieldsRow.columnconfigure( 2, weight=6 )
		entryFieldsRow.rowconfigure( 'all', weight=1 )

		# Determine the include paths to be used here, and add a button at the bottom of the window to display them
		self.detectContext()
		ttk.Button( self.window, text='View Include Paths', command=self.viewIncludePaths ).grid( column=0, row=3, pady=(2, 6), ipadx=20 )

		# Add the assembly time display
		#self.assemblyTime = StringVar()
		#Label( self.window, textvariable=self.assemblyTime ).grid( column=0, row=3, sticky='w', padx=(7, 0) )
		self.assemblyTimeDisplay = Tkinter.Entry( self.window, width=25, borderwidth=0 )
		self.assemblyTimeDisplay.configure( state="readonly" )
		self.assemblyTimeDisplay.grid( column=0, row=3, sticky='w', padx=(7, 0) )

		# Configure this window's expansion as a whole, so that only the text entry row can expand when the window is resized
		self.window.columnconfigure( 0, weight=1 )
		self.window.rowconfigure( 0, weight=0 )
		self.window.rowconfigure( 1, weight=0 )
		self.window.rowconfigure( 2, weight=1 )
		self.window.rowconfigure( 3, weight=0 )

	def updateAssemblyDisplay( self, textInput ):
		self.assemblyTimeDisplay.configure( state="normal" )
		self.assemblyTimeDisplay.delete( 0, 'end' )
		self.assemblyTimeDisplay.insert( 0, textInput )
		self.assemblyTimeDisplay.configure( state="readonly" )

	def asmToHexCode( self ):
		# Clear the current hex code field, and assembly time display
		self.hexCodeEntry.delete( '1.0', 'end' )
		#self.assemblyTimeDisplay.delete( 0, 'end' )
		self.updateAssemblyDisplay( '' )

		# Get the ASM to convert
		asmCode = self.sourceCodeEntry.get( '1.0', 'end' )

		# Assemble the code (this will also handle showing any warnings/errors to the user)
		tic = time.clock()
		returnCode, hexCode = customCodeProcessor.preAssembleRawCode( asmCode, self.includePaths, discardWhitespace=False )
		toc = time.clock()

		if returnCode != 0:
			self.lengthString.set( 'Length: ' )
			#self.assemblyTime.set( '' )
			return

		hexCode = hexCode.replace( '|S|', '' ) # Removes special branch syntax separators

		# Insert the new hex code
		self.hexCodeEntry.insert( 'end', hexCode )

		# Update the code length display
		codeLength = getCustomCodeLength( hexCode, preProcess=True, includePaths=self.includePaths ) # requires pre-processing to remove whitespace
		self.lengthString.set( 'Length: ' + uHex(codeLength) )

		# Update the assembly time display with appropriate units
		assemblyTime = round( toc - tic, 9 )
		if assemblyTime > 1:
			units = 's' # In seconds
		else:
			assemblyTime = assemblyTime * 1000
			if assemblyTime > 1:
				units = 'ms' # In milliseconds
			else:
				assemblyTime = assemblyTime * 1000
				units = 'us' # In microseconds
		#self.assemblyTime.set( 'Assembly Time:  {} us'.format(assemblyTime) ) # In microseconds
		#self.assemblyTimeDisplay.insert( 0, 'Assembly Time:  {} {}'.format(assemblyTime, units) )
		self.updateAssemblyDisplay( 'Assembly Time:  {} {}'.format(assemblyTime, units) )

	def hexCodeToAsm( self ):
		# Delete the current assembly code, and clear the assembly time label
		self.sourceCodeEntry.delete( '1.0', 'end' )
		#self.assemblyTime.set( '' )
		#self.assemblyTimeDisplay.delete( 0, 'end' )
		self.updateAssemblyDisplay( '' )

		# Get the HEX code to disassemble
		hexCode = self.hexCodeEntry.get( '1.0', 'end' )
		
		# Disassemble the code into assembly
		returnCode, asmCode = customCodeProcessor.preDisassembleRawCode( hexCode, discardWhitespace=False )

		if returnCode != 0:
			self.lengthString.set( 'Length: ' )
			return

		# Replace the current assembly code
		self.sourceCodeEntry.insert( 'end', asmCode )

		# Update the code length display
		codeLength = getCustomCodeLength( hexCode, preProcess=True, includePaths=self.includePaths )
		self.lengthString.set( 'Length: ' + uHex(codeLength) )

	def detectContext( self ):

		""" This window should use the same .include context for whatever mod it was opened alongside;
			i.e. whatever tab is selected in the Mod Construction tab. If an associated mod is not found,
			fall back on the default import directories. """

		self.includePaths = []
		self.contextModName = ''

		# Check if we're even within the Mod Construction interface
		currentMainTabSelected = root.nametowidget( mainNotebook.select() )
		if currentMainTabSelected != constructionTab: pass

		# Check if there are any mods currently loaded in the Mod Construction interface
		elif not constructionNotebook.tabs(): pass

		else:
			# Get the mod constructor object for the currently selected mod
			modConstructor = root.nametowidget( constructionNotebook.select() ).winfo_children()[0]

			# Check that this is a mod that's saved somewhere in the library, and get the mod name
			if modConstructor.sourceFile:
				self.includePaths = modConstructor.includePaths
				self.contextModName = modConstructor.getInput( modConstructor.titleEntry ) # Safer than using titleEntry.get() because of undo states

		if not self.includePaths:
			self.includePaths = [ os.path.join( getModsFolderPath(), '.include' ), os.path.join(scriptHomeFolder, '.include') ]

	def viewIncludePaths( self ):
		# Build the message to show the user
		cwd = os.getcwd() + '      <- Current Working Directory'

		if self.contextModName:
			contextMessage = '\n\nAssembly context (for ".include" file imports) has the following priority:\n\n{}\n\n    [Based on "{}"]'.format( '\n'.join([cwd]+self.includePaths), self.contextModName )
		else:
			contextMessage = '\n\nAssembly context (for ".include" file imports) has the following priority:\n\n{}\n\n    [Default paths]'.format( '\n'.join([cwd]+self.includePaths) )

		cmsg( contextMessage, 'Include Paths', 'left' )


																		 #=================================#
																		# ~ ~ Default Game Settings tab ~ ~ #
																		 #=================================#

def openStageSelectionWindow():
	if root.stageSelectionsWindow: root.stageSelectionsWindow.window.deiconify()
	else: root.stageSelectionsWindow = stageSelectWindow()

	playSound( 'menuChange' )


class stageSelectWindow( object ):

	def __init__( self ):
		# Create the window, and set the title and framing
		self.window = Toplevel()
		self.window.title( "    Random Stage Selection" )
		self.window.attributes( '-toolwindow', 1 ) # Makes window framing small, like a toolbox/widget.

		# Calculate the spawning position of the window
		rootDistanceFromScreenLeft, rootDistanceFromScreenTop = getWindowGeometry( root )[2:]
		self.window.geometry( '+' + str(rootDistanceFromScreenLeft + 140) + '+' + str(rootDistanceFromScreenTop + 100) )

		# These stages are listed in the bit order that the game uses to read whether they are enabled for random select. (29 total)
		stageList = [ 'Kongo Jungle N64', "Yoshi's Island N64", 'Dream Land N64', 'Final Destination', 'Battlefield', 'Flat Zone', 
				'Mushroom Kingdom II', 'Fourside', 'Big Blue', 'Poké Floats', 'Venom', 'Green Greens', "Yoshi's Island", 'Brinstar Depths', 
				'Temple', 'Jungle Japes', 'Rainbow Cruise', 'Mushroom Kingdom', 'Icicle Mountain', 'Onett', 'Mute City', 'Pokemon Stadium', 
				'Corneria', 'Fountain of Dreams', "Yoshi's Story", 'Brinstar', 'Great Bay', 'Kongo Jungle', "Peach's Castle" ]

		# Read the stage data for what is currently set in the DOL
		bitString = bin( int(currentGameSettingsValues['stageToggleSetting'].get(), 16) )[2:].zfill(32)

		# Create a 6x5 grid and populate it with the stages above.
		stageFrame = Frame( self.window, padx=7, pady=7, borderwidth=3, relief='groove' )
		column = 0
		for i, stage in enumerate( stageList ):
			row = ( i / 6 ) + 1
			
			newWidget = Label( stageFrame, text=stage, width=18, height=2 )
			newWidget.grid( row=row, column=column, padx=2, pady=3 )
			newWidget.state = 'disabled'
			newWidget.revertTo = ''

			if bitString[i+3] == '1': self.setState( 'enabled', newWidget )
			newWidget.bind("<Button-1>", self.stageClicked )

			column = column + 1
			if column == 6: column = 0

		# Add the confirmation buttons.
		Button( stageFrame, text='Select All', command=lambda: self.updateStates( 'FFFFFFFF', False, True ) ).grid( row=6, column=0, padx=2, pady=3 )
		Button( stageFrame, text='Deselect All', command=lambda: self.updateStates( '00000000', False, True ) ).grid( row=6, column=1, padx=2, pady=3 )
		Button( stageFrame, text='Set to Tourney Legal', command=lambda: self.updateStates( 'E70000B0', False, True ) ).grid( row=6, column=2, padx=2, pady=3 )
		ttk.Button( stageFrame, text='Cancel', command=self.cancel ).grid( row=6, column=4, padx=2, pady=3 )
		self.window.protocol( 'WM_DELETE_WINDOW', self.cancel ) # Overrides the 'X' close button.
		ttk.Button( stageFrame, text='OK', command=self.confirm ).grid( row=6, column=5, padx=2, pady=3 )

		self.window.protocol( 'WM_DELETE_WINDOW', self.cancel ) # Overrides the 'X' close button.
		stageFrame.pack( padx=4, pady=4 )

	def updateStates( self, hexString, readingFromDOL, playAudio ): # Sets all stage label/buttons on the Stage Selection Window
		bitString = bin( int( hexString, 16) )[2:].zfill(32)[3:] # Omits first 3 bits.
		mainFrameChildren = self.window.winfo_children()[0].winfo_children()
		if self.window.state() == 'normal': windowOpen = True
		else: windowOpen = False

		for i, bit in enumerate( bitString ):
			widget = mainFrameChildren[i]

			if readingFromDOL: # This input is what's actually read from the DOL; so this will be a 'hard' set (no pending status)
				if bit == '1': self.setState( 'enabled', widget )
				else: self.setState( 'disabled', widget )
				widget.revertTo = ''

			else: # The input is from some button selection; these settings will be pending a save operation (or reverting a previous selection).
				if windowOpen: # Since this update is not a reflection of what's in the DOL, we want it to be cancelable.
					widget.revertTo = widget.state # This is used for the cancel and 'X' close buttons to revert changes.
				else: widget.revertTo = '' # The window is closed. This should be cleared so that opening and then closing/canceling doesn't undo this update.

				if bit == '1':
					if widget.state == 'pendingDisable': self.setState( 'enabled', widget )
					elif widget.state == 'disabled': self.setState( 'pendingEnable', widget )
				else:
					if widget.state == 'pendingEnable': self.setState( 'disabled', widget )
					elif widget.state == 'enabled': self.setState( 'pendingDisable', widget )

		if playAudio: playSound( 'menuChange' )

	def setState( self, state, widget ): # Sets a single specific stage label/button on the window
		if state == 'pendingEnable':
			stateColor = '#aaffaa'		# light green
		elif state == 'pendingDisable':
			stateColor = '#ee9999'		# light red
		elif state == 'enabled':
			stateColor = '#77cc77'		# solid green
		else: # i.e. 'disabled'
			stateColor = 'SystemButtonFace' # The default (disabled) color for label backgrounds

		widget['bg'] = stateColor
		widget.state = state

	def stageClicked( self, event ):
		widget = event.widget
		widget.revertTo = widget.state # This is used for the cancel and 'X' close buttons to revert changes.

		if widget.state != 'unavailable':
			if widget.state == 'pendingEnable': state = 'disabled'
			elif widget.state == 'pendingDisable': state = 'enabled'
			elif widget.state == 'enabled': state = 'pendingDisable'
			elif widget.state == 'disabled': state = 'pendingEnable'
			else: state = 'disabled' # Failsafe reset.
			
			self.setState( state, widget )
			checkForPendingChanges()
			
			playSound( 'menuChange' )

	def cancel( self ): # Undo any state changes made to the label widgets, and then close the window.
		# Iterate over each label, revert any changes it had, reset its revertTo property, and close the window.
		for widget in self.window.winfo_children()[0].winfo_children()[:29]:
			if widget.revertTo != '': 
				self.setState( widget.revertTo, widget )
				widget.revertTo = ''

		playSound( 'menuBack' )
		self.window.withdraw()

	def confirm( self ):
		# Rebuild the bit string and convert it to hex.
		stageBitStr = '111'
		for stage in self.window.winfo_children()[0].winfo_children()[:29]: # Iterate throught the first 29 widgets, all of which are stage Labels.
			if stage.state == 'pendingEnable' or stage.state == 'enabled': stageBitStr += '1'
			else: stageBitStr += '0'
			stage.revertTo = ''

		# Convert to int with a base of 2, then convert to hex, padded with 0s to 8 characters (albeit the value should never need padding).
		hexString = toHex( int(stageBitStr, 2), 8 )
		currentGameSettingsValues['stageToggleSetting'].set( hexString )
		
		updateDefaultGameSettingWidget( 'stageToggleControl', hexString ) # Updates the appearance of the button for opening this window
		self.window.withdraw()


def openItemSelectionsWindow():
	if root.itemSelectionsWindow: root.itemSelectionsWindow.window.deiconify()
	else: root.itemSelectionsWindow = itemSelectWindow()

	playSound( 'menuChange' )


class itemSelectWindow( object ):

	def __init__( self ):
		# Create the window, and set the title and framing
		self.window = Toplevel()
		self.window.title("    Item Switch")
		self.window.attributes('-toolwindow', 1) # Makes window framing small, like a toolbox/widget.

		# Calculate the spawning position of the window
		rootDistanceFromScreenLeft, rootDistanceFromScreenTop = getWindowGeometry( root )[2:]
		self.window.geometry( '+' + str(rootDistanceFromScreenLeft + 340) + '+' + str(rootDistanceFromScreenTop + 270) )

		# Items listed in the bit order that the game uses to read whether they are enabled for random select. (31 total)
		# The 4th bit (position 3 if counting from 0) is actually nothing? It has no effect on the Item Switch Screen.
		# With first bit on, the previous 4 bytes turn to FFFFFFFF?
		itemList = ['Poison Mushroom', 'Warp Star', 'Barrel Cannon', '???', # Confirmed
					'Beam Sword', 'Starman', 'Screw Attack', 'Super Scope', # Confirmed
					'Star Rod', 'Bunny Hood', 'Red Shell', 'Parasol', 
					'Cloaking Device', 'Maxim Tomato', 'Motion-Sensor Bomb', 'Metal Box',
					'Poke ball', "Lip's Stick", 'Ray Gun', 'Party Ball', 
					'Super Mushroom', 'Heart Container', 'Fan', 'Hammer', 
					'Green Shell', 'Freezie', 'Food', 'Flipper', 
					'Fire Flower', 'Mr. Saturn', 'Home-Run Bat', 'Bob-omb']	# Last 3 confirmed

		# Read the data for what is currently selected.
		itemBitStr = bin( int(currentGameSettingsValues['itemToggleSetting'].get(), 16) )[2:].zfill( 32 )

		# Create a 6x5 grid and populate it with the items above.
		itemFrame = Frame(self.window, padx=7, pady=7, borderwidth=3, relief='groove')
		column = 0
		for i, item in enumerate(itemList):
			row = ( i / 6 ) + 1
			
			newWidget = Label(itemFrame, text=item, width=18, height=2)
			newWidget.grid(row=row, column=column, padx=2, pady=3)
			newWidget.state = 'disabled'
			newWidget.revertTo = ''
			if itemBitStr[i] == '1': self.setState( 'enabled', newWidget )
			newWidget.bind( "<Button-1>", self.itemClicked )
			column =  column + 1
			if column == 6: column = 0

		# Add the confirmation buttons.
		Button( itemFrame, text='Select All', command=lambda: self.updateStates( 'FFFFFFFF', False, True ) ).grid( row=7, column=0, padx=2, pady=3 )
		Button( itemFrame, text='Deselect All', command=lambda: self.updateStates( '00000000', False, True ) ).grid( row=7, column=1, padx=2, pady=3 )
		cellFrame = Frame( itemFrame )
		Label( cellFrame, text='Item Frequency:  ' ).pack( side='left' )
		itemFrequencyMimic.set( currentGameSettingsValues['itemFrequencySetting'].get() )
		itemFrequencyDisplay = OptionMenu(cellFrame, itemFrequencyMimic, 'None', 'Very Low', 'Low', 'Medium', 'High', 'Very High', 'Extremely High',
			command=lambda(value): self.reflectItemFrequencyChanges( itemFrequencyDisplay, value ))
		cellFrame.grid( row=7, column=2, columnspan=2 )
		itemFrequencyDisplay.revertTo = ''
		itemFrequencyDisplay.pack( side='left' )
		ttk.Button( itemFrame, text='Cancel', command=self.cancel ).grid( row=7, column=4, padx=2, pady=3 )
		ttk.Button( itemFrame, text='OK', command=self.confirm ).grid( row=7, column=5, padx=2, pady=3 )

		self.window.protocol( 'WM_DELETE_WINDOW', self.cancel ) # Overrides the 'X' close button.
		itemFrame.pack( padx=4, pady=4 )

	def updateStates( self, hexString, readingFromDOL, playAudio ): # Sets all stage label/buttons on the Stage Selection Window
		bitString = bin( int( hexString, 16) )[2:].zfill(32)
		mainFrameChildren = self.window.winfo_children()[0].winfo_children()
		if self.window.state() == 'normal': windowOpen = True
		else: windowOpen = False

		for i, bit in enumerate( bitString ):
			widget = mainFrameChildren[i]

			if readingFromDOL: # This input is what's actually read from the DOL; so this will be a 'hard' set (no pending status)
				if bit == '1': self.setState( 'enabled', widget )
				else: self.setState( 'disabled', widget )
				widget.revertTo = ''

			else: # The input is from some button selection; these settings will be pending a save operation (or reverting a previous selection).
				if windowOpen: # Since this update is not a reflection of what's in the DOL, we want it to be cancelable.
					widget.revertTo = widget.state # This is used for the cancel and 'X' close buttons to revert changes.
				else: widget.revertTo = '' # The window is closed. This should be cleared so that opening and then closing/canceling doesn't undo this update.

				if bit == '1':
					if widget.state == 'pendingDisable': self.setState( 'enabled', widget )
					elif widget.state == 'disabled': self.setState( 'pendingEnable', widget )
				else:
					if widget.state == 'pendingEnable': self.setState( 'disabled', widget )
					elif widget.state == 'enabled': self.setState( 'pendingDisable', widget )

		if playAudio: playSound( 'menuChange' )

	def setState( self, state, widget ): # Sets a single specific stage label/button on the window
		 # Sets a single specific stage label/button on the window
		if state == 'pendingEnable':
			stateColor = '#aaffaa'		# light green
		elif state == 'pendingDisable':
			stateColor = '#ee9999'		# light red
		elif state == 'enabled':
			stateColor = '#77cc77'		# solid green
		else: # i.e. 'disabled'
			stateColor = 'SystemButtonFace' # The default (disabled) color for label backgrounds

		widget['bg'] = stateColor
		widget.state = state

	def itemClicked( self, event ):
		widget = event.widget
		widget.revertTo = widget.state # This is used for the cancel and 'X' close buttons to revert changes.

		if widget.state != 'unavailable':
			if widget.state == 'pendingEnable': state = 'disabled'
			elif widget.state == 'pendingDisable': state = 'enabled'
			elif widget.state == 'enabled': state = 'pendingDisable'
			elif widget.state == 'disabled': state = 'pendingEnable'
			else: state = 'disabled' # Failsafe reset.
			
			self.setState( state, widget )
			checkForPendingChanges()
			playSound( 'menuChange' )

	def cancel( self ): # Undo any state changes made to the label widgets, and then close the window.
		# Iterate over each label, revert any changes it had, reset its revertTo property, and close the window.
		for widget in self.window.winfo_children()[0].winfo_children()[:32]:
			if widget.revertTo != '':
				self.setState( widget.revertTo, widget )
				widget.revertTo = ''

		playSound( 'menuBack' )
		self.window.withdraw()

	def confirm( self ):
		# Rebuild the bit string and convert it to hex.
		itemBitStr = ''
		for item in self.window.winfo_children()[0].winfo_children()[:32]: # Iterate throught the first 32 widgets, all of which are item Labels.
			if item.state == 'pendingEnable' or item.state == 'enabled': itemBitStr += '1'
			else: itemBitStr += '0'
			item.revertTo = ''

		# Convert to int using a base of 2, then convert to hex, padded with 0s to 8 characters (albeit the value should never need padding).
		newValue = toHex( int(itemBitStr,2), 8 )
		currentGameSettingsValues['itemToggleSetting'].set( newValue )
		currentGameSettingsValues['itemFrequencySetting'].set( itemFrequencyMimic.get() )
		
		updateDefaultGameSettingWidget( 'itemToggleControl', newValue )
		self.window.withdraw()

	def reflectItemFrequencyChanges( self, itemFrequencyDisplay, value ):
		itemFrequencyDisplay.revertTo = currentGameSettingsValues['itemFrequencySetting'].get()
		updateDefaultGameSettingWidget( 'itemFrequencyDisplay', value )


class rumbleSelectWindow( object ):

	def __init__( self ):
		if root.rumbleSelectionWindow: root.rumbleSelectionWindow.deiconify()
		else:
			rumbleSelectionWindow = Toplevel()
			rumbleSelectionWindow.title( "    Rumble Selection" )
			rumbleSelectionWindow.attributes( '-toolwindow', 1 ) # Makes window framing small, like a toolbox/widget.
			root.rumbleSelectionWindow = rumbleSelectionWindow
			rumbleSelectionWindow.buttons = {} # Used by the updateDefaultGameSettingWidget function

			# Calculate the spawning position of the window
			rootDistanceFromScreenLeft, rootDistanceFromScreenTop = getWindowGeometry( root )[2:]
			rumbleSelectionWindow.geometry( '+' + str(rootDistanceFromScreenLeft + 240) + '+' + str(rootDistanceFromScreenTop + 170) )

			for player in ( '1', '2', '3', '4' ):
				# Create the On/Off toggle button
				button = ttk.Button( rumbleSelectionWindow, textvariable=currentGameSettingsValues['p'+player+'RumbleSetting'], command=lambda p=player: self.toggleRumble(p) )
				rumbleSelectionWindow.buttons['p'+player+'RumbleControl'] = button
				button.player = player
				button.grid( column=player, row=0, padx=3, pady=8 )

				# Add a P1/P2/etc image below the button
				try:
					ttk.Label( rumbleSelectionWindow, image=imageBank['p'+player+'Indicator'] ).grid( column=player, row=1, padx=7, pady=(0, 8) )
				except:
					print 'Unable to load the p'+player+'Indicator image.'
					pass

			rumbleSelectionWindow.protocol( 'WM_DELETE_WINDOW', self.close ) # Overrides the 'X' close button.

		playSound( 'menuChange' )

	def toggleRumble( self, player ):
		# Get the respective StringVar
		var = currentGameSettingsValues['p'+player+'RumbleSetting']

		if var.get() == 'Off': var.set( 'On' )
		else: var.set( 'Off' )

		print 'updating to', var.get()

		updateDefaultGameSettingWidget( 'p'+player+'RumbleControl', var.get() )

	def close( self ):
		playSound( 'menuBack' )
		root.rumbleSelectionWindow.withdraw()


def onUpdateDefaultGameSettingsOnlyToggle():
	# Disable/Enable the Mods Library tab
	if onlyUpdateGameSettings.get(): mainNotebook.tab( 0, state='disabled' )
	else: 
		mainNotebook.tab( 0, state='normal' )
		root.update() # Force an update to the GUI, to reflect that the checkbox has been pressed before starting the library scan
		scanModsLibrary( playAudio=False )

	playSound( 'menuChange' )

	# Save this setting
	settings.set( 'General Settings', 'onlyUpdateGameSettings', str(onlyUpdateGameSettings.get()) )
	saveOptions()

																 #========================================#
																# ~ ~ Tools Tab and other calculations ~ ~ #
																 #========================================#

# Avert yer eyes! todo: write better functions
def floatToHex( input ): return '0x' + hex( struct.unpack('<I', struct.pack('<f', Decimal(input)))[0] )[2:].upper()

def doubleToHex( input ): return '0x' + hex( struct.unpack('<Q', struct.pack('<d', Decimal(input)))[0] ).replace('L', '')[2:].upper()


def convertDec( event, textvariable ):
	decimalFieldInput = ''.join( textvariable.get().split() ) # Removes whitespace

	if not isNaN( decimalFieldInput ):
		if float( decimalFieldInput ).is_integer(): 
			hexNum.set( '0x' + hex(int(Decimal(decimalFieldInput)))[2:].upper() )
		else: hexNum.set( 'n/a (not an integer)' )
		floatNum.set( floatToHex( decimalFieldInput ).replace('L', '') )
		doubleNum.set( doubleToHex( decimalFieldInput ) )
	else:
		hexNum.set('')
		floatNum.set('')
		doubleNum.set('')


def convertHex( event, textvariable ):
	hexFieldInput = ''.join( textvariable.get().replace('0x', '').split() ) # Removes whitespace

	if validHex( hexFieldInput ):
		intFieldInput = int( hexFieldInput, 16 )

		decimalNum.set( intFieldInput )
		floatNum.set( floatToHex(intFieldInput) )
		doubleNum.set( doubleToHex(intFieldInput) )
	else:
		decimalNum.set('')
		floatNum.set('')
		doubleNum.set('')


def convertFloat( event, textvariable ):
	input = ''.join( textvariable.get().replace('0x', '').split() ) # Removes whitespace

	if validHex( input ) and len( input ) == 8:
		decFloat = struct.unpack('>f', input.decode('hex'))[0]
		decimalNum.set( decFloat )
		if float(decFloat).is_integer(): hexNum.set( '0x' + hex(int(Decimal(decFloat)))[2:].upper() )
		else: hexNum.set( 'n/a (not an integer)' )
		doubleNum.set( doubleToHex( decFloat ) )
	else:
		decimalNum.set('')
		hexNum.set('')
		doubleNum.set('')


def convertDouble( event, textvariable ):
	input = ''.join( textvariable.get().replace('0x', '').split() ) # Removes whitespace

	if validHex( input ) and len( input ) == 16:
		decFloat = struct.unpack('>d', input.decode('hex'))[0]
		decimalNum.set( decFloat )
		if float(decFloat).is_integer(): hexNum.set( '0x' + hex(int(Decimal(decFloat)))[2:].upper() )
		else: hexNum.set( 'n/a (not an integer)' )
		floatNum.set( floatToHex( decFloat ).replace('L', '') )
	else:
		decimalNum.set('')
		hexNum.set('')
		floatNum.set('')


def offsetInRAM( dolOffset, sectionInfo ): # todo: write into dolInitializer method

	""" Converts the given DOL offset to the equivalent location in RAM once the DOL file is loaded. """

	ramAddress = -1

	# Determine which section the DOL offset is in, and then get that section's starting offsets in both the dol and RAM.
	for section in sectionInfo.values():
		if dolOffset >= section[0] and dolOffset < (section[0] + section[2]):
			sectionOffset = dolOffset - section[0] # Get the offset from the start of the DOL section.
			ramAddress = section[1] + sectionOffset # Add the section offset to the RAM's start point for that section.
			break

	return ramAddress


def offsetInDOL( ramOffset, sectionInfo ): # todo: write into dolInitializer method

	""" Converts the given integer RAM address (location in memory) to the equivalent DOL file integer offset. 
		ramOffset should already be relative to the base address (-0x80000000). """

	dolOffset = -1

	# Determine which section the address belongs in, and then get that section's starting offsets.
	for section in sectionInfo.values():
		if ramOffset >= section[1] and ramOffset < (section[1] + section[2]):
			sectionOffset = ramOffset - section[1] # Get the offset from the start of the section.
			dolOffset = section[0] + sectionOffset # Add the section offset to the RAM's start point for that section.
			break

	return dolOffset


def normalizeDolOffset( offsetString, dolObj=None, returnType='int' ):

	""" Converts a hex offset string to an int, and converts it to a DOL offset if it's a RAM address. 
		dolObj is an instance of the 'dol' class, representing a DOL file and its extrapolated properties. """

	# Use the default/global DOL if one is not specified.
	if not dolObj: dolObj = dol

	offsetString = offsetString.replace( '0x', '' ).strip()
	problemDetails = ''
	dolOffset = -1

	if len( offsetString ) == 8 and offsetString.startswith( '8' ): # Looks like it's a RAM address; convert it to a DOL offset int
		offset = int( offsetString[1:], 16 )
		if offset >= 0x3100:
			if offset < dolObj.maxRamAddress: 
				dolOffset = offsetInDOL( offset, dolObj.sectionInfo )
				
				# Check that the offset was found (it's possible the address is between text/data sections)
				if dolOffset == -1:
					problemDetails = ', because the RAM address does not have an equivalent location in the DOL.'
			else: problemDetails = ', because the RAM address is too big.'
		else: problemDetails = ', because the RAM address is too small.'

		if returnType == 'string' and not problemDetails:
			dolOffset = uHex( dolOffset )
	else:
		if returnType == 'string': # Already in the desired format; no need for conversion
			dolOffset = '0x' + offsetString.upper()

		else:
			offset = int( offsetString, 16 )
			if offset >= 0x100:
				if offset < dolObj.maxDolOffset: dolOffset = offset
				else: problemDetails = ', because the DOL offset is too big.'
			else: problemDetails = ', because the DOL offset is too small.'

	if problemDetails:
		msg( 'Problem detected while processing the offset 0x' + offsetString + '; it could not be converted to a DOL offset' + problemDetails )

	return dolOffset


def normalizeRamAddress( offsetString, dolObj=None, returnType='int' ):

	""" Converts a hex offset string to an int, and converts it to a RAM address if it's a DOL offset. 
		dolObj is an instance of the 'dol' class, representing a DOL file and its extrapolated properties. """

	# Use the default/global DOL if one is not specified.
	if not dolObj: dolObj = dol

	offsetString = offsetString.replace( '0x', '' ).strip()
	problemDetails = ''
	ramAddress = -1

	if len( offsetString ) == 8 and offsetString.startswith( '8' ):
		if returnType == 'string': # Already in the desired format; no need for conversion
			ramAddress = '0x' + offsetString.upper()

		else:
			offset = int( offsetString[1:], 16 )
			if offset >= 0x3100:
				if offset < dolObj.maxRamAddress: ramAddress = offset
				else: problemDetails = ', because the RAM address is too big.'
			else: problemDetails = ', because the RAM address is too small.'

	else: # Looks like it's a DOL offset; convert it to a RAM address int
		offset = int( offsetString, 16 )
		if offset >= 0x100:
			if offset < dolObj.maxDolOffset: ramAddress = offsetInRAM( offset, dolObj.sectionInfo )
			else: problemDetails = ', because the DOL offset is too big.'
		else: problemDetails = ', because the DOL offset is too small.'

		if returnType == 'string' and not problemDetails:
			ramAddress = '0x8' + toHex( ramAddress, 7 )

	if problemDetails:
		msg( 'Problem detected while processing the offset, 0x' + offsetString + '; it could not be converted to a DOL offset' + problemDetails )

	return ramAddress


def calcBranchDistance( fromDOL, toDOL ):
	start = offsetInRAM( fromDOL, dol.sectionInfo )
	end = offsetInRAM( toDOL, dol.sectionInfo )

	if start == -1:
		msg( 'Invalid input for branch calculation: "from" value (' + hex(fromDOL) + ') is out of range.' )
		return -1
	elif end == -1:
		msg( 'Invalid input for branch calculation: "to" value (' + hex(toDOL) + ') is out of range.' ) #.\n\nTarget DOL Offset: ' + hex(toDOL) )
		return -1
	else:
		return end - start


def assembleBranch( branchInstruction, branchDistance ):
	branchInstruction = branchInstruction.lower().strip() # Normalize to lower-case without whitespace
	useAssembler = False

	# Determine whether the branch instruction is known (and set required flags) or if it needs to be sent to pyiiasmh for evaluation.
	if branchInstruction == 'b': pass
	elif branchInstruction == 'ba': # Interpret the address as absolute
		branchDistance += 2
	elif branchInstruction == 'bl': # Store the link register
		branchDistance += 1
	elif branchInstruction == 'bal' or branchInstruction == 'bla': # Interpret the address as absolute and store the link register
		branchDistance += 3
	else:
		useAssembler = True # Last resort, since this will take much longer

	if useAssembler:
		fullInstruction = branchInstruction + ' ' + str( branchDistance ) + '\n' # newLine char prevents an assembly error message.
		branch, errors = customCodeProcessor.assemble( fullInstruction )
		if errors or len( branch ) != 8:
			return '48000000' # Failsafe; so that dol data cannot be corrupted with non-hex data.
	else:
		# Return the hex for a hard (unconditional) branch (b/ba/bl/bla).
		if branchDistance >= 0: # Determine if the branch is going forward or backward in RAM.
			branch = '48' + toHex( branchDistance, 6 ) # Converts to hex and then pads to 6 characters
		else:
			branch = '4B' + toHex( (0x1000000 + branchDistance), 6 )

	return branch


def getBranchDistance( branchHex ):
	opCode = branchHex[:2].lower()

	def round_down( num, divisor ): # Rounds down to the closest multiple of the second argument.
		return num - ( num % divisor )

	branchDistance = round_down( int(branchHex[2:], 16), 4 ) # This will exclude the ba & bl flags.

	if opCode == '4b': branchDistance = -( 0x1000000 - branchDistance )

	return branchDistance


def getBranchTargetDolOffset( branchOffset, branchHex ):

	""" Calculates a target DOL offset for a given branch. """

	branchDistance = getBranchDistance( branchHex )
	ramOffset = offsetInRAM( branchOffset, dol.sectionInfo )

	return offsetInDOL( ramOffset + branchDistance, dol.sectionInfo )


def convertDolOffset( event, showLowerLimitErrors=False ):
	if event.keysym == 'Return':
		showLowerLimitErrors = True # The user is probably trying to trigger/force an update

	# Filter the input; remove all whitespace and the '0x' hex indicator
	userInput = ''.join( event.widget.get().replace( '0x', '' ).split() )
	if not userInput: return

	# Clear all entry fields, except for the one currently being used for input. And get the DOL revision that this is for
	revision = ''
	for widget in offsetConverter.winfo_children():
		if widget != event.widget and widget.winfo_class() == 'TEntry': widget.delete( 0, 'end' )
		elif widget == event.widget:
			revision = lastWidget['text'] # You may see a linting error here, but it's fine
		lastWidget = widget
	ramToDolNotes.set( '' )
	if not revision: # failsafe; shouldn't be possible
		msg( 'Unable to determine a revision for this offset conversion.' )
		return

	# Prelim validation
	if not validHex( userInput ):
		ramToDolNotes.set( 'Invalid hex' )
		return

	# Load the DOL for this revision (if one is not already loaded), so that its section info can be used to determine a respective RAM Address
	vanillaDol = loadVanillaDol( revision )

	# Convert the given hex string to a decimal integer, then convert it to a RAM Address and update the RAM Address text field.
	dolOffset = int( userInput, 16 )
	if dolOffset < 0x100: # Space in the DOL prior to this is the file's header, which is not loaded into RAM
		if showLowerLimitErrors: ramToDolNotes.set( 'Input too small' )
	elif dolOffset >= vanillaDol.maxDolOffset:
		ramToDolNotes.set( 'Input too big' )
	else:
		ramAddress = offsetInRAM( dolOffset, vanillaDol.sectionInfo )

		if ramAddress == -1: ramToDolNotes.set( 'Not Found' ) #offsetConverter.winfo_children()[1].insert( 0, 'Not found' )
		else: offsetConverter.winfo_children()[1].insert( 0, '0x8' + toHex( ramAddress, 7 ) )


def convertRamOffset( event, showLowerLimitErrors=False ):
	if event.keysym == 'Return': showLowerLimitErrors = True # User probably trying to trigger/force an update

	# Remove all whitespace and the '0x' hex indicator
	userInput = ''.join( event.widget.get().replace( '0x', '' ).split() )
	if not userInput: return

	# Clear all entry fields, except for the one currently being used for input
	for widget in offsetConverter.winfo_children():
		if widget != event.widget and widget.winfo_class() == 'TEntry': widget.delete( 0, 'end' )
	ramToDolNotes.set( '' )

	# Prelim validation
	if not validHex( userInput ):
		ramToDolNotes.set( 'Invalid hex' )
		return

	# Convert the given hex string to a decimal integer
	if len( userInput ) == 8 and userInput.startswith( '8' ): userInput = userInput[1:]
	ramAddress = int( userInput, 16 )

	# More validation; make sure the input is not too small
	if ramAddress < 0x3100: # Space in the DOL prior to this is the file's header, which is not loaded into RAM
		if showLowerLimitErrors: ramToDolNotes.set( 'Input too small' )
		return

	# Iterate over the DOL revisions shown, and update their offset text fields
	label = None
	revision = ''
	for widget in offsetConverter.winfo_children()[3:]:
		if widget.winfo_class() == 'TLabel':
			label = widget # Remembers the previous (label) widget when moving on to the next (entry) widget
		else: # Should be a TEntry
			revision = label['text']

			if not revision: # Failsafe
				widget.insert( 0, 'Revision N/A' )
				continue

			# Load the DOL for this revision (if one is not already loaded), so that its section info can be used to determine a respective RAM Address
			vanillaDol = loadVanillaDol( revision )

			if not vanillaDol: # Failsafe
				widget.insert( 0, 'vDOL N/A' )
				continue
			elif ramAddress >= vanillaDol.maxRamAddress:
				widget.insert( 0, 'Input too big' )
			else:
				dolOffset = offsetInDOL( ramAddress, vanillaDol.sectionInfo )

				if dolOffset == -1: widget.insert( 0, 'Not Found' ) #offsetConverter.winfo_children()[1].insert( 0, 'Not found' )
				else: widget.insert( 0, uHex( dolOffset ) )


def convertCodeOffset( event ):

	""" This takes the offset of some code in the DOL, and gets the offset for the same code 
		in the other DOL revisions. However, this function mostly handles I/O to the GUI, 
		while the convertOffsetToVersion() function below this performs the offset search. """

	# Remove all whitespace and the '0x' hex indicator
	userInput = ''.join( event.widget.get().replace( '0x', '' ).split() )
	if not userInput: return
	lsd = userInput[-1].lower() # Least Significant Digit

	def setAllOutputs( text ): # Not counting the widget being used as input as an output
		for widget in codeOffsetConverter.winfo_children():
			if widget.winfo_class() == 'TEntry' and widget != event.widget:
				widget.delete( 0, 'end' )
				widget.insert( 0, text )

	# Input validation; display 'Invalid hex' for the outputs
	if not validHex( userInput ): 
		setAllOutputs( 'Invalid hex' )
		return

	# Check the Least Significant Digit for 4-byte alignment
	elif not (lsd == '0' or lsd == '4' or lsd == '8' or lsd == 'c'):
		msg( 'The offset must be a multiple of 4 bytes (i.e. ends with 0, 4, 8, or C).', 'Offset out of bounds' )
		setAllOutputs( '' ) # Blank the outputs
		return

	else: 
		setAllOutputs( 'Searching....' ) # Temporary display
		root.update() # Allows the GUI to update before continuing

	# Determine whether the input offset is a RAM address
	if len( userInput ) == 8 and userInput.startswith( '8' ): ramAddressGiven = True
	else: ramAddressGiven = False

	# Load the DOL for the input's revision (if one is not already loaded), to check its section info in convertOffsetToVersion
	vanillaDol = loadVanillaDol( event.widget.revision )
	if not vanillaDol: # Failsafe; this dol should always exist if this revision entry field was created
		setAllOutputs( 'Error' )
		return

	# Iterate over the entry widgets
	for widget in codeOffsetConverter.winfo_children():
		if widget.winfo_class() == 'TEntry' and widget != event.widget: # Ignores the current/input entry
			revision = widget.revision
			widget.delete( 0, 'end' )

			# Load the DOL for this output's revision (if one is not already loaded), to check its section info and min/max offsets
			vanillaDol = loadVanillaDol( revision )

			if not vanillaDol: # Failsafe
				widget.insert( 0, 'vDOL N/A' )
				continue

			# Convert the value to an integer DOL offset, even if it's a ram address
			offset = normalizeDolOffset( userInput, dolObj=vanillaDol )

			# Make sure the offset is not out of range of the DOL's sections
			if offset < 0x100:
				widget.insert( 0, 'Input too small' )
				continue
			elif offset >= vanillaDol.maxDolOffset:
				widget.insert( 0, 'Input too big' )
				continue

			# Perform the search for equivalent code between the input and output revisions
			matchingOffset = convertOffsetToVersion( offset, event.widget.revision, revision )

			# Output the result
			if matchingOffset == -1: widget.insert( 0, 'Not Found' )
			elif ramAddressGiven: # Convert back to a RAM address
				ramAddress = offsetInRAM( matchingOffset, vanillaDol.sectionInfo )
				widget.insert( 0, '0x8' + toHex( ramAddress, 7 ) )
			else: widget.insert( 0, uHex(matchingOffset) )

			root.update() # Allows the GUI to update before continuing


def convertOffsetToVersion( offset, sourceVer, targetVer ):

	""" This function matches code at a given offset to code in another [target] DOL, to find the offset of the code in the target. 
		This is done by creating a map of opcodes before and after the target offset, which is grown on each search iteration, until 
		until only one match is found between the source and target DOL sections.
		It's assumed that the target code/offset will be in the same section for all game versions. """

	# Vanilla DOLs for the revisions being compared should already be loaded into memory.
	sourceSectionInfo = originalDols[sourceVer].sectionInfo
	targetSectionInfo = originalDols[targetVer].sectionInfo

	# Get DOL data for the source DOL section
	sourceDolSection = ''
	sectionOffset = 0
	for dolOffsetStart, _, sectionSize in sourceSectionInfo.values():
		if offset >= dolOffsetStart and offset < (dolOffsetStart + sectionSize):
			sectionOffset = offset - dolOffsetStart # The offset between the start of the section and the given input offset
			sourceDolSection = originalDols[sourceVer].data[dolOffsetStart*2:(dolOffsetStart+sectionSize)*2]
			break

	# Get DOL data for the target DOL section
	targetDolSection = ''
	for dolOffsetStart, _, sectionSize in targetSectionInfo.values():
		if offset >= dolOffsetStart and offset < (dolOffsetStart + sectionSize):
			targetDolSection = originalDols[targetVer].data[dolOffsetStart*2:(dolOffsetStart+sectionSize)*2]
			break

	def matchCodeSample( testPoints, dolSection, samples ):
		matchCount = 0
		endOfMatch = 0
		for nib in range( 0, len(dolSection), 8 ):
			for i, point in enumerate(testPoints):
				if dolSection[nib:nib+2] != point:
					break
				else:
					if i+1 == len(testPoints): # This would be the last iteration, meaning a full match was found.
						endOfMatch = nib
						matchCount = matchCount + 1
					else: nib = nib + 8
		if not settingsFile.quickSearch: samples = samples/2

		return ( matchCount, dolOffsetStart + endOfMatch/2 - samples*4 ) # Second return value is the file offset for the last match.

	# Using the data section from the source file, find a unique code pattern centered at the given offset.
	samples = 0
	sourceMatchCount = 0
	targetMatchCount = 0
	testPoints = [ sourceDolSection[sectionOffset*2:sectionOffset*2+2] ] # This will be a map of test points, composed of command bytes.
	while sourceMatchCount != 1 or targetMatchCount != 1:
		samples = samples + 1

		if settingsFile.quickSearch: # Add a command byte test point both before and after the target command
			leadingPoint = sectionOffset*2 - samples*8
			trailingPoint = sectionOffset*2 + samples*8

			if leadingPoint >= 0: testPoints.insert( 0, sourceDolSection[leadingPoint:leadingPoint+2] )
			testPoints.append( sourceDolSection[trailingPoint:trailingPoint+2] )

		else: # For each match iteration (attempt at finding a unique code match), alternate between adding just one test point to the map at the front or back
			if isEven( samples ): 
				trailingPoint = sectionOffset*2 + (samples - samples/2)*8 # Add a test point to the end of the map
				testPoints.append( sourceDolSection[trailingPoint:trailingPoint+2] )
			else:
				leadingPoint = sectionOffset*2 - (samples - samples/2)*8 # Add a test point to the beginning of the map
				if leadingPoint >= 0: testPoints.insert( 0, sourceDolSection[leadingPoint:leadingPoint+2] )

		( sourceMatchCount, _ ) = matchCodeSample( testPoints, sourceDolSection, samples )

		( targetMatchCount, targetOffset ) = matchCodeSample( testPoints, targetDolSection, samples )

		# msg('found ' + str(testPoints) + ', \n' + str(sourceMatchCount) + ' times in the source, and ' + str(targetMatchCount) + \
		# 	' times in the target.\n\nFound in section ' + dolSection + ' at ' + hex(offset) + ', with a sample extension of ' + str(samples))

		if sourceMatchCount == 0 or targetMatchCount == 0: break # or samples > 200: break # Early exit if no match is found, plus a failsafe.

	if sourceMatchCount != 1 or targetMatchCount != 1:
		offset = -1
	else:
		offset = targetOffset

	# msg('offset: ' + hex(offset) + ', sourceVer: ' + sourceVer + ', targetVer: ' + targetVer + '\n\n' +
	# 	'found ' + str(testPoints) + ', \n' + str(sourceMatchCount) + ' times in the source, and ' + str(targetMatchCount) + \
	# 	' times in the target.\n\nFound in section ' + dolSection + ' at 0x' + hex(offset) + ', with a sample extension of ' + str(samples))

	return offset


def text2hexConv( event ):
	if event.widget == text2hex: # This is the ASCII text input field; need to convert the given text string to hex
		hex2text.delete( '1.0', 'end' ) # Delete current contents of the hex input field
		textInput = text2hex.get('1.0', 'end')[:-1]

		try:
			hex2text.insert( '1.0', textInput.encode('hex') )
		except: pass

	else:
		hexInput = ''.join( hex2text.get( '1.0', 'end' ).split() ) # Removes whitespace

		if validHex( hexInput ):
			# Only process the string if the number of characters is even (but don't erase the resulting string othewise).
			if isEven( len(hexInput) ):
				text2hex.delete( '1.0', 'end' )
				text2hex.insert( '1.0', hexInput.decode('hex') )
		else:
			text2hex.delete( '1.0', 'end' )


def menuText2hexConv( event ):
	if event.widget == menuText2hex: # This is the text input field; need to convert the given text string to hex
		hex2menuText.delete( '1.0', 'end' ) # Deletes the entire current contents

		# Encode!
		hexCodes = []
		for character in unicode( menuText2hex.get( '1.0', 'end' )[:-1] ):
			uniChar = character
			for key, value in settingsFile.menuTextDictionary.items():
				if value.decode( 'utf-8' ) == uniChar:
					hexCodes.append( key )
					break
			else: hexCodes.append( '__' + u'\ufffd' + '_' ) # basically: '__?_' using the "unknown" unicode character
		hex2menuText.insert( '1.0', ''.join(hexCodes) )

	else: # This is the hex input field; need to generate text
		hexInput = ''.join( hex2menuText.get( '1.0', 'end' ).split() ).lower() # Removes all whitespace

		if validHex( hexInput ):
			# Only process the string if the number of characters is even (but don't erase the resulting string othewise).
			if isEven( len(hexInput) ):
				menuText2hex.delete( '1.0', 'end' ) # Deletes the entire current contents

				# Decode!
				decodedCharacters = []
				position = 0
				currentByte = hexInput[:2]
				while currentByte:
					nextByte = hexInput[position+2:position+4]

					if currentByte in settingsFile.menuTextDictionary: 
						decodedCharacters.append( settingsFile.menuTextDictionary[currentByte] )
						position += 2
					elif nextByte and currentByte + nextByte in settingsFile.menuTextDictionary: 
						decodedCharacters.append( settingsFile.menuTextDictionary[currentByte + nextByte] )
						position += 4
					else: 
						decodedCharacters.append( u'\ufffd' )
						position += 2

					currentByte = hexInput[position:position+2]

				try:
					menuText2hex.insert( '1.0', ''.join(decodedCharacters) )
				except: pass
		else:
			menuText2hex.delete( '1.0', 'end' )


class CommandProcessor( object ):

	""" This is an assembler/disassembler to translate between assembly and bytecode (hex/binary machine code). 
		Uses the PowerPC Embedded Application Binary Interface (EABI) binary utilities. """

	# Build file paths to the binaries
	assemblerPath = scriptHomeFolder + '\\bin\\eabi\\powerpc-eabi-as.exe'
	linkerPath = scriptHomeFolder + '\\bin\\eabi\\powerpc-eabi-ld.exe'
	objcopyPath = scriptHomeFolder + '\\bin\\eabi\\powerpc-eabi-objcopy.exe'
	disassemblerPath = scriptHomeFolder + '\\bin\\eabi\\vdappc.exe'
	tempBinFile = ''

	def __init__( self ):
		# Construct paths for temporary files
		if not self.tempBinFile:
			tempFilesFolder = scriptHomeFolder + '\\bin\\tempFiles\\'
			self.tempBinFile = tempFilesFolder + 'code.bin' # Temp file for decompiling

			if not os.path.exists( tempFilesFolder ): createFolders( tempFilesFolder)

		# Validate the EABI file paths
		for path in ( self.assemblerPath, self.linkerPath, self.objcopyPath, self.disassemblerPath ):
			if not os.path.exists( path ):
				print 'Missing PowerPC-EABI binaries!'
				break

	@staticmethod
	def beautifyHex( rawHex ):
		code = []
		for block in xrange( 0, len(rawHex), 8 ):
			# Check whether this is the first or second block (set of 4 bytes or 8 nibbles)
			if block % 16 == 0: # Checks if evenly divisible by 16, meaning first block
				code.append( rawHex[block:block+8] + ' ' )
			else:
				code.append( rawHex[block:block+8] + '\n' )
		
		return ''.join( code ).rstrip()

	def assemble( self, asmCode, beautify=False, includePaths=None, suppressWarnings=False ): # IPC interface to EABI-AS

		args = [
				self.assemblerPath, 				# Path to the assembler binary
				"-mgekko", 							# Generate code for PowerPC Gekko (alternative to '-a32', '-mbig')
				"-mregnames", 						# Allows symbolic names for registers
				'-al', 								# Options for outputting assembled hex and other info to stdout
				'--listing-cont-lines', '100000',	# Sets the maximum number of continuation lines allowable in stdout (basically want this unlimited)
				#'--statistics',					# Prints additional assembly stats within the errors message; todo: will require some extra post processing
			]

		if suppressWarnings:
			args.append( '--no-warn' )

		# Set include directories, if requested
		if includePaths:
			for path in includePaths:
				args.extend( ('-I', path) ) # Need a -I for each path to add

		# Set object file output to 'nul', to prevent creation of the usual "a.out" elf object file
		args.extend( ('-o', 'nul') )

		# Pass the assembly code to the assembler using stdin.
		assemblyProcess = subprocess.Popen( args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, # Redirect input & output pipes
			creationflags=0x08000000 )
		output, errors = assemblyProcess.communicate( input=asmCode + '\n' ) # Extra ending linebreak prevents a warning from assembler

		if errors:
			# Post-process the error message by removing the first line (which just says 'Assembler messages:') and redundant input form notices
			errorLines = []
			for line in errors.splitlines()[1:]:
				if line.startswith( '{standard input}:' ):
					errorLines.append( line.split( '}:', 1 )[1] )
					continue
				
				# Condense the file path and rebuild the rest of the string as it was
				lineParts = line.split( ': ', 2 ) # Splits on first 2 occurrances only
				fileName, lineNumber = lineParts[0].rsplit( ':', 1 )
				errorLines.append( '{}:{}: {}'.format(os.path.basename(fileName), lineNumber, ': '.join(lineParts[1:])) )

			errors = '\n'.join( errorLines )
			
			if suppressWarnings:
				return ( '', errors )
			else:
				cmsg( errors, 'Assembler Warnings' )

		return self.parseAssemblerOutput( output, beautify=beautify )

	def disassemble( self, hexCode, whitespaceNeedsRemoving=False ):

		if whitespaceNeedsRemoving:
			hexCode = ''.join( hexCode.split() )

		# Create a temp file to send to the vdappc executable (doesn't appear to accept stdin)
		try:
			with open( self.tempBinFile, 'wb' ) as binFile:
				binFile.write( bytearray.fromhex(hexCode) )

		except IOError as e: # Couldn't create the file
			msg( 'Unable to create "' + self.tempBinFile + '" temp file for decompiling!', 'Error' )
			return ( '', e )

		except ValueError as e: # Couldn't convert the hex to a bytearray
			return ( '', e )

		# Give the temp file to vdappc and get its output
		process = subprocess.Popen( [self.disassemblerPath, self.tempBinFile, "0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 )
		output, errors = process.communicate() # creationFlags suppresses cmd GUI rendering

		if errors:
			print 'Errors detected during disassembly:'
			print errors
			return ( '', errors )
		
		return self.parseDisassemblerOutput( output )

	def parseAssemblerOutput( self, cmdOutput, beautify=False ):
		#tic = time.time()
		errors = ''
		code = []
		for line in cmdOutput.splitlines()[1:]: # Excludes first header line ('GAS Listing   [filename] [page _]')
			if not line: continue # Ignores empty lines
			elif 'GAS LISTING' in line and 'page' in line: continue # Ignores page headers
			elif line.startswith( '****' ): continue # Ignores warning lines

			lineMinusAsm = line.split( '\t' )[0] # ASM commands are separated by a tab. 
			lineParts = lineMinusAsm.split() # Will usually be [ lineNumber, codeOffset, hexCode ]
			linePartsCount = len( lineParts )

			if not lineParts[0].isdigit(): # Assuming there must be at least one lineParts item at this point, considering 'if not line: continue'
				print 'Error parsing assembler output on this line:'
				print line, '\n'
				code = []
				errors = 'Problem detected while parsing assembly process output:\n' + cmdOutput
				break
			elif linePartsCount == 1: continue # This must be just a label
			else:
				hexCode = lineParts[-1]

			if not beautify:
				code.append( hexCode )

			else: # Add line breaks and spaces for readability
				if code:
					lastBlockLength = len( code[-1] )
					while lastBlockLength != 9 and hexCode != '': # Last part isn't a full 4 bytes; add to that
						code[-1] += hexCode[:9 - lastBlockLength]
						hexCode = hexCode[9 - lastBlockLength:] # Add the remaining to the next block (unless the last still isn't filled)
						lastBlockLength = len( code[-1] )

				if hexCode:
					if len( code ) % 2 == 0: # An even number of blocks have been added (0 is even)
						code.append( '\n' + hexCode )
					else: code.append( ' ' + hexCode )

		# ( ''.join( code ).lstrip(), errors )
		# toc = time.time()
		# print 'asm output parsing time:', toc - tic

		return ( ''.join(code).lstrip(), errors ) # Removes first line break if present

	def parseBranchHex( self, hexCode ):

		""" Gets the branch operand (branch distance), and normalizes it. Avoids weird results from EABI.
			Essentially, this does two things: strip out the link and absolute flag bits,
			and normalize the output value, e.g. -0x40 instead of 0xffffffc0. """

		# Mask out bits 26-32 (opcode), bit 25 (sign bit) and bits 1 & 2 (branch link and absolute value flags)
		intValue = int( hexCode, 16 )
		branchDistance = intValue & 0b11111111111111111111111100

		# Check the sign bit 0x2000000, i.e. 0x10000000000000000000000000
		if intValue & 0x2000000:
			# Sign bit is set; this is a negative number.
			return hex( -( 0x4000000 - branchDistance ) )
		else:
			return hex( branchDistance )

	def parseDisassemblerOutput( self, cmdOutput ):
		code = []
		errors = ''

		for line in cmdOutput.splitlines():
			if not line:
				print 'Found empty line during disassembly. problem?'
				continue # Ignores empty lines

			lineParts = line.split() # Expected to be [ codeOffset, hexCode, instruction, *[operands] ]

			if len( lineParts ) < 3:
				errors = 'Problem detected while parsing disassembly process output:\n' + cmdOutput
				break

			codeOffset, hexCode, instruction = lineParts[:3]
			operands = lineParts[3:]

			if not validHex( codeOffset.replace(':', '') ): # Error
				errors = 'Problem detected while parsing disassembly process output:\n' + cmdOutput
				break

			elif operands and '0x' in operands[0]: # Apply some fixes
				if instruction == '.word' and len( hexCode ) > 4: # Convert to .long if this is more than 4 characters (2 bytes)
					lineParts[2] = '.long'
				elif instruction in ( 'b', 'bl', 'ba', 'bla' ):
					lineParts[3] = self.parseBranchHex( hexCode )

			code.append( ' '.join(lineParts[2:]) ) # Grabs everything from index 2 onward (all assembly command parts)

		if errors:
			code = []
			print errors

		return ( '\n'.join(code), errors )

	def preAssembleRawCode( self, codeLinesList, includePaths=None, discardWhitespace=True, suppressWarnings=False ):

		""" This method takes assembly or hex code, filters out custom MCM syntaxes and comments, and assembles the code 
			using the PowerPC EABI if it was assembly. Once that is done, the MCM syntaxes are re-added back into the code, 
			which will be replaced (compiled to hex) later. If the option to include whitespace is enabled, then the resulting 
			code will be formatted with spaces after every 4 bytes and line breaks after every 8 bytes (like a Gecko code). 
			The 'includePaths' option specifies a list of [full/absolute] directory paths for .include imports. 

			Return codes from this method are:
				0: Success
				1: Compilation placeholder or branch marker detected in original code
				2: Error during assembly
				3: Include file(s) could not be found
		"""

		# Define placeholders for special syntaxes
		compilationPlaceholder = 'stfdu f21,-16642(r13)' # Equivalent of 'deadbefe' (doesn't actually matter what this is, but must be in ASM in case of conversion)
		branchMarker = 'DEADBEFE'

		needsConversion = False
		allSpecialSyntaxes = True
		filteredLines = []
		specialBranches = []

		if type( codeLinesList ) != list:
			codeLinesList = codeLinesList.splitlines()

		# Filter out special syntaxes and remove comments
		for rawLine in codeLinesList:
			# Start off by filtering out comments
			codeLine = rawLine.split( '#' )[0].strip()

			if compilationPlaceholder in codeLine or branchMarker in codeLine:
				# This should be a very rare problem, so I'm not going to bother with suppressing this
				msg( 'There was an error while assembling this code (compilation placeholder detected):\n\n' + '\n'.join(codeLinesList), 'Assembly Error 01' )
				return ( 1, '' )

			elif isSpecialBranchSyntax( codeLine ): # e.g. "bl 0x80001234" or "bl <testFunction>"
				# Store the original command.
				if discardWhitespace: specialBranches.append( '|S|sbs__' + codeLine + '|S|' ) # Add parts for internal processing
				else: specialBranches.append( codeLine ) # Keep the finished string human-readable

				# Add a placeholder for compilation (important for other branch calculations). It will be replaced with the original command after the code is assembled to hex.
				filteredLines.append( compilationPlaceholder )

			elif containsPointerSymbol( codeLine ): # Identifies symbols in the form of <<functionName>>
				# Store the original command.
				if discardWhitespace: specialBranches.append( '|S|sym__' + codeLine + '|S|' ) # Add parts for internal processing
				else: specialBranches.append( codeLine ) # Keep the finished string human-readable

				# Add a placeholder for compilation (important for other branch calculations). It will be replaced with the original command after the code is assembled to hex.
				filteredLines.append( compilationPlaceholder )

			else:
				# Whether it's hex or not, re-add the line to filteredLines.
				filteredLines.append( codeLine )
				allSpecialSyntaxes = False

				# Check whether this line indicates that this code requires conversion.
				if not needsConversion and codeLine != '' and not validHex( codeLine.replace(' ', '') ):
					needsConversion = True

		if allSpecialSyntaxes: # No real processing needed; it will be done when resolving these syntaxes
			if discardWhitespace:
				return ( 0, ''.join(specialBranches) )
			else:
				return ( 0, '\n'.join(specialBranches) )

		filteredCode = '\n'.join( filteredLines ) # Joins the filtered lines with linebreaks.

		# If this is ASM, convert it to hex.
		if needsConversion:
			conversionOutput, errors = self.assemble( filteredCode, beautify=True, includePaths=includePaths, suppressWarnings=suppressWarnings )
			
			if errors:
				# If suppressWarnings is True, there shouldn't be warnings in the error text; but there may still be actual errors reported
				if not suppressWarnings:
					cmsg( errors, 'Assembly Error 02' )

				# Parse the error message for missing include files
				missingIncludeFile = '' #todo: change GUI to be able to show a list of multiple missing include files?
				for line in errors.splitlines():
					splitLine = line.split( "Error: can't open" )
					if len( splitLine ) == 2 and line.endswith( "No such file or directory" ):
						missingIncludeFile = splitLine[1].split( 'for reading:' )[0].strip()
						break

				if missingIncludeFile:
					return ( 3, missingIncludeFile )
				else:
					return ( 2, '' )

			else:
				newCode = conversionOutput
		else:
			newCode = filteredCode.replace( 'stfdu f21,-16642(r13)', 'DEADBEFE' )

		# If any special commands were filtered out, add them back in.
		if newCode != '' and specialBranches != []:
			# The code should be in hex at this point, with whitespace
			commandArray = newCode.split() # Split by whitespace

			commandLineArray = []
			specialBranchIndex = 0

			if discardWhitespace:
				for command in commandArray:

					# Add the previously saved special command(s).
					if command == branchMarker: 
						commandLineArray.append( specialBranches[specialBranchIndex] )
						specialBranchIndex += 1

					# Add just this command to this line.
					else: commandLineArray.append( command )

				newCode = ''.join( commandLineArray )

			else: # Add some extra formatting for the user.
				skip = False
				i = 1
				for command in commandArray:
					if skip:
						skip = False
						i += 1
						continue

					# Add the previously saved special command(s).
					if command == branchMarker: # This line was a special syntax
						commandLineArray.append( specialBranches[specialBranchIndex] )
						specialBranchIndex += 1

					# Add this command and the next on the same line if neither is a special syntax.
					elif i < len( commandArray ) and commandArray[i] != 'DEADBEFE':
						commandLineArray.append( command + ' ' + commandArray[i] )
						skip = True

					# Add just this command to this line.
					else: commandLineArray.append( command )

					i += 1

				newCode = '\n'.join( commandLineArray )

		elif discardWhitespace:
			newCode = ''.join( newCode.split() )

		return ( 0, newCode.strip() )

	def preDisassembleRawCode( self, codeLinesList, discardWhitespace=True ):
		# Define placeholders for special syntaxes
		compilationPlaceholder = 'DEADBEFE'
		branchMarker = 'stfdu f21,-16642(r13)'

		if type( codeLinesList ) == str:
			codeLinesList = codeLinesList.splitlines()

		# Filter out the special branch syntax, and remove comments.
		needsConversion = False
		allSpecialSyntaxes = True
		filteredLines = []
		specialBranches = []
		for rawLine in codeLinesList:
			# Remove comments and skip empty lines
			codeLine = rawLine.split( '#' )[0].strip()
			if codeLine == '': continue

			elif compilationPlaceholder in codeLine or branchMarker in codeLine:
				msg( 'There was an error while disassembling this code (compilation placeholder detected):\n\n' + codeLinesList, 'Disassembly Error 01' )
				return ( 1, '' )

			if isSpecialBranchSyntax( codeLine ): # e.g. "bl 0x80001234" or "bl <testFunction>"
				# Store the original command.
				specialBranches.append( codeLine )

				# Add a placeholder for compilation (important for other branch calculations). It will be replaced with the original command after the code is assembled to hex.
				filteredLines.append( compilationPlaceholder )

			elif containsPointerSymbol( codeLine ): # Identifies symbols in the form of <<functionName>>
				# Store the original command.
				specialBranches.append( codeLine )

				# Add a placeholder for compilation (important for other branch calculations). It will be replaced with the original command after the code is assembled to hex.
				filteredLines.append( compilationPlaceholder )

			else:
				# Whether it's hex or not, re-add the line to filteredLines.
				filteredLines.append( codeLine )
				allSpecialSyntaxes = False

				# Check whether this line indicates that this code requires conversion.
				if not needsConversion and validHex( codeLine.replace(' ', '') ):
					needsConversion = True

		if allSpecialSyntaxes: # No real processing needed; it will be done when resolving these syntaxes
			if discardWhitespace:
				return ( 0, ''.join(specialBranches) )
			else:
				return ( 0, '\n'.join(specialBranches) )

		filteredCode = '\n'.join( filteredLines ) # Joins the lines with linebreaks.

		# If this is hex, convert it to ASM.
		if needsConversion:
			conversionOutput, errors = self.disassemble( filteredCode, whitespaceNeedsRemoving=True )
			
			if errors:
				cmsg( errors, 'Disassembly Error 02' )
				return ( 2, '' )
			else:
				newCode = conversionOutput
		else:
			newCode = filteredCode.replace( 'DEADBEFE', 'stfdu f21,-16642(r13)' )

		# If any special commands were filtered out, add them back in.
		if newCode != '' and specialBranches != []:
			# The code is in assembly, with commands separated by line
			commandArray = newCode.splitlines()
			commandLineArray = []
			specialBranchIndex = 0

			if discardWhitespace:
				for command in commandArray:

					# Add the previously saved special command(s).
					if command == branchMarker: 
						commandLineArray.append( specialBranches[specialBranchIndex] )
						specialBranchIndex += 1

					# Add just this command to this line.
					else: commandLineArray.append( command )

				newCode = ''.join( commandLineArray )

			else: # Add some extra formatting for the user.
				# Replace special syntax placeholders with the previously saved special command(s)
				for command in commandArray:
					if command == branchMarker: # This line was a special syntax
						commandLineArray.append( specialBranches[specialBranchIndex] )
						specialBranchIndex += 1

					# Add just this command to this line.
					else: commandLineArray.append( command )

				newCode = '\n'.join( commandLineArray )
		elif discardWhitespace:
			newCode = ''.join( newCode.split() )

		# Replace a few choice ASM commands with an alternate syntax
		#newCode = newCode.replace( 'lwz r0,0(r1)', 'lwz r0,0(sp)' ).replace( 'lwz r0,0(r2)', 'lwz r0,0(rtoc)' )

		return ( 0, newCode.strip() )

	@staticmethod
	def resolveCustomSyntaxes( thisFunctionStartingOffset, rawCustomCode, preProcessedCustomCode, includePaths=None, rawCodeIsAssembly='unknown' ):

		""" Replaces any custom branch syntaxes that don't exist in the assembler with standard 'b_ [intDistance]' branches, 
			and replaces function symbols with literal RAM addresses, of where that function will end up residing in memory. 

			This process may require two passes. The first is always needed, in order to determine all addresses and syntax resolutions. 
			The second may be needed for final assembly because some lines with custom syntaxes might need to reference other parts of 
			the whole source code (raw custom code), such as for macros or label branch calculations. """

		debugging = False

		if '|S|' not in preProcessedCustomCode: # Contains no special syntaxes; just return it
			return ( 0, preProcessedCustomCode )

		if debugging:
			print '\nresolving custom syntaxes for code stored at', hex(thisFunctionStartingOffset)

		standaloneFunctions = genGlobals['allStandaloneFunctions'] # Making it local for less look-ups
		customCodeSections = preProcessedCustomCode.split( '|S|' )
		rawCustomCodeLines = rawCustomCode.splitlines()
		if rawCodeIsAssembly == 'unknown':
			rawCodeIsAssembly = codeIsAssembly( rawCustomCodeLines )
		requiresAssembly = False
		resolvedAsmCodeLines = []
		errorDetails = ''
		byteOffset = 0
		returnCode = 0

		# Resolve individual syntaxes to finished assembly and/or hex
		for i, section in enumerate( customCodeSections ):

			if section.startswith( 'sbs__' ): # Something of the form 'bl 0x80001234' or 'bl <function>'; build a branch from this
				section = section[5:] # Removes the 'sbs__' identifier

				if debugging:
					print 'recognized special branch syntax at function offset', hex( byteOffset ) + ':', section

				if '+' in section:
					section, offset = section.split( '+' ) # Whitespace around the + should be fine for int()
					if offset.lstrip().startswith( '0x' ):
						branchAdjustment = int( offset, 16 )
					else: branchAdjustment = int( offset )
				else: branchAdjustment = 0

				branchInstruction, targetDescriptor = section.split()[:2] # Get up to two parts max

				if isStandaloneFunctionHeader( targetDescriptor ): # The syntax references a standalone function (comments should already be filtered out).
					targetFunctionName = targetDescriptor[1:-1] # Removes the </> characters
					targetFunctionOffset = standaloneFunctions[targetFunctionName][0]
					branchDistance = calcBranchDistance( thisFunctionStartingOffset + byteOffset, targetFunctionOffset )

					if branchDistance == -1: # Fatal error; end the loop
						errorDetails = 'Unable to calculate SF branching distance, from {} to {}.'.format( hex(thisFunctionStartingOffset + byteOffset), hex(targetFunctionOffset) )
						break

				else: # Must be a special branch syntax using a RAM address
					startingRamOffset = offsetInRAM( thisFunctionStartingOffset + byteOffset, dol.sectionInfo )

					if startingRamOffset == -1: # Fatal error; end the loop
						errorDetails = 'Unable to determine starting RAM offset, from DOL offset {}.'.format( hex(thisFunctionStartingOffset + byteOffset) )
						break
					branchDistance = int( targetDescriptor, 16 ) - 0x80000000 - startingRamOffset

				branchDistance += branchAdjustment

				# Remember in case reassembly is later determined to be required
				resolvedAsmCodeLines.append( '{} {}'.format(branchInstruction, branchDistance) ) 

				# Replace this line with hex for the finished branch
				if not requiresAssembly: # The preProcessed customCode won't be used if reassembly is required; so don't bother replacing those lines
					customCodeSections[i] = assembleBranch( branchInstruction, branchDistance ) # Assembles these arguments into a finished hex string

				# Check if this was the last section
				if i + 1 == len( customCodeSections ):
					returnCode = 100

				byteOffset += 4

			elif section.startswith( 'sym__' ): # Contains a function symbol; something like 'lis r3, (<<function>>+0x40)@h'; change the symbol to an address
				section = section[5:]

				if debugging:
					print 'resolving symbol names in:', section

				erroredFunctions = set()

				# Determine the RAM addresses for the symbols, and replace them in the line
				for name in containsPointerSymbol( section ):
					# Get the dol offset and ultimate RAM address of the target function
					targetFunctionOffset = standaloneFunctions[name][0]
					ramAddress = offsetInRAM( targetFunctionOffset, dol.sectionInfo ) + 0x80000000 # 0x80000000 is the base address for GC/Wii games
					
					if ramAddress == -1: # Fatal error; probably an invalid function offset was given, pointing to an area outside of the DOL
						erroredFunctions.add( name )

					address = "0x{0:0{1}X}".format( ramAddress, 8 ) # e.g. 1234 (int) -> '0x800004D2' (string)

					section = section.replace( '<<' + name + '>>', address )

				if erroredFunctions:
					errorDetails = 'Unable to calculate RAM addresses for the following function symbols:\n\n' + '\n'.join( erroredFunctions )
					break				

				if debugging:
					print '              resolved to:', section

				requiresAssembly = True
				resolvedAsmCodeLines.append( section )

				# Check if this was the last section
				if i + 1 == len( customCodeSections ):
					returnCode = 100

				byteOffset += 4

			else: # This code should already be pre-processed hex (assembled, with whitespace removed)
				byteOffset += len( section ) / 2

		if errorDetails: return ( 1, errorDetails )

		# Assemble the final code using the full source (raw) code
		if requiresAssembly and rawCodeIsAssembly:
			if debugging:
				print 'reassembling resolved code from source (asm) code'

			# Using the original, raw code, remove comments, replace the custom syntaxes, and assemble it into hex
			rawAssembly = []

			for line in rawCustomCodeLines:
				# Start off by filtering out comments and empty lines.
				codeLine = line.split( '#' )[0].strip()
				#if not codeLine: continue
					
				if isSpecialBranchSyntax( codeLine ) or containsPointerSymbol( codeLine ): # Replace with resolved code lines
					rawAssembly.append( resolvedAsmCodeLines.pop(0) )

				else: rawAssembly.append( codeLine )

			customCode, errors = customCodeProcessor.assemble( '\n'.join(rawAssembly), includePaths=includePaths, suppressWarnings=True )

			if errors:
				return ( 2, 'Unable to assemble source code with custom syntaxes.\n\n' + errors )

		elif requiresAssembly: # Yet the raw code is in hex form
			if debugging:
				print 'assembling custom syntaxes separately from assembled hex'

			# Assemble the resolved lines in one group (doing it this way instead of independently in the customCodeSections loop for less IPC overhead)
			assembledResolvedCode, errors = customCodeProcessor.assemble( '\n'.join(resolvedAsmCodeLines), beautify=True, suppressWarnings=True )
			resolvedHexCodeLines = assembledResolvedCode.split()
			newCustomCodeSections = preProcessedCustomCode.split( '|S|' ) # Need to re-split this, since customCodeSections may have been modified by now

			if errors:
				return ( 3, 'Unable to assemble custom syntaxes.\n\n' + errors )
			else:
				# Add the resolved, assembled custom syntaxes back into the full custom code string
				for i, section in enumerate( newCustomCodeSections ):
					if section.startswith( 'sbs__' ) or section.startswith( 'sym__' ):
						newCustomCodeSections[i] = resolvedHexCodeLines.pop( 0 )
						if resolvedHexCodeLines == []: break

				customCode = ''.join( newCustomCodeSections )

		else: # Recombine the code lines back into one string. Special Branch Syntaxes have been assembled to hex
			if debugging:
				print 'resolved custom code using the preProcessedCustomCode lines'

			customCode = ''.join( customCodeSections )

		return ( returnCode, customCode )


def openModsLibrary():

	""" Wrapper for the two "Open Mods Library Folder" buttons. 
		Wraps the 'openFolder' button, using the current Mods Library path. """

	openFolder( getModsFolderPath() )


def openLibraryFile():

	""" Called solely by the "Open this File" button on the Mods Library control panel. 
		Opens the text file for the tab currently in view on the Mods Library tab. """

	currentlySelectedTab = getCurrentModsLibraryTab()

	if currentlySelectedTab == 'emptyNotebook': pass # Failsafe; shouldn't be able to happen.
	else:
		frameForBorder = currentlySelectedTab.winfo_children()[0]
		modsPanelInterior = frameForBorder.winfo_children()[0].interior # frameForBorder -> modsPanel.interior
		firstMod = modsPanelInterior.winfo_children()[0] # Checking the first mod of the mods panel (should all have same source file)

		# Open the file (or folder, if this is an AMFS)
		webbrowser.open( firstMod.sourceFile )


																 #==========================================#
																# ~ ~ Summary Tab Population and Sorting ~ ~ #
																 #==========================================#
def clearSummaryTab():
	# Empty the treeviews
	for item in modsSummaryTree.get_children(): modsSummaryTree.delete( item )
	for item in standalonesSummaryTree.get_children(): standalonesSummaryTree.delete( item )

	# Reset the totals labels
	totalModsInstalledLabel.set( 'Mods Installed:' )
	requiredStandaloneFunctionsLabel.set( 'Required Standalone Functions for the Installed Mods:' )


def addToInstallationSummary( modName='', modType='', summaryReport=None, geckoInfrastructure=False, isMod=True ):
	if not summaryReport: summaryReport = []
	childIndent = '\t-  '

	if geckoInfrastructure: # Add entries just for the codehandler and hook
		if not modsSummaryTree.exists( 'geckoEnvironInfo' ):
			modsSummaryTree.insert( '', 'end', iid='geckoEnvironInfo', text='Gecko Codehandler and Hook', 
				values=('GC', '', uHex(gecko.codehandlerLength + 4), uHex(gecko.codehandlerLength)), tags=('mainEntry', 'notMod') )
			modsSummaryTree.insert( 'geckoEnvironInfo', 'end', text=childIndent + 'Codehandler Hook', 
				values=('GC', uHex(gecko.hookOffset), '0x4', '0') )
			modsSummaryTree.insert( 'geckoEnvironInfo', 'end', text=childIndent + 'Gecko Codehandler', 
				values=('GC', uHex(gecko.codehandlerRegionStart), uHex(gecko.codehandlerLength), uHex(gecko.codehandlerLength)) )
		return

	def formatLocationString( dolOffset ): # dolOffset is an int in this case
		# Create a string for the location, converting to a RAM address if necessary
		if modsSummaryTree.heading( 'location', 'text' ) == 'DOL Offset': return uHex( dolOffset )
		else: 
			ramAddress = offsetInRAM( dolOffset, dol.sectionInfo )
			return '0x8' + toHex( ramAddress, 7 )

	modTypes = { 'static': 'SO', 'injection': 'IM', 'standalone': 'SF', 'gecko': 'GC' }
	totalBytesChanged = 0
	totalFreeSpaceUsed = 0

	# Add this mod to the summary tree
	if len( summaryReport ) == 1: # Create just one main entry for this mod (no children)
		changeName, changeType, dolOffset, customCodeLength = summaryReport[0]
		location = formatLocationString( dolOffset )

		if changeType == 'static': freeSpaceUsed = '0'
		else: freeSpaceUsed = uHex( customCodeLength )

		modsSummaryTree.insert( '', 'end', text=modName, tags=('mainEntry'), values=(modTypes[changeType], location, uHex(customCodeLength), freeSpaceUsed) )

	else:
		if isMod: tags = ( 'mainEntry' )
		else: tags = ( 'mainEntry', 'notMod' ) # First tag is for styling, second tag prevents it from being counted among total mods installed

		parentModEntry = modsSummaryTree.insert( '', 'end', text=modName, tags=tags )

		# Add each change for the parent mod entry above, as children
		for changeName, changeType, dolOffset, customCodeLength in summaryReport:
			totalBytesChanged += customCodeLength
			location = formatLocationString( dolOffset )

			# Check how much free space is used by this code change
			if changeType == 'static' or ( changeType == 'injection' and changeName == 'Branch' ): freeSpaceUsed = '0'
			else: freeSpaceUsed = uHex( customCodeLength )

			modsSummaryTree.insert( parentModEntry, 'end', text=childIndent + changeName, values=(modTypes[changeType], location, uHex(customCodeLength), freeSpaceUsed) )

			if changeType != 'static': totalFreeSpaceUsed += customCodeLength

			if changeType == 'injection': totalBytesChanged += 4 # For the branch
			elif changeType == 'standalone':
				functionName = changeName.split(':')[1].lstrip()

				# Add this function to the Standalone Functions summary tree, if it doesn't already exist
				if not standalonesSummaryTree.exists( functionName ):
					standalonesSummaryTree.insert( '', 'end', iid=functionName, text=functionName, tags=('mainEntry') ) # values=(refCount, location)
					standalonesSummaryTree.insert( functionName, 'end', text='\tMods using this function:' )

				standalonesSummaryTree.insert( functionName, 'end', text='\t  '+modName, tags=('modName') ) #, values=('', location)

				# Update the reference count of the function
				standalonesSummaryTree.item( functionName, values=(len( standalonesSummaryTree.get_children(functionName) ) - 1, location) )

		modsSummaryTree.item( parentModEntry, values=(modTypes[modType], '', uHex(totalBytesChanged), uHex(totalFreeSpaceUsed) ) )


def updateSummaryTabTotals():
	# Store a snapshot of the items in the treeviews, to help with sorting later. To be filled with ( iid, childIids, childNames )
	modsSummaryTree.originalSortOrder = []

	total1byteOverwrites = 0
	total2byteOverwrites = 0
	total4byteOverwrites = 0
	totalNbyteOverwrites = 0
	totalInjections = 0
	injectionsOverhead = 0
	staticGeckoOverhead = 0

	totalFreeSpaceUsed = 0
	grandTotalStandalonesSpaceUsed = 0
	sfItems = []
	modsSummaryTreeChildren = modsSummaryTree.get_children()
	
	# Calculate total bytes changed and space used by SAFs by iterating over the items in the mods summary tree
	for item in modsSummaryTreeChildren:
		changeType, _, _, freeSpaceUsed = modsSummaryTree.item( item, 'values' ) # Full tuple is ( changeType, location, bytesChanged, freeSpaceUsed )
		totalFreeSpaceUsed += int( freeSpaceUsed, 16 )
		childIids = modsSummaryTree.get_children( item )

		if changeType == 'SF':
			# Iterate over the changes for this mod, looking for standalone functions
			for child in childIids:
				childChangeType, _, _, childFreeSpaceUsed = modsSummaryTree.item( child, 'values' )

				if childChangeType == 'SF' and modsSummaryTree.item( child, 'text' ) not in sfItems: 
					grandTotalStandalonesSpaceUsed += int( childFreeSpaceUsed, 16 )
					sfItems.append( modsSummaryTree.item( child, 'text' ) )

		# Store this mod and it's children to remember their order (and original child names)
		childNames = []
		for child in childIids:
			childText = modsSummaryTree.item( child, 'text' )
			childNames.append( childText )
			if childText == '\t-  Branch': continue # Injection branch

			# Track a few metrics
			childChangeType, _, bytesChanged, _ = modsSummaryTree.item( child, 'values' )
			bytesChanged = int( bytesChanged, 16 )
			if childChangeType == 'SO':
				if bytesChanged == 1:
					total1byteOverwrites += 1
					staticGeckoOverhead += 8
				elif bytesChanged == 2:
					total2byteOverwrites += 1
					staticGeckoOverhead += 8
				elif bytesChanged == 4:
					total4byteOverwrites += 1
					staticGeckoOverhead += 8
				else: 
					totalNbyteOverwrites += 1
					staticGeckoOverhead += 8 + bytesChanged
			if childChangeType == 'IM':
				totalInjections += 1
				if bytesChanged % 8 == 0: injectionsOverhead += 8
				else: # Code not an even multiple of 8 bytes; would require an extra nop if in Gecko code form
					injectionsOverhead += 0xC

		modsSummaryTree.originalSortOrder.append( ( item, childIids, childNames ) )

	# Count the number of mods installed, excluding extra items in the summary tree that aren't actually mods
	totalModsInstalled = len( modsSummaryTreeChildren ) - len( modsSummaryTree.tag_has( 'notMod' ) )
	#print 'non mods found:', len( modsSummaryTree.tag_has( 'notMod' ) ), ':', modsSummaryTree.tag_has( 'notMod' )

	if injectionsOverhead > 0 or staticGeckoOverhead > 0:
		totalCodelistOverhead = 16 + injectionsOverhead + staticGeckoOverhead # +16 for the codelist wrapper
	else:
		totalCodelistOverhead = 0
	print ''
	print 'Total mods installed:', totalModsInstalled
	print 'Total injections:', totalInjections
	print '        overhead:', uHex( injectionsOverhead )
	print 'Total static overwrites:', total1byteOverwrites + total2byteOverwrites + total4byteOverwrites + totalNbyteOverwrites
	print '            1 byte:', total1byteOverwrites
	print '            2 byte:', total2byteOverwrites
	print '            4 byte:', total4byteOverwrites
	print '           >4 byte:', totalNbyteOverwrites
	print '               overhead:', uHex( staticGeckoOverhead )
	print 'Total Gecko codelist overhead:', uHex( totalCodelistOverhead ), ' (' + humansize(totalCodelistOverhead) + ')'
	combinedGeckoSpace = gecko.codehandlerLength + totalCodelistOverhead
	print '      + Codehandler size (' + uHex(gecko.codehandlerLength) + ') =', uHex( combinedGeckoSpace ), ' (' + humansize(combinedGeckoSpace) + ')'
	print ''

	# Update the mod & SF total labels
	totalModsInstalledLabel.set( 'Mods Installed (' + str(totalModsInstalled) + ' total; ' + uHex(totalFreeSpaceUsed) + ' bytes used):' )
	requiredStandaloneFunctionsLabel.set( 'Required Standalone Functions for the Installed Mods'
										  ' (' + str(len(sfItems)) + ' total; ' + uHex(grandTotalStandalonesSpaceUsed) + ' bytes used):' )

	# Reorder the mods if they should be sorted by offset
	if settings.getboolean( 'General Settings', 'sortSummaryByOffset' ):
		sortModsSummaryByOffset( True )


def updateSummaryTreeSelection( event, itemToSelect='' ): 

	""" Updates which treeview item(s) currently have the 'selected' tag.
		If no iid was given, this uses the item that was last clicked on. """

	treeview = event.widget

	# Check which mods are currently selected, and remove the "selected" tag from them.
	for iid in treeview.tag_has( 'selected' ):
		currentTags = list( treeview.item( iid, 'tags' ) )
		currentTags.remove( 'selected' )
		treeview.item( iid, tags=currentTags )

	# Add the 'selected' tag to the currently selected item
	if not itemToSelect: itemToSelect = treeview.identify_row( event.y )
	treeview.item( itemToSelect, tags=list(treeview.item( itemToSelect, 'tags' )) + ['selected'] )


def onModSummaryTreeRightClick( event ):

	""" If this was the DOL Offset ("location") column header, toggle all values between DOL Offset or RAM Address.
		Or if this click was on anything else, it was probably on a mod in the tree, so show a context menu. """

	if modsSummaryTree.identify_region( event.x, event.y ) == 'heading':
		if modsSummaryTree.identify_column( event.x ) == '#2': # The Offset column header was clicked on.
			toggleSummaryLocationDisplayType()

	else: # A mod was probably clicked on
		modsSummaryContextMenu.show( event )


def onStandalonesSummaryTreeRightClick( event ):
	# Check what item has been right-clicked on
	selectedItem = standalonesSummaryTree.identify_row( event.y ) # Empty string if no treeview item is under the mouse

	if selectedItem:
		# Bring up the context menu. Include 'View in...' options if a line describing a mod was clicked on.
		thisItemIsAModName = standalonesSummaryTree.tag_has( 'modName', selectedItem )
		standalonesSummaryContextMenu = summaryContextMenu( root, forStandalones=True, enableSearchFeatures=thisItemIsAModName )
		standalonesSummaryContextMenu.show( event, selectedItem=selectedItem )


def toggleSummaryLocationDisplayType():
	# Toggle the values for this column between DOL Offsets and RAM Addresses
	if modsSummaryTree.heading( 'location', 'text' ) == 'DOL Offset':
		def conversionFunction( offsetString ): return normalizeRamAddress( offsetString, returnType='string' )
		modsSummaryTree.heading( '#2', text='RAM Address' )
		settings.set( 'General Settings', 'summaryOffsetView', 'ramAddress' )
	else:
		def conversionFunction( offsetString ): return normalizeDolOffset( offsetString, returnType='string' )
		modsSummaryTree.heading( '#2', text='DOL Offset' )
		settings.set( 'General Settings', 'summaryOffsetView', 'dolOffset' )

	for modIid in modsSummaryTree.get_children():
		changeType, location, bytesChanged, freeSpaceUsed = modsSummaryTree.item( modIid, 'values' )
		if location != '':
			newValues = ( changeType, conversionFunction(location), bytesChanged, freeSpaceUsed )
			modsSummaryTree.item( modIid, values=newValues )

		for childIid in modsSummaryTree.get_children( modIid ):
			changeType, location, bytesChanged, freeSpaceUsed = modsSummaryTree.item( childIid, 'values' )
			newValues = ( changeType, conversionFunction(location), bytesChanged, freeSpaceUsed )
			modsSummaryTree.item( childIid, values=newValues )

	saveOptions()


class summaryContextMenu( Menu ): 

	""" Primarily, the benefit of using a class and creating instances for the context menus like this is that
		we can easily pass values to the menu functions using self, usually avoiding lambdas or helper functions. """

	def __init__( self, parent, forStandalones=False, enableSearchFeatures=True ):

		if forStandalones:
			Menu.__init__( self, parent, tearoff=False )

		else: # For all other mods (static/injection/gecko) in the main treeview
			Menu.__init__( self, parent, tearoff=False, postcommand=self.setCommandLabels )							# Keyboard selection

			self.add_command( command=toggleSummaryLocationSortMethod ) # Will get its text from setViewModeCommand()	# V
			self.add_command( command=toggleSummaryLocationDisplayType ) # Same text change trick as above
			self.add_separator()

		if enableSearchFeatures:
			self.add_command( label='View in Mods Library Tab', command=self.showInModLibrary )							# ?
			self.add_command( label='View in Mod Construction Tab', command=self.showInModConstruction )				# ?

		self.add_command( label='Copy Offset to Clipboard', underline=5, command=self.copyOffsetToClipboard )			# O
		self.add_separator()
		self.add_command( label='Expand All', underline=0, command=self.expandAll )										# E
		self.add_command( label='Collapse All', underline=0, command=self.collapseAll )									# C

	def setCommandLabels( self ):
		# Set text for the Sort Method option
		if settings.getboolean( 'General Settings', 'sortSummaryByOffset' ):						# Keyboard selection
			self.entryconfig( 0, label='Simple View', underline=7 )										# V
		else:
			self.entryconfig( 0, label='Advanced View (Sort Changes by Offset)', underline=9 )			# V

		# Set text for the location Display Type option (DOL Offset vs. RAM Address)
		if settings.get( 'General Settings', 'summaryOffsetView' ).lstrip()[0].lower().startswith( 'd' ): # 'd' for dolOffset
			self.entryconfig( 1, label='Show RAM Addresses' )
		else:
			self.entryconfig( 1, label='Show DOL Offsets' )

	def show( self, event, selectedItem=None ):
		# Remember the coordinates and the target treeview widget
		self.x = event.x
		self.y = event.y
		self.treeview = event.widget

		# Move focus to the item under the mouse and assume that's the target item
		if selectedItem:
			self.selectedItem = selectedItem
		else:
			self.selectedItem = self.treeview.identify_row( self.y )

		updateSummaryTreeSelection( event, self.selectedItem )
		self.treeview.focus( self.selectedItem )

		# Display the context menu at the current mouse coords
		self.post( event.x_root, event.y_root )

	def showInModLibrary( self ):
		if not self.selectedItem: 
			msg( 'No item is selected.' )
			return
		parent = self.treeview.parent( self.selectedItem ) # Returns an empty string if it doesn't have a parent
		tags = self.treeview.item( self.selectedItem, 'tags' )
		
		if 'notMod' in tags: # These won't exist in the Mods Library
			msg( 'This item represents changes that are not\npart of a mod in the Mods Library tab.' )
			return
		elif self.treeview != standalonesSummaryTree and not 'mainEntry' in tags and parent != '':
			modItem = parent
		else:
			modItem = self.selectedItem

		modName = self.getOrigName( modItem )

		# Check if this item exists in the mods library, and go to it if it does
		for mod in genGlobals['allMods']:
			if mod.name == modName:
				mainNotebook.select( modsLibraryTab )
				goToMod( modName )
				break
		else: msg( 'This item does not exist in the Mods Library tab!' )

	def showInModConstruction( self ):
		if not self.selectedItem: 
			msg( 'No item is selected.' )
			return
		parent = self.treeview.parent( self.selectedItem ) # Returns an empty string if it doesn't have a parent
		tags = self.treeview.item( self.selectedItem, 'tags' )
		
		if 'notMod' in tags: # These won't exist in the Mods Library
			msg( 'This item represents changes that are not\npart of a mod in the Mods Library tab.' )
			return
		elif self.treeview != standalonesSummaryTree and not 'mainEntry' in tags and parent != '':
			modItem = parent
		else:
			modItem = self.selectedItem

		modName = self.getOrigName( modItem )

		# Iterate over the mods in the mods library tab to get the mod's info, and send that to the mod construction tab.
		for mod in genGlobals['allMods']:
			if mod.name == modName:
				inspectMod( None, mod=mod )
				break
		else: msg( 'Unable to find this mod! The Mods Library may have been changed.' )

	def getOrigName( self, treeviewItem ):
		modName = self.treeview.item( treeviewItem, 'text' )

		if self.treeview == modsSummaryTree and modName.startswith( 'Part of "'): # For cases of sorted entries (Advanced View, with separated code changes).
			changeType = self.treeview.item( treeviewItem, 'values' )[0]

			if changeType == 'SF' and modName.endswith( ')' ):
				modName = modName.rsplit( ' (', 1 )[0][9:-1] # Removes the function name portion
			elif modName.endswith( '"' ):
				modName = modName[9:-1]

		return modName.strip()

	def copyOffsetToClipboard( self ):
		if not self.selectedItem: msg( 'No mod is selected.' )
		else:
			# Item values on the main list are ( changeType, location, bytesChanged, freeSpaceUsed )
			# On the SF list they are ( referenceCount, location ), or empty if not the main parent item
			values = self.treeview.item( self.selectedItem, 'values' )
			if len( values ) > 1: copyToClipboard( values[1].strip() )

	def expandAll( self ):
		for item in self.treeview.get_children(): self.treeview.item( item, open=True )

	def collapseAll( self ):
		for item in self.treeview.get_children(): self.treeview.item( item, open=False )


def sortModsSummaryByOffset( sortByOffset, treeview=None ):
	if not treeview:
		treeview = modsSummaryTree # might be using this function again a little differently

	if sortByOffset:
		# Unpack individual child code changes that mods may have, creating a list of all mod code changes
		allChanges = [] # Will be filled with ( location, iid )
		uniqueLocations = Set()
		for iid in treeview.get_children():
			children = treeview.get_children( iid )

			if len( children ) == 0:
				location = int( treeview.item( iid, 'values' )[1], 16 )
				if location not in uniqueLocations: # Prevents cases of multiple standalone function references
					allChanges.append( ( location, iid ) )
					uniqueLocations.add( location )

			else:
				treeview.detach( iid ) # Removes this item and its decendents from the treeview (doesn't delete them)

				# Add this mod's children/code changes to the list
				parentName = treeview.item( iid, 'text' )
				for childIid in children:
					changeType, locationHex, _, _ = treeview.item( childIid, 'values' ) # The full tuple is ( changeType, locationHex, bytesChanged, freeSpaceUsed )
					location = int( locationHex, 16 )

					if location not in uniqueLocations: # Prevents cases of multiple standalone function references
						allChanges.append( ( location, childIid ) )
						uniqueLocations.add( location )

					# These items will also need their names changed to understand what they belong to, since they'll no longer have a parent
					if changeType == 'SF':
						sfName = treeview.item( childIid, 'text' ).split( ':' )[1].strip()
						treeview.item( childIid, text='Part of "{}" ({})'.format(parentName, sfName)  )
					else:
						treeview.item( childIid, text='Part of "{}"'.format(parentName) )

		# Perform the sort on the list and then the treeview items
		allChanges.sort()
		for index, ( location, iid ) in enumerate( allChanges ): treeview.move( iid, '', index )

		treeview.heading( '#0', text='Mod Name / Component Owner' )
		settings.set( 'General Settings', 'sortSummaryByOffset', 'True' )

	else: # The items have previously been sorted. Restore them to their original order
		for index, (modIid, childIids, childNames) in enumerate( treeview.originalSortOrder ):
			treeview.move( modIid, '', index )
			for index2, childIid in enumerate( childIids ):
				treeview.move( childIid, modIid, index2)
				treeview.item( childIid, text=childNames[index2] ) # These were renamed during the first sort; need to restore them

		treeview.heading( '#0', text='Mod Name' )
		settings.set( 'General Settings', 'sortSummaryByOffset', 'False' )

	saveOptions()


def showInstalledModsList():
	if not problemWithDol():
		modsList = listInstalledMods()

		cmsg( '\n'.join(modsList), 'Installed Mods  ({} total)'.format(len(modsList)), 'left' )


def listInstalledMods():
	modNames = []

	# Iterate over all items (even those that may be hidden due to sorting)
	# for ( modIid, childIids, childNames ) in modsSummaryTree.originalSortOrder:
	# 	tags = modsSummaryTree.item( modIid, 'tags' )
	# 	#print 'item tags', tags
	# 	if 'mainEntry' in tags and not 'notMod' in tags:
	# 		modName = modsSummaryTree.item( modIid, 'text' )
	# 		modNames.append( modName )

	for mod in genGlobals['allMods']:
		if mod.state == 'enabled': modNames.append( mod.name )

	return modNames


def installModsList():
	if problemWithDol(): return

	entryWindow = PopupScrolledTextWindow( root, title='Mods List Entry', message="You may enter a list of mods (separated by line breaks) that you'd "
												"like to install to your " + dol.type.upper() + " here:", height=20, button1Text='Install' )
	if not entryWindow.entryText: return

	loadRegionOverwriteOptions()

	# Parse the given list for mod names (excluding empty lines and line start/end whitespace), and turn it into a set
	modsToInstall = []
	for line in entryWindow.entryText.strip().splitlines():
		if line.strip() != '': modsToInstall.append( line.strip() )
	modsToInstall = Set( modsToInstall )

	# Check if there are any issues with installing Gecko codes
	geckoCodesToSkip = []
	if not gecko.environmentSupported or not overwriteOptions[ 'EnableGeckoCodes' ].get():
		# Gecko codes are not currently enabled. Check if any Gecko codes are actually included in the list
		for mod in genGlobals['allMods']:
			if mod.type == 'gecko' and mod.name in modsToInstall: geckoCodesToSkip.append( mod.name )

		if geckoCodesToSkip:
			# Ask to cancel this operation or proceed without Gecko codes
			if not gecko.environmentSupported:
				proceed = tkMessageBox.askyesno( 'Proceed without Gecko codes?', 'Something about your current configuration does not allow for Gecko codes '
									'(some of which are included in the install list).\n\nWould you like to proceed without those Gecko codes anyway?' )
				if not proceed: return

			# Offer to enable Gecko codes
			elif not overwriteOptions[ 'EnableGeckoCodes' ].get():
				# If this is for Melee, add some details to the message
				if dol.isMelee and ( gecko.codelistRegion == 'DebugModeRegion' or gecko.codehandlerRegion == 'DebugModeRegion' 
									or gecko.codelistRegion == 'Debug Mode Region' or gecko.codehandlerRegion == 'Debug Mode Region' ):
					meleeDetails = ( "Mostly, this just means that you wouldn't be able to use the vanilla Debug Menu (if you're not "
									 "sure what that means, then you're probably not using the Debug Menu, and you can just click yes). " )
				else: meleeDetails = ''

				promptToUser = ('The "Enable Gecko Codes" option is not selected, however Gecko codes are included in the install list.'
								'\n\nEnabling Gecko codes means that the regions defined for Gecko codes, ' + gecko.codelistRegion + ' and ' + gecko.codehandlerRegion + ', '
								"will be reserved (i.e. may be partially or fully overwritten) for custom code. " + meleeDetails + 'Regions that you have '
								'enabled for use can be viewed and modified by clicking on the "Code-Space Options" button on the Mods Library tab. '
								'\n\nWould you like to enable these regions for overwrites in order to use Gecko codes?')

				geckoRegionsEnabled = willUserAllowGecko( promptToUser, True, root )

				if geckoRegionsEnabled: geckoCodesToSkip = []

			modsToInstall.difference_update( geckoCodesToSkip ) # Updates in-place

	# Remove any mods not found in the library, but also remember them for later
	modsNotFound = modsToInstall.difference( genGlobals['allModNames'] )
	modsToInstall.difference_update( modsNotFound )

	# Iterate all mods in the library. Disable them if they're not in the list above, and enable them if they are
	for mod in genGlobals['allMods']:
		if mod.state == 'unavailable': continue
		elif mod.name in modsToInstall: mod.setState( 'pendingEnable' )
		elif mod.state == 'enabled' or mod.state == 'pendingEnable': mod.setState( 'pendingDisable' )
		else: mod.setState( 'disabled' )

	# Check on and validate the selected mods and attempt to install them
	checkForPendingChanges() # Also updates GUI, such as the fill meters
	saveSuccessful = saveCodes()

	if saveSuccessful:
		# Check for any other mods that may not have been installed
		modsNotInstalled = modsToInstall.difference( listInstalledMods() )

		# Report out a summary of the operation
		if modsNotFound or modsNotInstalled or geckoCodesToSkip:
			summaryMessage = ''
			if modsNotFound: summaryMessage += '\nThe following mods could not be installed\nbecause they could not be found in the library:\n\n' + '\n'.join( modsNotFound ) + '\n'
			if geckoCodesToSkip: summaryMessage += '\nThe following mods could not be installed\nbecause Gecko codes are disabled:\n\n' + '\n'.join( geckoCodesToSkip ) + '\n'
			if modsNotInstalled: summaryMessage += '\nThe following mods could not be installed\n(likely because there is not enough free space enabled for use):\n\n' + '\n'.join( modsNotInstalled )

			cmsg( summaryMessage )

		else: msg( 'All mods installed!' )

																 #=======================================#
																# ~ ~ General GUI Modules & Functions ~ ~ #
																 #=======================================#

class VerticalScrolledFrame( Frame ):

	""" This is a widget used in the Mods Library tab for scrolling an entire region. 
		Use the 'interior' attribute to place widgets inside the scrollable area. 
		The outer widget is essentially just a Frame; which can be attached using 
		pack/place/grid geometry managers as normal. """

	def __init__( self, parent, *args, **kw ):
		Frame.__init__( self, parent, *args, **kw )
		self.scrollFlag = True # Used by the scroll wheel handler

		# create a canvas object and a vertical scrollbar for scrolling it
		self.vscrollbar = Scrollbar( self, orient='vertical' )
		self.vscrollbar.pack( fill='y', side='right', expand=False )
		self.canvas = Canvas( self, bd=0, highlightthickness=0, yscrollcommand=self.vscrollbar.set, width=430 )
		self.canvas.pack( side='left', fill='both', expand=True )
		self.vscrollbar.config( command=self.canvas.yview )

		# create a frame inside the canvas which will be scrolled with it
		self.interior = Frame( self.canvas, relief='ridge' )
		self.interior_id = self.canvas.create_window( 0, 0, window=self.interior, anchor='nw' )

		# track changes to the canvas and frame width and sync them,
		# also updating the scrollbar
		self.interior.bind( '<Configure>', self._configure_interior )
		self.canvas.bind( '<Configure>', self._configure_canvas )

	def _configure_interior( self, event ):
		# Check if a scrollbar is necessary, and add/remove it as needed.
		if self.interior.winfo_height() > self.canvas.winfo_height():
			self.vscrollbar.pack( fill='y', side='right', expand=False )
			self.scrollFlag = True
		else:
			self.vscrollbar.pack_forget()
			self.scrollFlag = False # Disable scrolling until it's really needed again

		# update the scrollbars to match the size of the inner frame
		size = ( self.interior.winfo_reqwidth(), self.interior.winfo_reqheight() )
		self.canvas.config( scrollregion="0 0 %s %s" % size )
		
		# if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
		# 	# update the canvas's width to fit the inner frame
		# 	self.canvas.config(width=self.interior.winfo_reqwidth())

	def _configure_canvas( self, event ):
		if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
			# update the inner frame's width to fill the canvas
			self.canvas.itemconfigure( self.interior_id, width=self.canvas.winfo_width() )


class VerticalScrolledFrame2( Frame ):

	""" This is a widget used in the Mods Library tab for scrolling an entire region. 
		This has a few subtle differences from the original variant, which is that the 
		scrollbar is placed on the left rather than the right, and the width is not set. 
		Use the 'interior' attribute to place widgets inside the scrollable area. 
		The outer widget is essentially just a Frame; which can be attached using 
		pack/place/grid geometry managers as normal. """

	def __init__( self, parent, *args, **kw ):
		Frame.__init__( self, parent, *args, **kw )
		self.scrollFlag = True # Used by the scroll wheel handler

		# create a canvas object and a vertical scrollbar for scrolling it
		self.vscrollbar = Scrollbar( self, orient='vertical' )
		self.vscrollbar.pack( fill='y', side='left', expand=False )
		self.canvas = Canvas( self, bd=0, highlightthickness=0, yscrollcommand=self.vscrollbar.set )
		self.canvas.pack( side='right', fill='both', expand=True )
		self.vscrollbar.config( command=self.canvas.yview )

		# create a frame inside the canvas which will be scrolled with it
		self.interior = Frame( self.canvas, relief='ridge' )
		self.interior_id = self.canvas.create_window( 0, 0, window=self.interior, anchor='nw' )

		# track changes to the canvas and frame width and sync them,
		# also updating the scrollbar
		self.interior.bind( '<Configure>', self._configure_interior )
		self.canvas.bind( '<Configure>', self._configure_canvas )

	def _configure_interior( self, event ):
		# Check if a scrollbar is necessary, and add/remove it as needed.
		if self.interior.winfo_height() > self.canvas.winfo_height():
			self.vscrollbar.pack( fill='y', side='left', expand=False )
			self.scrollFlag = True
		else:
			self.vscrollbar.pack_forget()
			self.scrollFlag = False # Disable scrolling until it's really needed again

		# update the scrollbar to match the size of the inner frame
		size = ( self.interior.winfo_reqwidth(), self.interior.winfo_reqheight() )
		self.canvas.config( scrollregion="0 0 %s %s" % size )

	def _configure_canvas( self, event ):
		if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
			# update the inner frame's width to fill the canvas
			self.canvas.itemconfigure( self.interior_id, width=self.canvas.winfo_width() )


def presentableModType( modType, changeType=False ):

	""" Converts a modType string to something presentable to a user.
		'chanteType=True' indicates that modType deals with a specific code change for a mod, 
		rather than the whole mod's classification. """

	if modType == 'static': modTypeTitle = 'Static Overwrite'
	elif modType == 'injection':
		if changeType:
			modTypeTitle = 'Injection'
		else: modTypeTitle = 'Injection Mod'
	elif modType == 'standalone':
		modTypeTitle = 'Standalone Function'
	elif modType == 'gecko': modTypeTitle = 'Gecko Code'
	else: modTypeTitle = modType

	return modTypeTitle


def cmsg( *args ):

	""" Expects arguments for message, title, alignment, and buttons. Only the first is required. """

	if len(args) == 4: CopyableMsg( root, message=args[0], title=args[1], alignment=args[2], buttons=args[3] )
	elif len(args) == 3: CopyableMsg( root, message=args[0], title=args[1], alignment=args[2] )
	elif len(args) == 2: CopyableMsg( root, message=args[0], title=args[1] )
	else: CopyableMsg( root, message=args[0] )


def createNewDolMod():
	# Create a tab for a new mod in the Mod Construction interface.
	newTab = ttk.Frame( constructionNotebook )
	constructionNotebook.add( newTab, text='New Mod' )

	# Bring the new tab into view for the user.
	constructionNotebook.select( newTab )

	ModConstructor( newTab, None ).pack( fill='both', expand=1 )


def getTabNames( notebook ):
	""" Returns a dictionary of 'key=mod name, value=tab index' """
	return { notebook.tab( tab, 'text' ): i for i, tab in enumerate( notebook.tabs() ) }


def getTabByName( notebook, tabName ):
	for windowName in notebook.tabs():
		targetTab = root.nametowidget( windowName ) # tabName == tab's text != windowName
		if notebook.tab( targetTab, option='text' ) == tabName: return targetTab
	else: return -1


def getCustomCodeRegions( searchDisabledRegions=False, specificRegion='', codelistStartPosShift=0, codehandlerStartPosShift=0 ):

	""" This gets the regions defined for custom code use (regions permitted for overwrites) in settings.py. Returned as a list of tuples of the 
		form (regionStart, regionEnd). The start position shifts (space reservations for the Gecko codelist/codehandler) should be counted in bytes. """

	codeRegions = []

	for regionName, regions in dol.customCodeRegions.items():

		# Check if this dol region should be included by its BooleanVar option value (or if that's overridden, which is the first check)
		if searchDisabledRegions or ( regionName in overwriteOptions and overwriteOptions[regionName].get() ):

			# Get all regions if specificRegion is not defined, or get only that region (or that group of regions)
			if not specificRegion or regionName == specificRegion: 

				# Offset the start of (thus excluding) areas that will be partially used by the Gecko codelist or codehandler
				if codelistStartPosShift != 0 and gecko.environmentSupported and regionName == gecko.codelistRegion:
					codelistRegionStart, codelistRegionEnd = regions[0]
					codelistRegionStart += codelistStartPosShift

					if codelistRegionEnd - codelistRegionStart > 0: # This excludes the first area if it was sufficiently shrunk
						codeRegions.append( (codelistRegionStart, codelistRegionEnd) )
					codeRegions.extend( regions[1:] ) # If there happen to be any more regions that have been added for this.

				elif codehandlerStartPosShift != 0 and gecko.environmentSupported and regionName == gecko.codehandlerRegion:
					codehandlerRegionStart, codehandlerRegionEnd = regions[0]
					codehandlerRegionStart += codehandlerStartPosShift

					if codehandlerRegionEnd - codehandlerRegionStart > 0: # This excludes the first area if it was sufficiently shrunk
						codeRegions.append( (codehandlerRegionStart, codehandlerRegionEnd) )
					codeRegions.extend( regions[1:] ) # If there happen to be any more regions that have been added for this.

				else:
					codeRegions.extend( regions )

				# If only looking for a specific revision, there's no need to iterate futher.
				if specificRegion: break

	return codeRegions


class RevisionPromptWindow( basicWindow ):

	""" Prompts the user to select a DOL region and version (together, these are the dol 'revision'). """

	def __init__( self, labelMessage, regionSuggestion='', versionSuggestion='' ):
		basicWindow.__init__( self, root, 'Select DOL Revision' )

		regionOptions = [ 'NTSC', 'PAL' ]
		if regionSuggestion not in regionOptions:
			regionOptions.append( regionSuggestion )

		ttk.Label( self.window, wraplength=240, text=labelMessage ).pack( padx=20, pady=12 )

		# Create variables for the region/version details
		self.regionChoice = StringVar()
		self.versionChoice = StringVar()
		self.regionChoice.set( regionSuggestion )
		self.versionChoice.set( '1.' + versionSuggestion )
		self.region = self.version = ''

		# Display the input widgets
		inputWrapper = ttk.Frame( self.window )
		OptionMenu( inputWrapper, self.regionChoice, *regionOptions ).pack( side='left', padx=8 )
		Spinbox( inputWrapper, textvariable=self.versionChoice, from_=1.0, to=1.99, increment=.01, width=4, format='%1.2f' ).pack( side='left', padx=8 )
		inputWrapper.pack( pady=(0,12) )

		# OK / Cancel buttons
		buttonsWrapper = ttk.Frame( self.window )
		ttk.Button( buttonsWrapper, text='OK', width=16, command=self.confirm ).pack( side='left', padx=8 )
		ttk.Button( buttonsWrapper, text='Cancel', width=16, command=self.close ).pack( side='left', padx=8 )
		buttonsWrapper.pack( pady=(0,12) )
		
		# Force focus away from the parent window and wait until the new window is closed to continue.
		self.window.grab_set()
		root.wait_window( self.window )

	# Define button functions
	def confirm( self ):
		self.region = self.regionChoice.get()
		self.version = self.versionChoice.get()
		self.window.destroy()


class ShowOptionsWindow( object ):

	""" Creates a modeless (non-modal) message window that allows the user to toggle 
		what regions are allowed to be overwritten by custom code. """

	def __init__( self ):
		if not dol.data:
			msg( 'A game file (ISO) or DOL must be loaded to view these options.' )

		elif root.optionsWindow == None:
			# Define the window.
			self.window = Toplevel()
			self.window.title( 'Code-Space Options' )
			self.window.attributes( '-toolwindow', 1 ) # Makes window framing small, like a toolbox/widget.
			self.window.resizable( width=False, height=False )

			# Calculate the spawning position of the new window
			rootDistanceFromScreenLeft, rootDistanceFromScreenTop = getWindowGeometry( root )[2:]
			self.window.geometry( '+' + str(rootDistanceFromScreenLeft + 180) + '+' + str(rootDistanceFromScreenTop + 180) )
			self.window.protocol( 'WM_DELETE_WINDOW', self.close ) # Overrides the 'X' close button.

			self.createContents()

		else: # The window must already exist. Make sure it's not minimized, and bring it to the foreground
			root.optionsWindow.window.deiconify()
			root.optionsWindow.window.lift()

	def createContents( self ):
		root.optionsWindow = self

		mainFrame = ttk.Frame( self.window, padding='15 0 15 0' ) # padding order: left, top, right, bottom
		Label( mainFrame, text='These are the regions that will be reserved (i.e. may be partially or fully overwritten) for injecting custom code. '
			'It is safest to uninstall all mods that may be installed to a region before disabling it. '
			'For more information on these regions, or to add your own, see the "settings.py" file.', wraplength=550 ).grid( columnspan=4, pady=12 )

		# Create the rows for each region option to be displayed.
		row = 1
		padx = 5
		pady = 3
		self.checkboxes = []
		for overwriteOptionName, boolVar in overwriteOptions.items():
			if overwriteOptionName == 'EnableGeckoCodes': continue
			elif overwriteOptionName not in dol.customCodeRegions: continue # An option is loaded for a region not available for the loaded DOL (todo: guess these loops should be reversed in their nesting)

			# The checkbox
			checkbox = ttk.Checkbutton( mainFrame, variable=boolVar, command=lambda regionName=overwriteOptionName: self.checkBoxClicked(regionName) )

			# Title
			Label( mainFrame, text=overwriteOptionName ).grid( row=row, column=1, padx=padx, pady=pady )

			# Check the space available with this region
			totalRegionSpace = 0
			tooltipText = []
			for i, region in enumerate( dol.customCodeRegions[overwriteOptionName], start=1 ):
				spaceAvailable = region[1] - region[0]
				totalRegionSpace += spaceAvailable
				tooltipText.append( 'Area ' + str(i) + ': ' + uHex(region[0]) + ' - ' + uHex(region[1]) + '  |  ' + uHex(spaceAvailable) + ' bytes' )

			# Create the label and tooltip for displaying the total region space and details
			regionSizeLabel = Label( mainFrame, text=uHex(totalRegionSpace) + '  Bytes', foreground='#777', font="-slant italic" )
			regionSizeLabel.grid( row=row, column=2, padx=padx, pady=pady )
			ToolTip( regionSizeLabel, delay=300, text='\n'.join(tooltipText), location='e', bg='#c5e1eb', follow_mouse=False, wraplength=1000 )

			# Restore button
			restoreBtn = ttk.Button( mainFrame, text='Restore', command=lambda regionName=overwriteOptionName: self.restoreRegions(regionName) )
			restoreBtn.grid( row=row, column=3, padx=padx, pady=pady )

			# Disable regions which are reserved for Gecko codes
			if overwriteOptions[ 'EnableGeckoCodes' ].get() and ( overwriteOptionName == gecko.codelistRegion or overwriteOptionName == gecko.codehandlerRegion ):
				checkbox['state'] = 'disabled'
				restoreBtn['state'] = 'disabled'
				checkbox.bind( '<1>', self.checkboxDisabledMessage )

			# Attach some info for later use
			checkbox.space = totalRegionSpace
			checkbox.regionName = overwriteOptionName
			checkbox.restoreBtn = restoreBtn
			checkbox.grid( row=row, column=0, padx=padx, pady=pady )

			self.checkboxes.append( checkbox )

			row += 1
		
		# Add the checkbox to enable Gecko codes
		if gecko.environmentSupported:
			self.enableGeckoChkBox = ttk.Checkbutton( mainFrame, text='Enable Gecko Codes', variable=overwriteOptions['EnableGeckoCodes'], command=self.toggleGeckoEngagement )
		else:
			self.enableGeckoChkBox = ttk.Checkbutton( mainFrame, text='Enable Gecko Codes', variable=overwriteOptions['EnableGeckoCodes'], command=self.toggleGeckoEngagement, state='disabled' )
		self.enableGeckoChkBox.grid( columnspan=4, pady=12 )

		# Add the total space label and the Details button to the bottom of the window
		lastRow = Frame( mainFrame )
		self.totalSpaceLabel = StringVar()
		self.calculateSpaceAvailable()
		Label( lastRow, textvariable=self.totalSpaceLabel ).pack( side='left', padx=11 )
		detailsLabel = Label( lastRow, text='Details', foreground='#03f', cursor='hand2' )
		detailsLabel.pack( side='left', padx=11 )
		detailsLabel.bind( '<1>', self.extraDetails )
		lastRow.grid( columnspan=4, pady=12 )

		mainFrame.pack()

	def checkBoxClicked( self, regionName ):
		# The program's checkbox boolVars (in overwriteOptions) has already been updated by the checkbox. However, the variables in the "settings"
		# object still need to be updated. saveOptions does this, as well as saves the settings to the options file.
		saveOptions()

		self.calculateSpaceAvailable()
		checkForPendingChanges( changesArePending=True )
		
		playSound( 'menuChange' )

	def toggleGeckoEngagement( self ):

		""" Called by the 'Enable Gecko Codes' checkbox when it changes state. When enabling, and either 
			of the gecko regions are not selected for use, prompt with a usage warning. """

		if overwriteOptions['EnableGeckoCodes'].get() and ( not overwriteOptions[ gecko.codelistRegion ].get() or not overwriteOptions[ gecko.codehandlerRegion ].get() ) :
			if dol.isMelee and ( gecko.codelistRegion == 'DebugModeRegion' or gecko.codehandlerRegion == 'DebugModeRegion'
								or gecko.codelistRegion == 'Debug Mode Region' or gecko.codehandlerRegion == 'Debug Mode Region' ): 
				meleeDetails = ( " Mostly, this just means that you won't be able to use the vanilla Debug Menu (if you're not "
								 "sure what that means, then you're probably not using the Debug Menu, and you can just click yes)." )
			else: meleeDetails = ''

			promptToUser = ( 'Enabling Gecko codes means that the regions assigned for Gecko codes, ' + gecko.codelistRegion + ' and ' + gecko.codehandlerRegion + ', '
				"will be reserved (i.e. may be partially or fully overwritten) for custom code." + meleeDetails + \
				'\n\nWould you like to enable these regions for overwrites in order to use Gecko codes?' )
		else: promptToUser = '' # Just going to use the following function to set some options & states (no prompt to the user)

		self.calculateSpaceAvailable()

		willUserAllowGecko( promptToUser, True, self.window ) # This will also check for pending changes, or for enabled codes (if gecko codes are allowed)
		
		playSound( 'menuChange' )

	def restoreRegions( self, regionName ):

		""" Called by the regions' "Restore" button. Restores custom code or zeroed out space for the chosen space back to vanilla code. """

		if dol.isMelee and regionName.replace( ' ', '' ) == 'ScreenshotRegions':
			noteOnScreenshotNops = 'The nops required to enable these regions will also be reverted.'
		else: noteOnScreenshotNops = ''

		restoreApproved = tkMessageBox.askyesno( 'Restoration Confirmation', 'This action will overwrite the region(s) defined by "' + regionName + '" with the '
			"game's default/vanilla hex, and deselect the region(s) so that they will not be used for custom code. Any custom code previously saved here "
			"will be moved to the next available region upon saving. " + noteOnScreenshotNops + "\n\nAre you sure you want to do this?", parent=self.window )
		if not restoreApproved:
			return

		# Update the option for whether or not this region should be used (and save this to file)
		overwriteOptions[ regionName ].set( False )
		saveOptions()

		# Restore nops if the regions being restored are the "screenshot" regions
		if dol.isMelee and regionName.replace( ' ', '' ) == 'ScreenshotRegions':
			# Commands at the points below were replaced with a nop to use this region. Restore them to vanilla
			screenshotRegionNopSites = { 'NTSC 1.03': (0x1a1b64, 0x1a1c50), 'NTSC 1.02': (0x1a1b64, 0x1a1c50), 'NTSC 1.01': (0x1a151c, 0x1a1608),
										'NTSC 1.00': (0x1a0e1c, 0x1a0f08), 'PAL 1.00':  (0x1a2668, 0x1a2754) }
			nopSites = screenshotRegionNopSites[ dol.revision ]
			nop0Hex = getVanillaHex( nopSites[0] ) # , revision=revisionList[0]
			nop1Hex = getVanillaHex( nopSites[1] )

			if not nop0Hex or not nop1Hex:
				msg( 'Unable to uninstall the ScreenshotRegion nops (at ' + hex(nopSites[0]) + ' and ' + hex(nopSites[1]) + '). This was likely because an original DOL for this game revision '
					'was not found in the original DOLs folder. In order to restore regions and look up vanilla code, you must place an original copy of the DOL here:'
					'\n\n' + dolsFolder + '\n\nThe filename should be "[region] [version].dol", for example, "NTSC 1.02.dol"', 'Unable to Uninstall ScreenshotRegion nops', self.window )
			else:
				replaceHex( nopSites[0], nop0Hex )
				replaceHex( nopSites[1], nop1Hex )

		# Restore each area in this region
		regionsUnrestored = []
		for regionStart, regionEnd in dol.customCodeRegions[ regionName ]:
			vanillaHex = getVanillaHex( regionStart, regionEnd - regionStart )

			if not vanillaHex:
				regionsUnrestored.append( uHex(regionStart) + '-' + uHex(regionEnd) )
			else:
				replaceHex( regionStart, vanillaHex )

		# Notify the user of any regions that could not be restored for some reason
		if regionsUnrestored:
			if dol.revision in originalDols:
				msg( "The regions below could not be restored. This is likely due to them being out of range of the DOL "
					"(i.e. pointing to an area beyond the end of the file).\n\n" + '\n'.join(regionsUnrestored), 'Unable to restore regions', self.window )

			else: # The revisions in revisionList don't appear to be loaded.
				msg( 'Some regions could not be restored. This was likely because an original DOL for this game revision '
					'was not found in the original DOLs folder. In order to restore regions and look up vanilla code, you must place an original '
					'copy of the DOL here:\n\n' + dolsFolder + '\n\nThe filename should be "[region] [version].dol", for example, "NTSC 1.02.dol". '
					'The regions below could not be restored:\n\n"' + '\n'.join(regionsUnrestored), 'Unable to Uninstall ScreenshotRegion nops', self.window )
		else:
			programStatus.set( 'Regions Successfully Restored' )

			playSound( 'menuSelect' )

		# Indicate to the program that changes have happened, so that the user can use the 'save' buttons.
		checkForPendingChanges( changesArePending=True )

	def checkboxDisabledMessage( self, event ):

		""" This will be executed on click events to the checkboxes for the regions assigned to the Gecko codelist and codehandler, since they will be disabled. """

		if overwriteOptions[ 'EnableGeckoCodes' ].get():
			msg( "You currently have Gecko codes enabled, which require use of this region. "
				 "You must uncheck the 'Enable Gecko codes' checkbox if you want to unselect this region.", "Can't let you do that, Star Fox!", self.window )

	def calculateSpaceAvailable( self ):
		space = 0
		for checkbox in self.checkboxes:
			if overwriteOptions[checkbox.regionName].get(): space += checkbox.space
		self.totalSpaceLabel.set( 'Total Space Available:   ' + uHex(space) + ' Bytes  (' + humansize(space) + ')' )
	
	def extraDetails( self, event ):
		msg( 'Each of the region options displayed here may be a single contiguous area in the DOL, or a collection of several areas (see settings.py for '
			'the exact definitions of each region). Regions assigned for the Gecko codehandler and codelist may be changed in the settings.py file under Gecko Configuration. '
			'However, if one of these is a group of areas, only the first contiguous area among the group will be used for the codehandler or codelist.'
			"""\n\nIf Gecko codes are used, you may notice that the "Total Space Available" shown here will be higher than what's reported by the Codes Free Space indicators in the """
			'main program window. That is because the free space indicators do not count space that will be assigned for the Gecko codehandler (' + uHex(gecko.codehandlerLength) + ' bytes), '
			'the codelist wrapper (0x10 bytes), or the codelist.', '', self.window )

	def close( self ):
		root.optionsWindow = None
		self.window.destroy()


def onWindowResize( event ):

	""" Fires when the window is resized (including maximize/restore functionality). 
		This is primarily used to update the position of the Mods Library's control panel. """

	# Reset the timer if it's already running
	if rootFrame.resizeTimer:
		rootFrame.after_cancel( rootFrame.resizeTimer )

	timeout = 0

	# Toggle the flag describing whether the program is maximized
	if root.state() == 'zoomed':
		root.maximized = True

	elif root.maximized: 
		# In this case, the root state is not zoomed (but the flag says it is), meaning the window must have just now been unmaximized
		root.maximized = False
		timeout = 100 	# Provide a slight delay before panel realignment if the program window is being unmaximized by dragging
						# This prevents a timing issue with root.update() in the alignment function, which would cause it to undo the unmaximize

	rootFrame.resizeTimer = rootFrame.after( timeout, realignControlPanel )
	

def onMouseWheelScroll( event ):

	""" Checks the widget under the mouse when a scroll event occurs, and then looks through the GUI geometry
		for parent widgets that may have scroll wheel support (indicated by the "scrollFlag" bool attribute). """

	# Cross-platform resources on scrolling:
		# - http://stackoverflow.com/questions/17355902/python-tkinter-binding-mousewheel-to-scrollbar
		# - https://www.daniweb.com/programming/software-development/code/217059/using-the-mouse-wheel-with-tkinter-python

	# Get the widget currently under the mouse
	widget = root.winfo_containing( event.x_root, event.y_root )

	# Traverse upwards through the parent widgets, looking for a scrollable widget
	while widget:
		if getattr( widget, 'scrollFlag', False ): # For a VerticalScrolledFrame widget
			widget = widget.canvas
			break

		elif widget.winfo_class() == 'Text': break

		widget = widget.master

	# If the above loop doesn't break (no scrollable found), widget will reach the top level item and become None.
	if widget:
		widget.yview_scroll( -1*(event.delta/30), "units" )


def selectAll( event ): # Adds bindings for normal CTRL-A functionality.
	if event.widget.winfo_class() == 'Text': event.widget.tag_add( 'sel', '1.0', 'end' )
	elif event.widget.winfo_class() == 'TEntry': event.widget.selection_range( 0, 'end' )


def playSoundHelper( soundFilePath ):

	""" Helper (thread-target) function for playSound(). Runs in a separate 
		thread to prevent audio playback from blocking main execution. """

	try:
		# Instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		wf = wave.open( soundFilePath, 'rb' )

		# Open an audio data stream (2)
		stream = p.open( format=p.get_format_from_width(wf.getsampwidth()),
						 channels=wf.getnchannels(),
						 rate=wf.getframerate(),
						 output=True )

		# Continuously read/write data from the file to the stream until there is no data left (3)
		data = wf.readframes( 1024 )
		while len( data ) > 0:
			stream.write( data )
			data = wf.readframes( 1024 )

		# Stop the stream (4)
		stream.stop_stream()
		stream.close()

		# Close PyAudio (5)
		p.terminate()

	except Exception as err:
		soundFileName = os.path.basename( soundFilePath )
		print 'Unable to play "{}" sound.'.format( soundFileName )
		print err


def playSound( soundFileName ):
	if not audioInitialized: return
	elif soundFileName not in soundBank:
		msg( 'The "{}" sound file could not be found in the "{}\\sfx" folder.'.format(soundFileName, scriptHomeFolder) )
		return

	# Play the audio clip in a separate thread so that it's non-blocking
	# (Yes, pyaudio has a "non-blocking" way for playback already, 
	# but that too blocks anyway due to waiting for the thread to finish.)
	audioThread = Thread( target=playSoundHelper, args=(soundBank[soundFileName],) )
	audioThread.start()


# Function definitions complete

																							 #===========#
																							# ~ ~ GUI ~ ~ #
																							 #===========#

if __name__ == '__main__':
	# Parse command line input
	import argparse
	cmdParser = argparse.ArgumentParser()
	cmdParser.add_argument( 'inputFile', nargs='?', help='an optional file path can be provided via command line or by drag-and-dropping onto the program icon' )
	cmdParser.add_argument( '-d', '--debugMode', action='store_true', help='creates a "Debug Log" text file for outputting various program debug and error messages' )
	cmdArgs = cmdParser.parse_args()

	root = Tk() # Instantiation of GUI program loop.
	root.withdraw() # Keep the GUI minimized until it is fully generated
	
	loadImageBank() # Must be loaded after root is initialized

	## Program icon and title display.
	root.tk.call( 'wm', 'iconphoto', root._w, imageBank['appIcon'] )
	root.title( " Melee Code Manager - v" + programVersion )
	root.resizable( width=True, height=True )
	root.geometry( '880x680' )
	root.minsize( width=640, height=620 )

	dnd = TkDND( root )

	rootFrame = ttk.Frame( root )
	rootFrame.resizeTimer = None

	root.stageSelectionsWindow = None # Used for later storage of the window.
	root.itemSelectionsWindow = None
	root.optionsWindow = None
	root.rumbleSelectionWindow = None
	root.maximized = False

	colorBank = {
		'freeSpaceIndicatorGood': '#c1ffb6',
		'freeSpaceIndicatorBad': '#ffcccc'
		#'altFontColor': '#d1cede' # A shade of silver; useful for high-contrast system themes
	}

	# Load the program's options and images.
	onlyUpdateGameSettings = BooleanVar()
	onlyUpdateGameSettings.set( False ) # Should be updated when the default settings are loaded (loadGeneralOptions())
	loadGeneralOptions()
	customCodeProcessor = CommandProcessor() # Must be initialized after gettings general settings, so the base include paths are set correctly

	# Set the program's default font size and color
	ttkStyle = ttk.Style()
	globalFontSize = int( settingsFile.globalFontSize )
	for font in tkFont.names():
		tkFont.nametofont( font ).configure( size=globalFontSize )
	
	# Set the program's default font color (todo: standardize label usage so this can be used. will still need other widget modifications for high contrast)
	# if settings.has_option( 'General Settings', 'altFontColor' ):
	# 	globalFontColor = settings.get( 'General Settings', 'altFontColor' )
		
	# 	# Validate the user color
	# 	try:
	# 		root.winfo_rgb( globalFontColor ) # Returns an RGB tuple if successful
	# 	except:
	# 		msg( 'The alternate color, "' + globalFontColor + '", is not a valid color. The string should be written as #RRGGBB, '
	# 			 'or a basic color such as, "blue", "teal", "orange", etc. The default font color will be used instead.' )
	# 		globalFontColor = '#071240'

	# 	# Set the new color for everything
	# 	ttkStyle.configure( '.', font="TkDefaultFont", foreground=globalFontColor )

	# Set some other global custom widget styling
	ttkStyle.map( "TNotebook.Tab", foreground=[("selected", '#03f')], padding=[('selected', 2)] )
	ttkStyle.configure( "TNotebook.Tab", foreground='#071240', padding=1 )
	ttkStyle.configure( 'pendingSave.TButton', background='#aaffaa' )
	ttkStyle.configure( 'red.TButton', background='#ee9999', bordercolor='#ee9999', foreground='red' )

	# Root Row 1 | File Input

	rootRow1 = ttk.Frame( rootFrame, padding="12 12 12 12" )

	openedFilePath = StringVar()
	ttk.Label( rootRow1, text="ISO / DOL:" ).pack( side='left' )
	fileEntry = ttk.Entry( rootRow1, textvariable=openedFilePath, font='TkTextFont', state='disabled' )
	fileEntry.pack( side='left', fill='x', expand=1, padx=12 )
	fileEntry.bind( '<Return>', openFileByField )
	mainOpenBtn = ttk.Button( rootRow1, text="Open", command=openFileByButton, width=14, state='disabled' )
	mainOpenBtn.pack()

	rootRow1.pack( fill='x', side='top' )

	# Root Row 2 |  Begin tabbed interface.

	mainNotebook = ttk.Notebook( rootFrame )

																														# Tab 1 | Mods Library

	modsLibraryTab = ttk.Frame( mainNotebook, takefocus=True )
	mainNotebook.add( modsLibraryTab, text=' Mods Library ', padding="0 0 0 0" ) # Padding: L, T, R, B

	modsLibraryTab.mainRow = ttk.Frame( modsLibraryTab )
	freeSpaceUsage = IntVar()
	freeSpaceUsage.set( 0 )
	freeSpaceIndicator = ttk.Progressbar( modsLibraryTab.mainRow, orient='vertical', mode='determinate', variable=freeSpaceUsage, maximum=100 )
	freeSpaceIndicator.pack( anchor='w', side='left', fill='y', padx=12, pady=9 )
	freeSpaceIndicator.toolTip = ToolTip( freeSpaceIndicator, delay=600, text='Standard Codes Free Space', location='n', bg=colorBank['freeSpaceIndicatorGood'], follow_mouse=True, wraplength=600 )

	freeGeckoSpaceUsage = IntVar()
	freeGeckoSpaceUsage.set( 0 )
	freeGeckoSpaceIndicator = ttk.Progressbar( modsLibraryTab.mainRow, orient='vertical', mode='determinate', variable=freeGeckoSpaceUsage, maximum=100 )
	freeGeckoSpaceIndicator.pack( anchor='w', side='left', fill='y', padx=(0, 12), pady=9 )
	freeGeckoSpaceIndicator.toolTip = ToolTip( freeGeckoSpaceIndicator, delay=600, text='Gecko Codes Free Space', location='n', bg=colorBank['freeSpaceIndicatorGood'], follow_mouse=True, wraplength=600 )

	modsLibraryNotebook = ttk.Notebook( modsLibraryTab.mainRow ) # Code module tabs will be children of this
	modsLibraryNotebook.pack( fill='both', expand=1, pady=7 )
	modsLibraryNotebook.bind( '<<NotebookTabChanged>>', onTabChange )
	modsLibraryNotebook.isScanning = False
	modsLibraryNotebook.stopToRescan = False

	modsLibraryTab.mainRow.pack( side='bottom', fill='both', expand=True )

				# - Control Panel -

	controlPanel = ttk.Frame( modsLibraryTab.mainRow, padding="20 8 20 20" ) # Padding: L, T, R, B

	programStatus = StringVar()
	programStatus.set( '' )
	Label( controlPanel, textvariable=programStatus, fg='#2a2').pack( pady=5 )

	ttk.Button( controlPanel, text='Open this File', command=openLibraryFile ).pack( pady=4, padx=6, ipadx=8 )
	ttk.Button( controlPanel, text='Open Mods Library Folder', command=openModsLibrary ).pack( pady=4, padx=6, ipadx=8 )

	ttk.Separator( controlPanel, orient='horizontal' ).pack( fill='x', padx=24, pady=7 )

	saveButtonsContainer = ttk.Frame( controlPanel, padding="0 0 0 0" )
	saveChangesBtn = ttk.Button( saveButtonsContainer, text='Save', command=saveCodes, state='disabled', width=12 )
	saveChangesBtn.pack( side='left', padx=6 )
	saveChangesAsBtn = ttk.Button( saveButtonsContainer, text='Save As...', command=saveAs, state='disabled', width=12 )
	saveChangesAsBtn.pack( side='left', padx=6 )
	saveButtonsContainer.pack( pady=4 )

	createFileContainer = ttk.Frame( controlPanel, padding="0 0 0 0" )
	ttk.Button( createFileContainer, text='Create INI', command=saveIniFile ).pack( side='left', padx=6 )
	ttk.Button( createFileContainer, text='Create GCT', command=saveGctFile ).pack( side='left', padx=6 )
	createFileContainer.pack( pady=4 )

	ttk.Separator( controlPanel, orient='horizontal' ).pack( fill='x', padx=24, pady=7 )

	restoreDolBtn = ttk.Button( controlPanel, text='Restore Original DOL', state='disabled', command=restoreOriginalDol, width=23 )
	restoreDolBtn.pack( pady=4 )
	importFileBtn = ttk.Button( controlPanel, text='Import into ISO', state='disabled', command=importIntoISO, width=23 )
	importFileBtn.pack( pady=4 )
	exportFileBtn = ttk.Button( controlPanel, text='Export DOL', state='disabled', command=exportDOL, width=23 )
	exportFileBtn.pack( pady=4 )

	ttk.Separator( controlPanel, orient='horizontal' ).pack( fill='x', padx=24, pady=7 )

	selectBtnsContainer = ttk.Frame( controlPanel, padding="0 0 0 0" )
	selectBtnsContainer.selectAllBtn = ttk.Button( selectBtnsContainer, text='Select All', width=12 )
	selectBtnsContainer.deselectAllBtn = ttk.Button( selectBtnsContainer, text='Deselect All', width=12 )
	selectBtnsContainer.selectAllBtn.pack( side='left', padx=6, pady=0 )
	selectBtnsContainer.deselectAllBtn.pack( side='left', padx=6, pady=0 )
	selectBtnsContainer.selectAllBtn.bind( '<Button-1>', selectAllMods )
	selectBtnsContainer.selectAllBtn.bind( '<Shift-Button-1>', selectWholeLibrary )
	selectBtnsContainer.deselectAllBtn.bind( '<Button-1>', deselectAllMods )
	selectBtnsContainer.deselectAllBtn.bind( '<Shift-Button-1>', deselectWholeLibrary )
	ToolTip( selectBtnsContainer.selectAllBtn, delay=600, justify='center', text='Shift-Click to select\nwhole library' )
	ToolTip( selectBtnsContainer.deselectAllBtn, delay=600, justify='center', text='Shift-Click to deselect\nwhole library' )
	selectBtnsContainer.pack( pady=4 )

	ttk.Button( controlPanel, text=' Rescan for Mods ', command=scanModsLibrary ).pack( pady=4 )

	showRegionOptionsBtn = ttk.Button( controlPanel, text=' Code-Space Options ', state='disabled', command=ShowOptionsWindow )
	showRegionOptionsBtn.pack( side='bottom' )

	installedModsTabLabel = StringVar()
	installedModsTabLabel.set( '' )
	ttk.Label( controlPanel, textvariable=installedModsTabLabel ).pack( side='bottom', pady=(0, 12) )

	# Mod Library selection button
	librarySelectionLabel = Label( modsLibraryTab.mainRow, image=imageBank['books'], cursor='hand2' )
	librarySelectionLabel.hoverText = StringVar()
	librarySelectionLabel.hoverText.set( 'Select Mods Library.\tCurrent library:\n' + getModsFolderPath() )
	librarySelectionLabel.bind( '<1>', lambda event: ModsLibrarySelector(root) )
	ToolTip( librarySelectionLabel, delay=600, justify='center', location='w', textvariable=librarySelectionLabel.hoverText, wraplength=600 )

				# - Control Panel end -
																														# Tab 2 | Mod Construction (Viewing / Editing)

	constructionTab = ttk.Frame( mainNotebook, takefocus=True )
	mainNotebook.add( constructionTab, text=' Mod Construction ' )

	constructionTab.row1 = Frame( constructionTab )
	ttk.Button( constructionTab.row1, text='Add New Mod to Library', command=createNewDolMod ).pack( side='left', ipadx=10, padx=20 )
	ttk.Button( constructionTab.row1, text='Open Mods Library Folder', command=openModsLibrary ).pack( side='left', ipadx=10, padx=20 )
	ttk.Button( constructionTab.row1, text='ASM <-> HEX Converter', command=lambda: AsmToHexConverter() ).pack( side='left', ipadx=10, padx=20 )
	ttk.Button( constructionTab.row1, text='Mod Search', command=enterSearchMode ).pack( side='left', ipadx=10, padx=20 )
	constructionTab.row1.pack( padx=16, pady=7 )

	constructionNotebook = ttk.Notebook( constructionTab )
	constructionNotebook.pack( fill='both', expand=1 )

	try:
		ttk.Label( constructionNotebook, image=imageBank['Bowser2'], background='white' ).place( relx=0.5, rely=0.5, anchor='center' )
	except: pass

																														# Tab 3 | Default Game Settings

	settingsTab = ttk.Frame( mainNotebook, takefocus=True )
	mainNotebook.add( settingsTab, text=' Default Game Settings ' )

	def initializeCurrentGameSettingsValues():
		for widgetSettingID in gameSettingsTable:
			currentGameSettingsValues[widgetSettingID] = StringVar()
			if widgetSettingID == 'stageToggleSetting' or widgetSettingID == 'itemToggleSetting': currentGameSettingsValues[widgetSettingID].set( 'FFFFFFFF' )
			else: currentGameSettingsValues[widgetSettingID].set( '- -' )

	currentGameSettingsValues = {}
	initializeCurrentGameSettingsValues()

	tab2Row1 = ttk.Frame( settingsTab, padding="17 25 20 0" ) # Padding: L, T, R, B

	settingsGroup1 = ttk.Labelframe( tab2Row1, text='  Custom Rules  ', labelanchor='n', padding=5 )

	Label( settingsGroup1, text='Game Mode:' ).grid( row=0, column=0 )
	gameModeControl = OptionMenu(settingsGroup1, currentGameSettingsValues['gameModeSetting'], 'Time', 'Stock', 'Coin', 'Bonus',
		command=lambda(value): updateDefaultGameSettingWidget( 'gameModeControl', value ))
	gameModeControl.grid(row=0, column=1)

	Label(settingsGroup1, text='Time Limit:').grid(row=1, column=0)
	gameTimeControl = Spinbox(settingsGroup1, from_=0, to=99, wrap=True, width=3, textvariable=currentGameSettingsValues['gameTimeSetting'], 
		command=lambda: updateDefaultGameSettingWidget( 'gameTimeControl', currentGameSettingsValues['gameTimeSetting'].get() ))
	gameTimeControl.grid(row=1, column=1)

	Label(settingsGroup1, text='Stock Count:').grid(row=2, column=0)
	stockCountControl = Spinbox(settingsGroup1, from_=0, to=99, wrap=True, width=3, textvariable=currentGameSettingsValues['stockCountSetting'], 
		command=lambda: updateDefaultGameSettingWidget( 'stockCountControl', currentGameSettingsValues['stockCountSetting'].get() ))
	stockCountControl.grid(row=2, column=1)

	Label(settingsGroup1, text='Handicap:').grid(row=3, column=0)
	handicapControl = OptionMenu(settingsGroup1, currentGameSettingsValues['handicapSetting'], 'Off', 'Auto', 'On', 
		command=lambda(value): updateDefaultGameSettingWidget( 'handicapControl', value ))
	handicapControl.grid(row=3, column=1)

	Label(settingsGroup1, text='Damage Ratio:').grid(row=4, column=0)
	damageRatioControl = Spinbox(settingsGroup1, from_=.5, to=2, increment=.1, wrap=True, width=3, textvariable=currentGameSettingsValues['damageRatioSetting'], 
		command=lambda: updateDefaultGameSettingWidget( 'damageRatioControl', currentGameSettingsValues['damageRatioSetting'].get() ))
	damageRatioControl.grid(row=4, column=1)

	Label(settingsGroup1, text='Stage Selection:').grid(row=5, column=0)
	stageSelectionControl = OptionMenu(settingsGroup1, currentGameSettingsValues['stageSelectionSetting'], 'On', 'Random', 'Ordered', 'Turns', 'Loser',
		command=lambda(value): updateDefaultGameSettingWidget( 'stageSelectionControl', value ))
	stageSelectionControl.grid(row=5, column=1)

	settingsGroup1.grid_columnconfigure(1, minsize=100)
	for widget in settingsGroup1.winfo_children():
		widget.grid_configure(padx=5, pady=5)

	settingsGroup1.grid( column=0, row=0 )

	# End of Group 1 / Start of Group 2

	settingsGroup2 = Frame(tab2Row1)

	additionalRules = ttk.Labelframe(settingsGroup2, text='  Additional Rules  ', labelanchor='n', padding=5)

	Label(additionalRules, text='Stock Time Limit:').grid(row=0, column=0)
	stockTimeControl = Spinbox(additionalRules, from_=0, to=99, wrap=True, width=3, textvariable=currentGameSettingsValues['stockTimeSetting'], 
		command=lambda: updateDefaultGameSettingWidget( 'stockTimeControl', currentGameSettingsValues['stockTimeSetting'].get() ))
	stockTimeControl.grid(row=0, column=1)

	Label(additionalRules, text='Friendly Fire:').grid(row=1, column=0)
	friendlyFireControl = OptionMenu(additionalRules, currentGameSettingsValues['friendlyFireSetting'], 'Off', 'On', 
		command=lambda(value): updateDefaultGameSettingWidget( 'friendlyFireControl', value ))
	friendlyFireControl.grid(row=1, column=1)

	Label(additionalRules, text='Pause:').grid(row=2, column=0)
	pauseControl = OptionMenu(additionalRules, currentGameSettingsValues['pauseSetting'], 'Off', 'On', 
		command=lambda(value): updateDefaultGameSettingWidget( 'pauseControl', value ))
	pauseControl.grid(row=2, column=1)

	Label(additionalRules, text='Score Display:').grid(row=3, column=0)
	scoreDisplayControl = OptionMenu(additionalRules, currentGameSettingsValues['scoreDisplaySetting'], 'Off', 'On', 
		command=lambda(value): updateDefaultGameSettingWidget( 'scoreDisplayControl', value ))
	scoreDisplayControl.grid(row=3, column=1)

	Label(additionalRules, text='Self-Destructs:').grid(row=4, column=0)
	selfDestructsControl = OptionMenu(additionalRules, currentGameSettingsValues['selfDestructsSetting'], '0', '-1', '-2', 
		command=lambda(value): updateDefaultGameSettingWidget( 'selfDestructsControl', value ))
	selfDestructsControl.grid(row=4, column=1)

	additionalRules.grid_columnconfigure(1, minsize=80)
	for widget in additionalRules.winfo_children():
		widget.grid_configure(padx=5, pady=5)

	additionalRules.pack()

	settingsGroup2.grid( column=1, row=0, pady=15 )

	# End of Group 2 / Start of Group 3

	tab2Row1.buttonsGroup = Frame(tab2Row1)

	programStatusLabel = Label( tab2Row1.buttonsGroup, textvariable=programStatus, fg='#2a2' )
	programStatusLabel.pack( pady=8 )

	ttk.Button( tab2Row1.buttonsGroup, text=' Set to vMelee \nGame Defaults', command=updateMeleeToVanillaGameSettings, width=20 ).pack( pady=7 )
	ttk.Button( tab2Row1.buttonsGroup, text='      Set to standard \nTournament Defaults', command=updateMeleeToTournamentGameSettings, width=20 ).pack()

	ttk.Separator( tab2Row1.buttonsGroup, orient='horizontal' ).pack( fill='x', padx=0, pady=14 )

	saveButtonsContainer2 = ttk.Frame( tab2Row1.buttonsGroup, padding="0 0 0 0" )
	saveChangesBtn2 = ttk.Button( saveButtonsContainer2, text='Save', command=saveCodes, state='disabled', width=12 )
	saveChangesBtn2.pack( side='left', padx=12 )
	saveChangesAsBtn2 = ttk.Button( saveButtonsContainer2, text='Save As...', command=saveAs, state='disabled', width=12 )
	saveChangesAsBtn2.pack( side='left', padx=12 )
	saveButtonsContainer2.pack()

	ttk.Checkbutton( tab2Row1.buttonsGroup, onvalue=True, offvalue=False, variable=onlyUpdateGameSettings,
		text='  Update Default\n  Game Settings Only', command=onUpdateDefaultGameSettingsOnlyToggle ).pack( pady=15 )

	tab2Row1.buttonsGroup.grid( column=2, row=0 )

	tab2Row1.columnconfigure( 'all', weight=1 )
	
	tab2Row1.pack( anchor='n', fill='x' )

	# The widget below exists so that this setting may be controlled/processed like all the others. It is then "mimicked" in the item selections window.
	itemFrequencyMimic = StringVar()
	itemFrequencyMimic.set( '- -' )
	itemFrequencyControl = OptionMenu( tab2Row1, currentGameSettingsValues['itemFrequencySetting'], 
				'None', 'Very Low', 'Low', 'Medium', 'High', 'Very High', 'Very Very High', 'Extremely High' )

	# End of Tab 2, Row 1 / Start of Row 2

	tab2Row2 = Frame(settingsTab)

	stageToggleControl = ttk.Button( tab2Row2, text='Random Stage Selection', command=openStageSelectionWindow, width=30 )
	stageToggleControl.pack( side='left', padx=18, pady=0 )

	itemToggleControl = ttk.Button( tab2Row2, text='Item Switch', command=openItemSelectionsWindow, width=30 )
	itemToggleControl.pack( side='left', padx=18, pady=0 )

	# gameSettingsDefaults = {} # For a more concise solution, code for the other settings could eventually be switched to use this, or combined with the gameSettingsTable
	rumbleToggleControl = ttk.Button( tab2Row2, text='Rumble Settings', command=rumbleSelectWindow, width=30 )
	rumbleToggleControl.pack( side='left', padx=18, pady=0 )

	tab2Row2.pack(anchor='n', pady=12)

	# End of Tab 2, Row 2 / Start of Row 3

	try: # Place the bobomb images
		tab2Row3 = Frame(settingsTab)
		Label( tab2Row3, image=imageBank['bobombsSitting'] ).place( relx=.333, y=50, anchor='n' )
		Label( tab2Row3, image=imageBank['bobombWalking'] ).place( relx=.667, y=35, anchor='n' )
		tab2Row3.pack( fill='both', expand=True )
	except Exception as err:
		print 'Wait! Where da bob-ombs!?'
		print err
																														# Tab 4 | Summary

	summaryTab = ttk.Frame( mainNotebook, padding="15 0 15 12", takefocus=True )
	mainNotebook.add( summaryTab, text=' Summary ' )

	summaryTabFirstRow = ttk.Frame( summaryTab )
	totalModsInLibraryLabel = StringVar()
	totalModsInstalledLabel = StringVar()
	totalModsInLibraryLabel.set( 'Total Mods in Library: 0' )
	totalModsInstalledLabel.set( 'Mods Installed:' )

	Label( summaryTabFirstRow, textvariable=totalModsInLibraryLabel ).grid( column=0, row=0, sticky='w' )
	Label( summaryTabFirstRow, textvariable=totalModsInstalledLabel ).grid( column=0, row=1, sticky='w' )

	summaryTabFirstRow.rightColumnFrame = ttk.Frame( summaryTabFirstRow )
	ttk.Button( summaryTabFirstRow.rightColumnFrame, text='Create Installed Mods List', command=showInstalledModsList, state='disabled' ).pack( side='left', ipadx=12, padx=5 )
	ttk.Button( summaryTabFirstRow.rightColumnFrame, text='Install Mods List', command=installModsList, state='disabled' ).pack( side='left', ipadx=12, padx=5 )
	ttk.Button( summaryTabFirstRow.rightColumnFrame, text='View DOL Hex', command=viewDolHex, state='disabled' ).pack( side='left', ipadx=12, padx=5 ) #.pack( side='right', , padx=75 )
	summaryTabFirstRow.rightColumnFrame.grid( column=1, row=0, rowspan=2, sticky='e' )

	summaryTabFirstRow.pack( fill='x', padx=65, pady=9 )
	summaryTabFirstRow.columnconfigure( 0, weight=1 )
	summaryTabFirstRow.columnconfigure( 1, weight=1 )

	# Create the Mods Summary table
	modsSummaryRow = ttk.Frame( summaryTab, padding='10 0 10 0' )
	modsSummaryScroller = Scrollbar( modsSummaryRow )
	modsSummaryTree = ttk.Treeview( modsSummaryRow, columns=('type', 'location', 'bytesChanged', 'spaceUsed'), selectmode='none',
													yscrollcommand=modsSummaryScroller.set ) # First icon column, #0, included by default
	if settings.getboolean( 'General Settings', 'sortSummaryByOffset' ):
		modsSummaryTree.heading( '#0', anchor='center', text='Mod Name / Component Owner' )
	else: modsSummaryTree.heading( '#0', anchor='center', text='Mod Name' )
	modsSummaryTree.column( '#0', anchor='center', minwidth=280, stretch=1 )
	modsSummaryTree.heading( 'type', anchor='center', text='Type' )
	modsSummaryTree.column( 'type', anchor='center', minwidth=60, stretch=0, width=60 )
	def toggleSummaryLocationSortMethod():
		sortModsSummaryByOffset( not settings.getboolean( 'General Settings', 'sortSummaryByOffset' ) )
	# Determine the starting text for the location (DOL/RAM Offset) column
	if settings.get( 'General Settings', 'summaryOffsetView' ).lstrip()[0].lower().startswith( 'd' ): # 'd' for dolOffset
		modsSummaryTree.heading( 'location', anchor='center', text='DOL Offset', command=toggleSummaryLocationSortMethod )
	else: modsSummaryTree.heading( 'location', anchor='center', text='RAM Address', command=toggleSummaryLocationSortMethod )
	modsSummaryTree.column( 'location', anchor='center', minwidth=110, stretch=0, width=110 )
	modsSummaryTree.heading( 'bytesChanged', anchor='center', text='Bytes Changed' )
	modsSummaryTree.column( 'bytesChanged', anchor='center', minwidth=110, stretch=0, width=110 )
	modsSummaryTree.heading( 'spaceUsed', anchor='center', text='Free Space Used' )
	modsSummaryTree.column( 'spaceUsed', anchor='center', minwidth=120, stretch=0, width=110 )
	modsSummaryTree.pack( side='left', fill='both', expand=True )
	modsSummaryScroller.config( command=modsSummaryTree.yview )
	modsSummaryScroller.pack( side='left', fill='y' )
	modsSummaryRow.pack( fill='both', expand=True )
	modsSummaryTree.originalSortOrder = []

	requiredStandaloneFunctionsLabel = StringVar()
	requiredStandaloneFunctionsLabel.set( 'Required Standalone Functions for the Installed Mods:' )
	Label( summaryTab, textvariable=requiredStandaloneFunctionsLabel ).pack( padx=135, pady=(7, 7), anchor='w' )

	standalonesSummaryRow = ttk.Frame( summaryTab, padding='80 0 80 0' )
	standalonesSummaryScroller = Scrollbar( standalonesSummaryRow )
	standalonesSummaryTree = ttk.Treeview( standalonesSummaryRow, selectmode='none', columns=('refCount', 'location'), yscrollcommand=standalonesSummaryScroller.set )
	standalonesSummaryTree.heading( '#0', anchor='center', text='Function Name' )
	standalonesSummaryTree.column( '#0', anchor='center', minwidth=290, stretch=1 )
	standalonesSummaryTree.heading( 'refCount', anchor='center', text='Reference Count' )
	standalonesSummaryTree.column( 'refCount', anchor='center', minwidth=110, stretch=1 )
	standalonesSummaryTree.heading( 'location', anchor='center', text='Installation location (DOL Offset)' )
	standalonesSummaryTree.column( 'location', anchor='center', minwidth=220, stretch=1 )
	standalonesSummaryTree.pack( side='left', fill='both', expand=True )
	standalonesSummaryScroller.config( command=standalonesSummaryTree.yview )
	standalonesSummaryScroller.pack( side='left', fill='y' )
	standalonesSummaryRow.pack( fill='x', expand=True )

	modsSummaryContextMenu = summaryContextMenu( root )

	# Define some colors and an event handler for the above treeviews
	modsSummaryTree.tag_configure( 'selected', background='#b9c3ff' ) # more blue; takes priority over lower config
	modsSummaryTree.tag_configure( 'mainEntry', background='#d9e3ff' ) # light blue
	modsSummaryTree.bind( '<1>', updateSummaryTreeSelection )
	modsSummaryTree.bind( '<3>', onModSummaryTreeRightClick )

	standalonesSummaryTree.tag_configure( 'selected', background='#b9c3ff' ) # more blue; takes priority over lower config
	standalonesSummaryTree.tag_configure( 'mainEntry', background='#d9e3ff' ) # light blue
	standalonesSummaryTree.bind( '<1>', updateSummaryTreeSelection )
	standalonesSummaryTree.bind( '<3>', onStandalonesSummaryTreeRightClick )

																														# Tab 5 | Tools

	toolsTab = ttk.Frame( mainNotebook, padding="15 9 15 9", takefocus=True )
	mainNotebook.add( toolsTab, text=' Tools ' )

	toolsTab.row1 = Frame( toolsTab )
	numberConverter = ttk.Labelframe(toolsTab.row1, text='  Number Conversion  ', labelanchor='n', padding="15 12 15 10")

	Label(numberConverter, text='Decimal:').grid(row=0,column=0)
	decimalNum = StringVar()
	ttk.Entry(numberConverter, width=19, textvariable=decimalNum, font='TkTextFont').grid(row=0,column=1)
	Label(numberConverter, text='Hex (unsigned):').grid(row=1,column=0)
	hexNum = StringVar()
	ttk.Entry(numberConverter, width=19, textvariable=hexNum, font='TkTextFont').grid(row=1,column=1)
	Label(numberConverter, text='32-bit float:\n(signed)').grid(row=2,column=0)
	floatNum = StringVar()
	ttk.Entry(numberConverter, width=19, textvariable=floatNum, font='TkTextFont').grid(row=2,column=1)
	Label(numberConverter, text='64-bit float:\n(signed double)').grid(row=3,column=0)
	doubleNum = StringVar()
	ttk.Entry(numberConverter, width=19, textvariable=doubleNum, font='TkTextFont').grid(row=3,column=1)

	numberConverterChildren = numberConverter.winfo_children()
	numberConverterChildren[1].bind("<KeyRelease>", lambda event: convertDec( event, decimalNum ))
	numberConverterChildren[3].bind("<KeyRelease>", lambda event: convertHex( event, hexNum ))
	numberConverterChildren[5].bind("<KeyRelease>", lambda event: convertFloat( event, floatNum ))
	numberConverterChildren[7].bind("<KeyRelease>", lambda event: convertDouble( event, doubleNum ))

	numberConverter.grid(row=0, column=0, sticky='e' )

	offsetConverter = ttk.Labelframe( toolsTab.row1, text='  RAM Address Conversion  ', labelanchor='n', padding="15 12 15 0" ) # Padding: L, T, R, B

	def populateRamAddressConverter():
		ttk.Label( offsetConverter, text='RAM Address:' ).grid( row=0, column=0 )
		entry = ttk.Entry( offsetConverter, width=12, font='TkTextFont' )
		entry.grid( row=0, column=1 )

		ttk.Label( offsetConverter, text='DOL Offsets:     ' ).grid( row=1, column=0, columnspan=2 )

		genGlobals['originalDolRevisions'] = listValidOriginalDols()

		if len( genGlobals['originalDolRevisions'] ) < 6: pady = 1
		else: pady = 0
		
		ramToDolNotesLabel = ttk.Label( offsetConverter, textvariable=ramToDolNotes, justify='center' )

		# Add an entry field for conversion input for each DOL found in the Original DOLs folder
		if genGlobals['originalDolRevisions']:
			entry.bind( "<KeyRelease>", convertRamOffset )

			for i, dolRevision in enumerate( genGlobals['originalDolRevisions'] ):
				ttk.Label( offsetConverter, text=dolRevision ).grid( row=i+2, column=0 )
				entry = ttk.Entry( offsetConverter, width=13, font='TkTextFont' )
				entry.grid( row=i+2, column=1, pady=pady )
				entry.bind( "<KeyRelease>", convertDolOffset )

			ramToDolNotesLabel.grid( row=len(genGlobals['originalDolRevisions'])+3, column=0, columnspan=2 )
		else:
			entry['state'] = 'disabled'
			ramToDolNotes.set( 'Unavailable; no\noriginal DOLs found.' )
			ramToDolNotesLabel.grid( row=3, column=0, columnspan=2, pady=(8, 14) )

	ramToDolNotes = StringVar()
	populateRamAddressConverter()

	offsetConverter.grid( row=0, column=1 )

	codeOffsetConverter = ttk.Labelframe( toolsTab.row1, text='  Code Offset Conversion  ', labelanchor='n', padding=15 )

	def populateCodeOffsetConverter():
		if len( genGlobals['originalDolRevisions'] ) < 6: pady = 1
		else: pady = 0

		# Add an entry field for conversion input for each DOL found in the Original DOLs folder
		if genGlobals['originalDolRevisions']:
			for i, dolRevision in enumerate( genGlobals['originalDolRevisions'] ):
				ttk.Label( codeOffsetConverter, text=dolRevision ).grid( row=i, column=0 )
				entry = ttk.Entry( codeOffsetConverter, width=13, font='TkTextFont' )
				entry.grid( row=i, column=1, pady=pady )
				entry.revision = dolRevision
				entry.bind( "<Return>", convertCodeOffset )
			Label( codeOffsetConverter, text="(Press 'Enter' to search)" ).grid( row=i+1, column=0, columnspan=2 )
		else:
			Label( codeOffsetConverter, text='Unavailable; no\noriginal DOLs found.' ).grid( row=0, column=0, columnspan=2 )

	populateCodeOffsetConverter()

	codeOffsetConverter.grid( row=0, column=2, sticky='w' )

	toolsTab.row1.columnconfigure( 0, weight=1 )
	toolsTab.row1.columnconfigure( 1, weight=1 )
	toolsTab.row1.columnconfigure( 2, weight=1 )
	toolsTab.row1.rowconfigure( 0, weight=1 )

	toolsTab.row1.pack( fill='x', pady=(15, 0) )

	toolsTab.row3 = Frame( toolsTab )

	Label( toolsTab.row3, text='\t\tASCII Text to Hex:', foreground='#03f' ).pack( anchor='nw', pady=(0, 3) )
	text2hex = ScrolledText( toolsTab.row3, height=3, borderwidth=2, relief='groove' )
	text2hex.pack( fill='both', expand=True, padx=3, pady=0 )
	hex2text = ScrolledText( toolsTab.row3, height=3, borderwidth=2, relief='groove' )
	hex2text.pack( fill='both', expand=True, padx=3, pady=5 )
	text2hex.bind( '<KeyRelease>', text2hexConv )
	hex2text.bind( '<KeyRelease>', text2hexConv )

	Label( toolsTab.row3, text="\t\tMenu Text to Hex:", foreground='#03f' ).pack( anchor='nw', pady=3 )
	menuText2hex = ScrolledText( toolsTab.row3, height=3, borderwidth=2, relief='groove' )
	menuText2hex.pack( fill='both', expand=True, padx=3, pady=0 )
	hex2menuText = ScrolledText( toolsTab.row3, height=3, borderwidth=2, relief='groove' )
	hex2menuText.pack( fill='both', expand=True, padx=3, pady=5 )
	menuText2hex.bind( '<KeyRelease>', menuText2hexConv )
	hex2menuText.bind( '<KeyRelease>', menuText2hexConv )

	toolsTab.row3.pack( fill='both', expand=1, padx=6 )

	# End of tabbed interface.

	mainNotebook.pack( fill='both', expand=1 )
	mainNotebook.bind( '<<NotebookTabChanged>>', onTabChange )

	rootFrame.pack( fill='both', expand=1 )

	def dndHandler( event ):
		root.deiconify() # Brings the main program window to the front (application z-order).
		readRecievedFile( event.data )
		playSound( 'menuChange' )

	dnd.bindtarget( rootFrame, dndHandler, 'text/uri-list' )
	rootFrame.bind( "<Configure>", onWindowResize )

	discVersion = StringVar()
	discVersion.set( '' )
	Label( mainNotebook, textvariable=discVersion ).place( anchor='center', x=610, y=14 )
	dolVersion = StringVar()
	dolVersion.set( 'Nothing Loaded' )
	Label( mainNotebook, textvariable=dolVersion ).place( anchor='center', x=694, y=14 )

																# GUI Rendering complete. Initialize program bindings and variables.

	root.deiconify()

	# Scrollwheel and 'CTRL-A' support.
	root.unbind_class( 'Text', '<MouseWheel>' ) # The global onMouseWheelScroll below will handle this too. Prevents problems when scrolling on top of other widgets
	root.bind_all( "<MouseWheel>", onMouseWheelScroll )
	root.bind_all( "<Control-s>", saveCurrentWork )
	root.bind( "<Control-f>", enterSearchMode )
	root.bind( "<Escape>", exitSearchMode )
	root.bind_class( "Text", "<Control-a>", selectAll )
	root.bind_class( "TEntry", "<Control-a>", selectAll )

	# Initialize the dol and gecko information containers (essentially containers for globals and specific file-reading functions)
	dol = dolInitializer()
	gecko = geckoInitializer()
	originalDols = {} # Container for the original DOL files, which are used for code references

	# Set up logging output (comment this out if compiling while preserving the console)
	if sys.argv[0][-4:] == '.exe': # If this code has been compiled....
		if cmdArgs.debugMode:
			sys.stdout = sys.stderr = open( 'Debug Log.txt', 'a' )
		else:
			# Nullify stdout and stderr, to prevent any odd errors
			class NullWriter( object ):
				def write( self, value ): pass
			sys.stdout = sys.stderr = NullWriter()

	# Initialize the program's audio
	audioInitialized = False
	try:
		for fileNameWithExt in os.listdir( scriptHomeFolder + '\\sfx' ): # listdir gets folders too, but there aren't any expected here.
			if fileNameWithExt.endswith( '.wav' ):
				fileName = os.path.splitext( fileNameWithExt )[0] # No file extension
				soundBank[fileName] = scriptHomeFolder + '\\sfx\\' + fileNameWithExt
		audioInitialized = True

	except Exception as e:
		print 'Problem playing audio; audio drivers might not be installed or no sound device is available.'
		print str(e)

	# Either disable the Mods Library tab or populate the program with the available mods.
	if onlyUpdateGameSettings.get():
		mainNotebook.tab( 0, state='disabled' )
	else:
		scanModsLibrary( playAudio=False )

	# Process any files drag-and-dropped onto the program icon (or provided via command line)
	if cmdArgs.inputFile:
		readRecievedFile( sys.argv[-1] )

	# Enable the GUI's file input
	fileEntry['state'] = 'normal'
	mainOpenBtn['state'] = 'normal'

	# Start the GUI's mainloop
	fileEntry.focus()
	playSound( 'menuChange' )
	root.mainloop()
