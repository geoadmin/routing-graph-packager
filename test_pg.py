#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import sys, os

p = dict(
    host=os.getenv('POSTGRES_PASS') or 'localhost',
    port=os.getenv('POSTGRES_PASS') or 5432,
    database=os.getenv('POSTGRES_DB') or 'gis_test',
    user=os.getenv('POSTGRES_USER') or 'admin',
    password=os.getenv('POSTGRES_PASS') or 'admin',
)
print(p)
con = psycopg2.connect(**p)

cur = con.cursor()
cur.execute('SELECT PostGIS_full_version();')
print(cur.fetchone())