#!/usr/bin/python
# This Python file uses the following encoding: utf-8

							# ------------------------------------------------------------------- #
						   # ~ ~ Written by DRGN of SmashBoards (Daniel R. Cappel);  Feb, 2020 ~ ~ #
						   #			    Original ToolTip module by Michael Lange			   #
							#       -       -       [Python v2.7.9 & 2.7.12]      -       -       #
							# ------------------------------------------------------------------- #

import Tkinter
import ttk
from ScrolledText import ScrolledText

version = 1.0

def getWindowGeometry( topLevelWindow ):

	""" Returns a tuple of ( width, height, distanceFromScreenLeft, distanceFromScreenTop ) """

	try:
		dimensions, topDistance, leftDistance = topLevelWindow.geometry().split( '+' )
		width, height = dimensions.split( 'x' )
		geometry = ( int(width), int(height), int(topDistance), int(leftDistance) ) # faster than above line
	except:
		raise ValueError( "Failed to parse window geometry string: " + topLevelWindow.geometry() )

	return geometry


class basicWindow( object ): # todo: expand on this and use it for more windows

	""" Basic user window setup. Provides a title, a window with small border framing, size/position 
		configuration, a mainFrame frame widget for attaching contents to, and a built-in close method. 

			'dimensions' are window dimentions, which can be supplied as a tuple of (width, height)
			'offsets' relate to window spawning position, which is relative to the main program window,
				and can be supplied as a tuple of (leftOffset, topOffset). """

	def __init__( self, topLevelWindow, windowTitle='', dimensions='auto', offsets='auto', resizable=False, topMost=True ):
		self.window = Tkinter.Toplevel( topLevelWindow )
		self.window.title( windowTitle )
		self.window.attributes( '-toolwindow', 1 ) # Makes window framing small, like a toolbox/widget.
		self.window.resizable( width=resizable, height=resizable )
		if topMost:
			self.window.wm_attributes( '-topmost', 1 )

		rootDistanceFromScreenLeft, rootDistanceFromScreenTop = getWindowGeometry( topLevelWindow )[2:]

		# Set the spawning position of the new window (usually such that it's over the program)
		if offsets == 'auto':
			topOffset = rootDistanceFromScreenTop + 180
			leftOffset = rootDistanceFromScreenLeft + 180
		else:
			leftOffset, topOffset = offsets
			topOffset += rootDistanceFromScreenTop
			leftOffset += rootDistanceFromScreenLeft

		# Set/apply the window width/height and spawning position
		if dimensions == 'auto':
			self.window.geometry( '+{}+{}'.format(leftOffset, topOffset) )
		else:
			width, height = dimensions
			self.window.geometry( '{}x{}+{}+{}'.format(width, height, leftOffset, topOffset) )
		self.window.focus()

		self.window.protocol( 'WM_DELETE_WINDOW', self.close ) # Overrides the 'X' close button.

	def close( self ):
		self.window.destroy()


class CopyableMsg( basicWindow ):

	""" Creates a modeless (non-modal) message window that allows the user to easily copy the given text. 
		If buttons are provided, they should be an iterable of tuples of the form (buttonText, buttonCallback). """

	def __init__( self, root, message='', title='', alignment='center', buttons=None ):
		super( CopyableMsg, self ).__init__( root, title, resizable=True, topMost=False )
		self.root = root

		if alignment == 'left':
			height = 22 # Expecting a longer, more formal message
		else: height = 14

		# Add the main text display of the window
		self.messageText = ScrolledText( self.window, relief='groove', wrap='word', height=height )
		self.messageText.insert( '1.0', message )
		self.messageText.tag_add( 'All', '1.0', 'end' )
		self.messageText.tag_config( 'All', justify=alignment )
		self.messageText.pack( fill='both', expand=1 )

		# Add the buttons
		self.buttonsFrame = Tkinter.Frame( self.window )
		ttk.Button( self.buttonsFrame, text='Close', command=self.close ).pack( side='right', padx=5 )
		if buttons:
			for buttonText, buttonCommand in buttons:
				ttk.Button( self.buttonsFrame, text=buttonText, command=buttonCommand ).pack( side='right', padx=5 )
		ttk.Button( self.buttonsFrame, text='Copy text to Clipboard', command=self.copyToClipboard ).pack( side='right', padx=5 )
		self.buttonsFrame.pack( pady=3 )

	def copyToClipboard( self ):
		self.root.clipboard_clear()
		self.root.clipboard_append( self.messageText.get('1.0', 'end') )


class PopupEntryWindow( basicWindow ):

	""" Creates a modal dialog window with just a single-line text input field, with Ok/Cancel buttons.
		Useful for displaying text that the user should be able to select/copy, or for user input. """

	def __init__( self, master, message='', defaultText='', title='', width=100 ):
		basicWindow.__init__( self, master, windowTitle=title )
		self.entryText = ''

		self.label = ttk.Label( self.window, text=message, justify='center' )
		self.label.pack( pady=5 )
		self.entry = ttk.Entry( self.window, width=width )
		self.entry.insert( 'end', defaultText )
		self.entry.pack( padx=10, pady=10 )
		self.entry.bind( '<Return>', self.cleanup )

		buttonsFrame = ttk.Frame( self.window )
		self.okButton = ttk.Button( buttonsFrame, text='Ok', command=self.cleanup )
		self.okButton.pack( side='left', padx=10 )
		ttk.Button( buttonsFrame, text='Cancel', command=self.cancel ).pack( side='left', padx=10 )
		buttonsFrame.pack( pady=5 )

		# Move focus to this window (for keyboard control), and pause execution of the calling function until this window is closed.
		self.entry.focus_set()
		master.wait_window( self.window ) # Pauses execution of the calling function until this window is closed.

	def cleanup( self, event='' ):
		self.entryText = self.entry.get()
		self.window.destroy()

	def cancel( self, event='' ):
		self.entryText = ''
		self.window.destroy()


class PopupScrolledTextWindow( basicWindow ):

	""" Creates a modal dialog window with only a multi-line text input box (with scrollbar), and a few buttons.
		Useful for displaying text that the user should be able to select/copy, or for input. """

	def __init__( self, master, message='', defaultText='', title='', width=100, height=8, button1Text='Ok' ):
		basicWindow.__init__( self, master, windowTitle=title )
		self.entryText = ''

		# Add the explanation text and text input field
		self.label = ttk.Label( self.window, text=message )
		self.label.pack( pady=5 )
		self.entry = ScrolledText( self.window, width=width, height=height )
		self.entry.insert( 'end', defaultText )
		self.entry.pack( padx=5 )

		# Add the confirm/cancel buttons
		buttonsFrame = ttk.Frame( self.window )
		self.okButton = ttk.Button( buttonsFrame, text=button1Text, command=self.cleanup )
		self.okButton.pack( side='left', padx=10 )
		ttk.Button( buttonsFrame, text='Cancel', command=self.cancel ).pack( side='left', padx=10 )
		buttonsFrame.pack( pady=5 )

		# Move focus to this window (for keyboard control), and pause execution of the calling function until this window is closed.
		self.entry.focus_set()
		master.wait_window( self.window ) # Pauses execution of the calling function until this window is closed.

	def cleanup( self, event='' ):
		self.entryText = self.entry.get( '1.0', 'end' ).strip()
		self.window.destroy()

	def cancel( self, event='' ):
		self.entryText = ''
		self.window.destroy()


class ToolTip:

	''' 
		This class provides a flexible tooltip widget for Tkinter; it is based on IDLE's ToolTip
		module which unfortunately seems to be broken (at least the version I saw).

		Original author: Michael Lange <klappnase (at) freakmail (dot) de>
		Modified slightly by Daniel R. Cappel, including these additions:
		- 'remove' method, 'location' option, multi-monitor support, live update of textvariable, and a few other changes
		The original class is no longer available online, however a simplified adaptation can be found here:
			https://github.com/wikibook/python-in-practice/blob/master/TkUtil/Tooltip.py
			
	INITIALIZATION OPTIONS:
	anchor :        where the text should be positioned inside the widget, must be one of "n", "s", "e", "w", "nw" and so on;
					default is "center"
	bd :            borderwidth of the widget; default is 1 (NOTE: don't use "borderwidth" here)
	bg :            background color to use for the widget; default is "lightyellow" (NOTE: don't use "background")
	delay :         time in ms that it takes for the widget to appear on the screen when the mouse pointer has
					entered the parent widget; default is 1500
	fg :            foreground (i.e. text) color to use; default is "black" (NOTE: don't use "foreground")
	follow_mouse :  if set to 1 the tooltip will follow the mouse pointer instead of being displayed
					outside of the parent widget; this may be useful if you want to use tooltips for
					large widgets like listboxes or canvases; default is 0
	font :          font to use for the widget; default is system specific
	justify :       how multiple lines of text will be aligned, must be "left", "right" or "center"; default is "left"
	location :      placement above or below the target (master) widget. values may be 'n' or 's' (default)
	padx :          extra space added to the left and right within the widget; default is 4
	pady :          extra space above and below the text; default is 2
	relief :        one of "flat", "ridge", "groove", "raised", "sunken" or "solid"; default is "solid"
	state :         must be "normal" or "disabled"; if set to "disabled" the tooltip will not appear; default is "normal"
	text :          the text that is displayed inside the widget
	textvariable :  if set to an instance of Tkinter.StringVar() the variable's value will be used as text for the widget
	width :         width of the widget; the default is 0, which means that "wraplength" will be used to limit the widgets width
	wraplength :    limits the number of characters in each line; default is 150

	WIDGET METHODS:
	configure(**opts) : change one or more of the widget's options as described above; the changes will take effect the
						next time the tooltip shows up; NOTE: 'follow_mouse' cannot be changed after widget initialization
	remove() :          removes the tooltip from the parent widget

	Other widget methods that might be useful if you want to subclass ToolTip:
	enter() :           callback when the mouse pointer enters the parent widget
	leave() :           called when the mouse pointer leaves the parent widget
	motion() :          is called when the mouse pointer moves inside the parent widget if 'follow_mouse' is set to 1 and 
						the tooltip has shown up to continually update the coordinates of the tooltip window
	coords() :          calculates the screen coordinates of the tooltip window
	create_contents() : creates the contents of the tooltip window (by default a Tkinter.Label)

	Ideas gleaned from PySol

	Other Notes:
		If text or textvariable are empty or not specified, the tooltip will not show. '''

	version = '1.6.1'

	def __init__( self, master, text='Your text here', delay=1500, **opts ):
		self.master = master
		self._opts = {'anchor':'center', 'bd':1, 'bg':'lightyellow', 'delay':delay, 'fg':'black',
					  'follow_mouse':0, 'font':None, 'justify':'left', 'location':'s', 'padx':4, 'pady':2,
					  'relief':'solid', 'state':'normal', 'text':text, 'textvariable':None,
					  'width':0, 'wraplength':150}
		self.configure(**opts)
		self._tipwindow = None
		self._id = None
		self._id1 = self.master.bind("<Enter>", self.enter, '+')
		self._id2 = self.master.bind("<Leave>", self.leave, '+')
		self._id3 = self.master.bind("<ButtonPress>", self.leave, '+')
		self._follow_mouse = 0
		if self._opts['follow_mouse']:
			self._id4 = self.master.bind("<Motion>", self.motion, '+')
			self._follow_mouse = 1

		# Monitor changes to the textvariable, if one is used (for dynamic updates to the tooltip's position)
		if self._opts['textvariable']:
			self._opts['textvariable'].trace( 'w', lambda nm, idx, mode: self.update() )

	def configure(self, **opts):
		for key in opts:
			if self._opts.has_key(key):
				self._opts[key] = opts[key]
			else:
				KeyError = 'KeyError: Unknown option: "%s"' %key
				raise KeyError

	def remove(self):
		#self._tipwindow.destroy()
		self.leave()
		self.master.unbind("<Enter>", self._id1)
		self.master.unbind("<Leave>", self._id2)
		self.master.unbind("<ButtonPress>", self._id3)
		if self._follow_mouse:
			self.master.unbind("<Motion>", self._id4)

	##----these methods handle the callbacks on "<Enter>", "<Leave>" and "<Motion>"---------------##
	##----events on the parent widget; override them if you want to change the widget's behavior--##

	def enter(self, event=None):
		self._schedule()

	def leave(self, event=None):
		self._unschedule()
		self._hide()

	def motion(self, event=None):
		if self._tipwindow and self._follow_mouse:
			x, y = self.coords()
			self._tipwindow.wm_geometry("+%d+%d" % (x, y))

	def update(self, event=None):
		tw = self._tipwindow
		if not tw: return

		if self._opts['text'] == 'Your text here' and not self._opts['textvariable'].get():
			self.leave()
		else:
			tw.withdraw()
			tw.update_idletasks() # to make sure we get the correct geometry
			x, y = self.coords()
			tw.wm_geometry("+%d+%d" % (x, y))
			tw.deiconify()

	##------the methods that do the work:---------------------------------------------------------##

	def _schedule(self):
		self._unschedule()
		if self._opts['state'] == 'disabled': return
		self._id = self.master.after(self._opts['delay'], self._show)

	def _unschedule(self):
		id = self._id
		self._id = None
		if id:
			self.master.after_cancel(id)

	def _show(self):
		if self._opts['state'] == 'disabled' or \
			( self._opts['text'] == 'Your text here' and not self._opts['textvariable'].get() ):
			self._unschedule()
			return
		if not self._tipwindow:
			self._tipwindow = tw = Tkinter.Toplevel(self.master)
			self._tipwindow.wm_attributes( '-topmost', 1 )
			# hide the window until we know the geometry
			tw.withdraw()
			tw.wm_overrideredirect(1)

			if tw.tk.call("tk", "windowingsystem") == 'aqua':
				tw.tk.call("::tk::unsupported::MacWindowStyle", "style", tw._w, "help", "none")

			self.create_contents()
			tw.update_idletasks()
			x, y = self.coords()
			tw.wm_geometry("+%d+%d" % (x, y))
			tw.deiconify()

	def _hide(self):
		tw = self._tipwindow
		self._tipwindow = None
		if tw:
			tw.destroy()

	##----these methods might be overridden in derived classes:----------------------------------##

	def coords(self):
		# The tip window must be completely outside the master widget;
		# otherwise when the mouse enters the tip window we get
		# a leave event and it disappears, and then we get an enter
		# event and it reappears, and so on forever :-(
		# or we take care that the mouse pointer is always outside the tipwindow :-)

		tw = self._tipwindow
		twWidth, twHeight = tw.winfo_reqwidth(), tw.winfo_reqheight()
		masterWidth, masterHeight = self.master.winfo_reqwidth(), self.master.winfo_reqheight()
		if 's' in self._opts['location'] or 'e' in self._opts['location']:
			cursorBuffer = 32 # Guestimate on cursor size, to ensure no overlap with it (or the master widget if follow_mouse=False)
		else: cursorBuffer = 2
		# if self._follow_mouse: # Tooltip needs to be well out of range of the cursor, to prevent triggering the original widget's leave event
		# 	cursorBuffer += 32

		# Establish base x/y coords
		if self._follow_mouse: # Sets to cursor coords
			x = self.master.winfo_pointerx()
			y = self.master.winfo_pointery()

		else: # Sets to widget top-left screen coords
			x = self.master.winfo_rootx()
			y = self.master.winfo_rooty()

		# Offset the tooltip location from the master (target) widget, so that it is not over the top of it
		if 'w' in self._opts['location'] or 'e' in self._opts['location']:
			if self._follow_mouse:
				if 'w' in self._opts['location']:
					x -= ( twWidth + cursorBuffer )

				else: x += cursorBuffer

				# Center y coord relative to the mouse position
				y -= ( twHeight / 2 - 8 )

			else:
				# Place the tooltip completely to the left or right of the target widget
				if 'w' in self._opts['location']:
					x -= ( twWidth + cursorBuffer )

				else: x += masterWidth + cursorBuffer

				# Vertically center tooltip relative to master widget
				y += ( masterHeight / 2 - twHeight / 2 )

		else: # No horizontal offset, so the tooltip must be placed above or below the target to prevent problems
			if 'n' in self._opts['location']: # place the tooltip above the target
				y -= ( twHeight + cursorBuffer )
				
			else:
				y += cursorBuffer

			# Horizontally center tooltip relative to master widget
			x += ( masterWidth / 2 - twWidth / 2 )

		return x, y

	def create_contents(self):
		opts = self._opts.copy()
		for opt in ('delay', 'follow_mouse', 'state', 'location'):
			del opts[opt]
		label = Tkinter.Label(self._tipwindow, **opts)
		label.pack()