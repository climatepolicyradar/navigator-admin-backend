#!/bin/bash
#

cd $(git rev-parse --show-toplevel) || exit
NAV=../navigator-backend

# Squirrel away this file to restore later
cp app/clients/db/models/app/authorisation.py /tmp

# remove the engire db model
rm -rf app/clients/db/models

# copy new db model
cp -r "${NAV}"/app/db/models app/clients/db/models
# restore the file - TODO: we shoud really move this methinks
cp /tmp/authorisation.py app/clients/db/models/app/authorisation.py

# update import paths
find app/clients/db/models/ -name '*.py' -exec sed -i 's/ app\.db/ app.clients.db/g' {} \;
