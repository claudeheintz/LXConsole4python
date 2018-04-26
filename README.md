# LXConsole4python
LXConsole|Python is an implementation of LXConsole for Raspberry Pi.  It is distributed as Python source code and can run on any system with Python installed.  (LXConsole for Python depends on the tkinter module for the GUI)

# Instructions for Raspberry Pi

The pylx folder should be located in the /home/pi/ directory for the desktop file to work properly.  After unzipping you need to log out and back in for the desktop file's icon to show properly.

You may need to set execute permissions on the lxconsole.py file.  To do this, right click and choose properties.  Then, select the permissions tab.  Check the box that says "Make the file executable"  Once you've done that, you should be able to double-click the desktop launcher to run the application.  (see note above about the icon) You can move this file to another location, only the source files have to stay in /home/pi/pylx unless you edit the desktop file and supply a replacement path.

The initial configuration is for 300 channels and 512 dimmers.  Output is broadcast Art-Net on 10.255.255.255.  You can edit the lxconsole.properties file to change these settings.

In order for the output to work properly, you need to setup an ethernet interface with an appropriate static ip address and netmask.  The staticip.sh shell file can do this for you.  (You may need to do Properties->Permissions->Make this file executable in order to double-click to execute the script.)  You can also type the following commands into a terminal:

sudo ifconfig eth0 add 10.1.110.132
sudo ifconfig eth0:0 netmask 255.0.0.0


LXConsole|Python has a very basic command line interface.  A summary is available from the menu Help->Quick Help.


# Running LXConsole!Python on other platforms

You can run LXConsole!Python on other platforms through the command line.  On OS X (and other unix type operating systems) the command might look like this if you uncompress pylx.zip to the desktop:

$ python /Users/username/Desktop/pylx/lxconsole.py

(of course, you cave to replace username with your own)

# DMX USB Pro support

DMXUSBPro compatible version requires pyserial https://pypi.python.org/pypi/pyserial. The lxconsole.properties file should be edited at the line widget=<inteface location>. The included file is set for ttyUSB0 on Linux.  On Linux, ttyUSB0 may be owned by root.  To write to it, you may need to add your username to the dialout group.  Using the terminal use the command

sudo adduser $USER dialout
