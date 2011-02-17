#!/bin/bash
set -e

# What must be done when we upgrade to this release
# When you break stuff between upgrades you must provide a solution.
############## from 2.2
echo "Drop spconf table in sp_users if it exists"

mysql -uroot sp_users << EOF 
DROP TABLE IF EXISTS spconf;
EOF
