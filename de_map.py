#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import geopandas as gpd
import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import re
import sqlite3

def get_closer_dist(points, point_to_assign):
    '''
    Given to ndarrays return the idx of the point in points
    that is the closest to the point_to_assign
    '''
    euc_dist = np.linalg.norm(points-point_to_assign, axis=1)
    min_euc_dist = np.min(euc_dist)
    idx = np.where(min_euc_dist == euc_dist)[0][0]
    return idx, min_euc_dist

def is_in_boundingbox(point, lat_limit, lon_limit):
    it_is = (lat_limit[0] <= point[0] <= lat_limit[1]) and ((lon_limit[0] <= point[1] <= lon_limit[1]))
    return it_is
     
plt.style.use('seaborn')
plt.rcParams['figure.figsize'] = [12, 12]
file = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/DE_maps/plz-gebiete.shp/plz-gebiete.shp'
plz_shape_df = gpd.read_file(file, dtype={'plz': str})
# Plot map with all the centroids of the polygons
fig, ax = plt.subplots()
#plz_shape_df.plot(ax=ax, color='orange', alpha=0.8)
# Read the polygons from the df
polygons = plz_shape_df['geometry']
lat_center = []
lon_center = []
for p in polygons:
    lat_lon_center = p.centroid.wkt#we can get the centroid with .centroid but it does not work with these polygon objects (?)
    llc_splited = lat_lon_center.split()#thus we get text and then convert the lat lon to float
    lat_center.append(float(re.sub('[()]', '', llc_splited[1])))
    lon_center.append(float(re.sub('[()]', '', llc_splited[2])))
lat_center = np.asarray(lat_center)
lon_center = np.asarray(lon_center)
lat_lon_centers = np.vstack((lat_center,lon_center))   
lat_lon_centers = lat_lon_centers.T 
# Lat Lon limit (bounding box) for DE
lat_limit = (47,56)
lon_limit = (6,16)     
# Compute values to be plotted
# Read the lat lon from the db. Select lat lon from DE based affiliations
db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'unique_affiliations_geocode_city.db'
conn_affil = sqlite3.connect(db_folder / db_filename)
cursor_affil = conn_affil.cursor()
db_filename = 'ndays_pubmed_noprimary.db'
conn_pub = sqlite3.connect(db_folder / db_filename)
cursor_pub = conn_pub.cursor()
nr_rows = 100 
# Get affil from table affiliations that do not have lat and lon, that is: (0,0) 
cursor_pub.execute("SELECT affiliations FROM publications") 
counter = 1
counter_de_plotted = 0
counter_de_not_plotted = 0
pubs_per_plz = [0] * len(plz_shape_df.index)
while 1:
    rows = cursor_pub.fetchmany(nr_rows)
    for i,current_row in enumerate(rows):
        print('\n\nIterating row nr:', counter)
        counter += 1
        if 'Germany' in current_row[0]:
            print(current_row)
            # Split the str to all affiliations for this pub
            all_affil = current_row[0].split(';')
            # Keep only the ones that are based in Germany
            affil_DE = [aa for aa in all_affil if 'Germany' in aa]
            affil_DE = list(set(affil_DE))
            # Get lat lon for each of these affiliations by quering the db
            for ade in affil_DE:
                cursor_affil.execute("SELECT latitude,longitude FROM affiliations WHERE affiliation = ?", (ade,)) 
                row = cursor_affil.fetchone()#One row returned since affil in db unique
                print('\nCurrent affiliation:', ade)
                print('\nCurrent lat: %.5f  lon: %.5f ' % (row[0], row[1]))
                if is_in_boundingbox((row[0], row[1]), lat_limit, lon_limit):
                    counter_de_plotted += 1
                    idx,dist = get_closer_dist(lat_lon_centers, np.asarray([[row[1], row[0]]]))
                    pubs_per_plz[idx] = pubs_per_plz[idx] + 1#assign the publication to plz with center closer to the lat lon of the current affil
                    print('\nidx:', idx)
                    print('\nmin dist:', dist)
                else:
                    counter_de_not_plotted += 1
                # ax.plot(
                #         row[1], 
                #         row[0], 
                #         marker='o',
                #         c='black', 
                #         alpha=0.5
                #        )
                                
    if not rows: break
cursor_pub.close()
conn_pub.close()
cursor_affil.close()
conn_affil.close()
plz_shape_df['values'] = pd.Series(np.asarray(pubs_per_plz), 
                                    index = plz_shape_df.index
                                    )
import copy
cmap = copy.copy(plt.cm.get_cmap('cool'))
cmap.set_under(color='grey')    
plz_shape_df.plot(
                    ax = ax, 
                    column = 'values', 
                    categorical = False, 
                    legend = True, 
                    cmap = cmap,
                    alpha = 0.8,
                    vmin = 0.5
                  ) 
ax.set(
        title='Publications in Germany', 
        aspect=1.3,
        facecolor='white'
      )

    