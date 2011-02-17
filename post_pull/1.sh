#!/bin/bash

set -e
echo "Updating btp_content with btp_content_qiosq.sql"
mysql -uroot btp_content < ./lib/CPData/DbaseAssets/btp_content_qiosq.sql


