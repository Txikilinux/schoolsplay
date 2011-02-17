#!/bin/bash
set -e

# What must be done when we upgrade to this release
# When you break stuff between upgrades you must provide a solution.
############## from 2.1.1

# The layout of the .schoolsplay.rc is changed.
# The user dbase sen_sp.db is changed so we must remove it
# (In the future we will preserve data but we don't collect stuff for real in 2.1
echo "removing .schoolsplay.rc"
rm -rf ~/.schoolsplay.rc

# we changed the format of the year col from varchar to int so that we can
# make queries like 1940 < orm.year < 1950
echo "Changing game_quizhistory year col from varchar to int."
mysql -uroot btp_content << EOF 
ALTER TABLE game_quizhistory CHANGE year year INT( 4 ) NOT NULL;
EOF

# Drop sp_users as there are many changes.
echo "Drop sp_users dbase"
mysql -uroot sp_users << EOF 
DROP DATABASE IF EXISTS sp_users;
EOF

