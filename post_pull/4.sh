#!/bin/bash

set -e
echo "Updating content dbase, this can take a while..."
cd ./lib/CPData/DbaseAssets
mysql -uroot btp_content < btp_content_qiosq.sql

./updateImages.sh
./updateSounds.sh

