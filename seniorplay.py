#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           seniorplay
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation.  A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import sys, os, shlex
sys.path.insert(0, "..")
# This is only for debian testing as we don't have an official pygame 1.9 package.
# I've created my own debian package for pygame 1.9 which lives in
# python/site-packages so we can use both, isn't that cool :-)
sys.path.insert(1,'/usr/lib/python2.6/site-packages')
# Now python finds the pygame 1.9 package first.
# It's ignored when there's no such path

if sys.argv > 2:
    # construct proper restart command if we need to restart
    prog = "python %s " % os.path.join(os.getcwd(), " ".join(sys.argv))
        
import subprocess
#import gc
#gc.set_debug(gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS)
# first parse commandline options
from SPOptionParser import OParser
# if this doesn't bail out the options are correct and we continue with schoolsplay

op = OParser()
# this will return a class object with the options as attributes  
CMD_Options = op.get_options()

######## Here we add options for debugging #####
### Must be removed or at least discussed before release #####
#CMD_Options.loglevel = 'debug'
# TODO: remove this when the login is using SPWidgets iso ocempgui
#CMD_Options.no_login = True
#if not CMD_Options.user:
#    CMD_Options.user = 'BT_user'
#CMD_Options.nocountdown = True

import sqlalchemy
import time
import SPLogging
SPLogging.set_level(CMD_Options.loglevel)
SPLogging.start()

#create logger, configuration of logger was done above
import logging
CPmodule_logger = logging.getLogger("schoolsplay.seniorplay")
CPmodule_logger.debug("Created schoolsplay loggers")

#CPmodule_logger.info("IMPORTANT READ THE FOLLOWING LINES")
#CPmodule_logger.info("For debugging purposes we run with some cmdline options hardcoded.")
#CPmodule_logger.info("These must be removed before releasing this to the real world")
#CPmodule_logger.info("Look at the top of this module for these options")

if CMD_Options.loglevel == 'debug':
    from SPConstants import *
    CPmodule_logger.debug("Paths defined in SPConstants:")
    for v in ['ACTIVITYDATADIR', 'ALPHABETDIR', 'BASEDIR',\
               'DBASEPATH', 'HOMEDIR', 'HOMEIMAGES', 'HOME_DIR_NAME',\
               'LOCALEDIR', 'LOCKFILE', 'PYTHONCPDIR']:
        CPmodule_logger.debug("%s > %s" % (v, eval(v)))

# Rudimentary language check, when it fails it sets the cmdline option to C                                                                                 
# which is available on every proper GNU/Linux system. We don't have yet a dbase 
# connection at this stage so we just check if the locale is properly formed.
# We don't care about windows of course that system locale handling sucks anyway.
loc = CMD_Options.lang
if loc.find('_') == -1 or loc.upper().find('utf8') == -1:
    pass

import pygame
## set a bigger buffer, seems that on win XP in conjuction with certain hardware
## the playback of sound is scrambled with the "normal" 1024 buffer.
###  XXXX this still sucks, signed or unsigned that's the question :-(
pygame.mixer.pre_init(22050, -16, 2, 2048)
pygame.init()

import utils
# this will return the tuple (lang,rtl=bool)
LANG = utils.set_locale(lang=CMD_Options.lang)

if CMD_Options.checklog:
    try:
        import SPlogCheck
    except (ImportError, utils.SPError):
        sys.exit(1)
    except utils.MyError:
        sys.exit(1)
    sys.exit(0)

if CMD_Options.admingui:
    # This will not return
    try:
        import gui.AdminGui as AdminGui
        AdminGui.main()
    except Exception,info:
        print "GUI raised an exception"
        print info
        sys.exit(1)
    else:
        sys.exit(0)
        
if not utils._set_lock():
    sys.exit(1)
    
import SPMainCore

from SPgdm import GDMEscapeKeyException

# start the maincore, we only return here on an exit
CPmodule_logger.debug("Start logging")
CPmodule_logger.debug("commandline options: %s" % CMD_Options)
CPmodule_logger.debug("SPMainCore running from: %s" % SPMainCore)

mainscreen = None
abort = 0 
while not abort:
    restartme = False   
    try:
        # there's no support for other resolutions then 800x600
        mcgui = SPMainCore.MainCoreGui(resolution=(800,600),\
                                        options=CMD_Options,\
                                        mainscr=mainscreen)
        mainscreen = mcgui.get_mainscreen()
        mcgui.start()
    except SPMainCore.MainEscapeKeyException:
        CPmodule_logger.info("User hits exit/escape...")
        if CMD_Options.no_login or CMD_Options.user:
            # we have no login screen or the user was passed as a cmdline option so we exit
            #sys.exit(0)
            abort = True
            CPmodule_logger.info("nologin screen, clean exit")
        elif CMD_Options.theme == 'childsplay':
            CPmodule_logger.info("Theme is childsplay, clean exit")
            abort = True
        else:
            CPmodule_logger.info("restarting core after 1.0 sec.")
    except GDMEscapeKeyException:
        CPmodule_logger.info("login screen, clean exit")
        break
    except utils.RestartMeException:
        CPmodule_logger.info("GIT pull occurred, need to restart myself.")
        restartme = True
        abort = True
    except (SystemExit, utils.StopmeException),status:
        if str(status) == '0':
            CPmodule_logger.info("systemexit, clean exit")
            abort = True
        else:
            CPmodule_logger.info("systemexit, not a clean exit")
            abort = True
    except utils.SPError, info:
        CPmodule_logger.error("Unrecoverable error, not a clean exit")
        abort = True
    except Exception,status:        
        CPmodule_logger.exception("unhandled exception in toplevel, traceback follows:")
        abort = True
       
try:
    mcgui.activity.stop_timer()
except Exception, info:
    CPmodule_logger.warning("Failed to stop activity timers")
    
CPmodule_logger.info("Seniorplay stopped.")

#from SPWidgets import Dialog
#
#try:
#    import SPlogCheck
#except (ImportError, utils.SPError):
#    text = _("Failed to parse the logfile, please contact the developers.\nMessage was: %s" % info)
#    dlg = Dialog(text, buttons=[_('OK')], title=_('Warning !'))
#    dlg.run()
#except utils.MyError, info:
#    text = "%s" % info
#    #dlg.run()
CPmodule_logger.debug("quiting pygame and waiting 0.5 seconds.")
pygame.quit()
time.sleep(0.5)
#if sys.platform == "linux2":
#    CPmodule_logger.info("Removing pyc files")
#    subprocess.Popen('find . -name "*.pyc" -exec rm {} \;',shell=True )

# BT+ specific stuff
if CMD_Options.theme == 'braintrainer' and restartme:
    restartme = False
    CPmodule_logger.info("respawing in one second with :%s" % prog)
    pid = subprocess.Popen(prog, shell=True).pid
    CPmodule_logger.debug("launched Control Panel with pid %s" % pid)
    sys.exit()
