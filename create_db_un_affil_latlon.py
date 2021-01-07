#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Create SQL database if it does not exist
from pathlib import Path
import sqlite3

from puboracle.writestoredata import readwritefun

db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'unique_affiliations.db'
conn_affiliations = readwritefun.sql_create_db(db_folder,
                                               db_filename = db_filename
                                              )

# Create table publications if it does not exists
sql_table = """ CREATE TABLE IF NOT EXISTS affiliations (
                                   affiliation text,
                                   latitude real,
                                   longitude real
                               ); """

readwritefun.sql_create_table(conn_affiliations, 
                              sql_table = sql_table
                              )

# Get a coursor to the newly created db
cursor_affiliations = conn_affiliations.cursor()

# Database from where the affiliations should be read
db_filename_publications = 'ndays_pubmed_noprimary.db'
conn_publications = sqlite3.connect(db_folder / db_filename_publications)
cursor_publications = conn_publications.cursor()
cursor_publications.execute("SELECT affiliations FROM publications")
nr_rows = 100
affiliations_delimeter = ';'

while 1:
    rows = cursor_publications.fetchmany(nr_rows)
    for i,row in enumerate(rows):
        unique_affiliations = []
        print('\n\nProcessing row nr:',i)
        print(row)
        affils = row[0].split(';')
        affils = list(set(affils))
        # Check if these unique affils exists in the affilaitions_db
        for a in affils:
            cursor_affiliations.execute("SELECT COUNT(*) FROM affiliations WHERE affiliation = ?", (a,))
            count = cursor_affiliations.fetchone()
            if count[0] == 0: unique_affiliations.append((a,0,0))
        # Enter the rows that do not exist in the affiliations db
        if unique_affiliations:
            sql_insert = 'INSERT INTO affiliations VALUES(?,?,?);'
            readwritefun.sql_insert_many_to_table(sql_insert, 
                                                  rows = unique_affiliations, 
                                                  conn = conn_affiliations
                                                 )
            
    if not rows: break


cursor_affiliations.close()
cursor_publications.close()

conn_affiliations.close()
conn_publications.close()




