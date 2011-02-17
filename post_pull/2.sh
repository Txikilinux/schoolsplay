#!/bin/bash

set -e
echo "Drop languages table in btp_content if it exists"

mysql -uroot btp_content << EOF 
DROP TABLE IF EXISTS languages;
EOF
