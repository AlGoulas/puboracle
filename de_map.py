#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import geopandas as gpd
import matplotlib.pyplot as plt
import re

plt.style.use('seaborn')
file = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/DE_maps/plz-gebiete.shp/plz-gebiete.shp'
plz_shape_df = gpd.read_file(file, dtype={'plz': str})
# Plot map with all the centroids of the polygons
fig, ax = plt.subplots()
plz_shape_df.plot(ax=ax, color='orange', alpha=0.8)
# Read the polygons from the df
polygons = plz_shape_df['geometry']
lat_center = []
lon_center = []
for p in polygons:
    lat_lon_center = p.centroid.wkt
    llc_splited = lat_lon_center.split()
    lat_center.append(float(re.sub('[()]', '', llc_splited[1])))
    lon_center.append(float(re.sub('[()]', '', llc_splited[2])))
    # ax.text(
    #     x=top_cities[c][0], 
    #     # Add small shift to avoid overlap with point.
    #     y=top_cities[c][1] + 0.08, 
    #     s=c, 
    #     fontsize=12,
    #     ha='center', 
    # )
    # Plot city location centroid
    ax.plot(
        float(re.sub('[()]', '', llc_splited[1])), 
        float(re.sub('[()]', '', llc_splited[2])), 
        marker='o',
        c='black', 
        alpha=0.5,
        markersize=0.5
    )
    


    