#!/bin/bash
cd /c/Users/meili/forked/ca-biositing
git fetch upstream feat--feedstock_etl
git show upstream/feat--feedstock_etl:alembic/versions/ > /tmp/upstream_files.txt 2>&1
ls -la /tmp/upstream_files.txt
