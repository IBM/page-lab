#! /usr/bin/env bash

python3 manage.py dumpdata auth.User auth.Group report --indent 4 > report/fixtures/fixture-for-dev.json