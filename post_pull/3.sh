#!/bin/bash

set -e
echo "Drop spconf table in sp_users if it exists"

mysql -uroot sp_users << EOF 
DROP TABLE IF EXISTS spconf;
EOF
