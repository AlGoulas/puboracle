#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sqlite3

from puboracle.txtprocess import txt2geo

db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'unique_affiliations.db'
conn = sqlite3.connect(db_folder / db_filename)
cursor = conn.cursor()
cursor_updates = conn.cursor() 
nr_rows = 10
# Get affil from table affiliations that do not have lat and lon, that is: (0,0) 
cursor.execute("SELECT rowid, affiliation FROM affiliations WHERE latitude=? , longitude=?", (0,0)) 
counter = 1
while 1:
    rows = cursor.fetchmany(nr_rows)
    for i,current_row in enumerate(rows):
        print('\n\nIterating row nr:', counter)
        counter += 1
        #Get the lat lot via geocoding
        lat, lon, _ = txt2geo.get_lat_lon_from_text([current_row[1]],#second entry of tuple is the affiliation
                                                    geophrase_delimeter = ',',
                                                    clean_string = 'unicode',
                                                    reverse = False,
                                                    verbose = True
                                                    ) 
        if isinstance(lat[0], float) and isinstance(lon[0], float):
            cursor_updates.execute("""UPDATE affiliations SET latitude=? , longitude=? WHERE rowid = ?""", (lat[0], lon[0], current_row[0]))
            #conn.commit()#is it okay to perform this after each update?
            print('\nUpdated latitude: %.2f and longitude: %.2f for affiliation: %s' % (lat[0], lon[0], current_row[1]))
            print('\n')
    if not rows: break
# Commit updated rows and sign off
conn.commit()
cursor.close()
conn.close()

