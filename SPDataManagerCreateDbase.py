# -*- coding: utf-8 -*-

# Copyright (c) 2007-2010 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           SPDataManagerCreateDbase.py
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
#create logger, logger was configured in SPLogging
import os

import logging
module_logger = logging.getLogger("schoolsplay.SPDataManagerCreateDbase")
from SPConstants import ACTIVITYDATADIR, USERSDBASE, HOMEDIR, WHICHDBASE, CONTENTDBASE

from utils import MyError, read_rcfile
try:
    import sqlalchemy as sqla
    import sqlalchemy.exceptions as sqlae
    import sqlalchemy.orm as sqlorm
except ImportError:
    module_logger.exception("No sqlalchemy package found")
    raise MyError
else:
    if sqla.__version__ < '0.5':
        module_logger.error("Found sqlalchemy version %s" % sqla.__version__)
        module_logger.error("Your version of sqlalchemy is to old, please upgrade to version >= 0.4")
        raise MyError
    module_logger.debug("using sqlalchemy %s" % sqla.__version__)

import SQLTables
import SPORMs

# determine which dbase to use, we support mySQL and SQLite
USEMYSQL = False
USESQLITE = False
rc_hash = ''

if WHICHDBASE == 'mysql':
    try:
        import MySQLdb, _mysql_exceptions
    except ImportError:
        module_logger.exception("No MySQLdb package found which is needed by sqlalchemy")
        module_logger.error("The WHICHDBASE constant is set in SPConstants to 'mysql'")
        raise MyError
    else:
        module_logger.info("Using mySQL for the user dbase")
        USEMYSQL = True
        # suppress warnings from MySQLdb which seems to use Python warnings iso exceptions
        import warnings
        warnings.filterwarnings("ignore")
        if os.path.exists('db.conf'):
            dbp = 'db.conf'
            kind = 'production'
        else:
            dbp = 'db.dev'
            kind = 'develop'
        rc_hash = read_rcfile(dbp)
        rc_hash['kind'] = kind
        rc_hash['path'] = dbp
else:
    module_logger.info("Using SQLite for the user dbase")
    USESQLITE = True

class DbaseMaker:
    def __init__(self, theme, debug_sql=False):
        self.logger = logging.getLogger("schoolsplay.SPDataManagerCreateDbase.DbaseMaker")
        self.logger.debug("Starting")
        self.usersdbasepath= os.path.join(HOMEDIR, theme, USERSDBASE)
        self.contentdbasepath = os.path.join(HOMEDIR, theme, CONTENTDBASE)
        # We could also use a mysql dbase, local or remote
        try:
            ##### start userdb stuff ########
            if USESQLITE:
                self.logger.debug("Starting SQLite users dbase, %s" % self.usersdbasepath)
                engine = sqla.create_engine('sqlite:///%s' % self.usersdbasepath)
            elif USEMYSQL:
                self.logger.info("Starting mySQL dbase, %s" % rc_hash['default']['dbasename_users'])
                import MySQLdb, _mysql_exceptions
                self.logger.info("Using conffile %s" % rc_hash['path'])
                db=MySQLdb.connect(host=rc_hash['default']['host_users'], \
                                   user=rc_hash['default']['user_sp_users'], \
                                   passwd=rc_hash['default']['user_sp_users_pass'])
                c = db.cursor()
                c.execute('''CREATE DATABASE IF NOT EXISTS %s''' % rc_hash['default']['dbasename_users'])
                
                db.close()
                url = 'mysql://%s:%s@%s/%s' %\
                                    (rc_hash['default']['user_sp_users'], \
                                    rc_hash['default']['user_sp_users_pass'], \
                                    rc_hash['default']['host_users'], \
                                    rc_hash['default']['dbasename_users'])
                engine = sqla.create_engine(url)
            else:
                self.logger.error("I'm confused about which dbase to use, please check your settings in SPConstants and make sure you have all the dependencies installed")
                raise MyError
            # The rest is the same for all dbases thanks to sqlalchemy  
            self.metadata_usersdb = sqla.MetaData(engine)
            self.metadata_usersdb.bind.echo = debug_sql
            sqltb = SQLTables.SqlTables(self.metadata_usersdb)
            # returns lookup table to get table objects by name and creates tables
            self.orms_userdb = sqltb._create_userdb_tables(self.metadata_usersdb)
            self.user_engine = engine
            #self._check_tables_uptodate()
            #### end userdb stuff#####
            #### start contentdb stuff #####
            if USESQLITE:
                self.logger.debug("Starting SQLite content dbase, %s" % self.contentdbasepath)
                engine = sqla.create_engine('sqlite:///%s' % self.contentdbasepath)
            elif USEMYSQL:
                engine = sqla.create_engine('mysql://%s:%s@%s/%s' %\
                                        (rc_hash['default']['user_btp_content'], \
                                        rc_hash['default']['user_btp_content_pass'], \
                                        rc_hash['default']['host_content'], \
                                        rc_hash['default']['dbasename_content']))
                
            self.metadata_contentdb = sqla.MetaData(engine)
            self.metadata_contentdb.bind.echo = debug_sql
            self.orms_content_db = SQLTables.create_contentdb_orms(self.metadata_contentdb)
            self.content_engine = engine
            ##############################
            self.all_orms = {}
            self.all_orms.update(self.orms_userdb)
            self.all_orms.update(self.orms_content_db)
        except (AttributeError, sqlae.SQLAlchemyError), info:
            self.logger.exception("Failed to start the DBase, %s" % info)
            raise MyError, info
            
    def get_engines(self):
        return(self.content_engine, self.user_engine)
    def get_all_orms(self):
        return self.all_orms
    def get_orms(self):
        return (self.orms_content_db, self.orms_userdb)
    def get_metadatas(self):
        return (self.metadata_contentdb, self.metadata_usersdb)
        
        
        
            
