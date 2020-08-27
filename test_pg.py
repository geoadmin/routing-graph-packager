#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import sys, os

p = dict(
    host='localhost',
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASS')
)
con = psycopg2.connect(**p)

cur = con.cursor()
cur.execute('SELECT PostGIS_full_version();')
print(cur.fetchone())