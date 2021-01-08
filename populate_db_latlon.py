#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sqlite3

from puboracle.txtprocess import txt2geo

db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'unique_affiliations.db'
nr_rows = 100

conn = sqlite3.connect(db_folder / db_filename)
cursor = conn.cursor()

# Get affil from table affiliations that do not have lat and lon, that is: (0,0) 
cursor.execute("SELECT rowid, affiliation FROM affiliations WHERE latitude = ? and longitude = ?", (0,0))
counter = 1
rows = cursor.fetchall()
for i,current_row in enumerate(rows):
    print('\n\nIterating row nr:',counter)
    counter += 1
    #Get the lat lot via geocoding
    lat, lon, _ = txt2geo.get_lat_lon_from_text([current_row[1]],#second entry of tuple is the affiliation
                                                geophrase_delimeter = ',',
                                                clean_string = 'unicode',
                                                reverse = False,
                                                verbose = True
                                                )
    if isinstance(lat[0], float) and isinstance(lon[0], float):
        cursor.execute("""UPDATE affiliations SET latitude=? , longitude=? WHERE rowid = ?""", (lat[0], lon[0], current_row[0]))
        print('\nUpdated latitude: %.2f and longitude: %.2f for affiliation: %s' % (lat[0], lon[0], current_row[1]))
        print('\n')

# Commit updated rows and sign off
conn.commit()
cursor.close()
conn.close()

