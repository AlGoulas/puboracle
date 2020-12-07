#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from pathlib import Path
import re

from puboracle.writestoredata import getdata,readwritefun
from puboracle.txtprocess import txt2geo, txtfun
from puboracle.visualization import visfun
from puboracle.metrics import txtmetrics
from puboracle.metrics import netmetrics

# This project showcases how puboracle can be used to mine PubMed and extract 
# info on geospatial location of research activity, networks of collaborations
# and related matrics

# This example tracks publications with the key word "connectome" in 2020

# Submit query and fetch data in an XML format
save_folder = '/Users/alexandrosgoulas/Data/example_puboracle_connectomics/xmldata/'
query = 'connectomics OR connectome'
days = 365
email = 'arimpos@gmail.com'

getdata.fetch_write_data(
                        query = query,
                        datetype = 'pdat',
                        email = email,
                        days = days,
                        save_folder = save_folder
                        )

# Read all the XML files that were downloaded
folder_to_xmls = Path('/Users/alexandrosgoulas/Data/work-stuff/projects/example_puboracle_connectomics/xmldata/')
all_xml_files = readwritefun.get_files_in_folder(folder_to_xmls, 
                                                order = True
                                                )

# Read the XML files and extract the desired info specified by the list 
# keys_to_parse 
keys_to_parse = [
                 'affiliations'
                ]

pub_data, xml_filenames = readwritefun.read_xml_to_dict(folder_to_xmls, 
                                                        all_xml_files = all_xml_files,
                                                        keys_to_parse = keys_to_parse
                                                        )

# Extract affiliations
affiliations = pub_data[keys_to_parse.index('affiliations')]
                                 
# Remove unwanted elements from affiliations:
# i.  email address 
# ii. author names or initials in parentheses (can also remove acronyms of location but this is OK)   
# iii. the word "and" from the beginning of an affiliation 
# iv. length of affiliation above len_threshold 
# affiliations_cleaned = []
# indexes_empty = []
# len_threshold = 15
# for i,affil in enumerate(affiliations):
#     cleaned = re.sub("[\(\[].*?[\)\]]", "", affil)#remove text in parentheses
#     cleaned = re.sub("\S*@\S*\s?", "", cleaned).rstrip()#remove email address
#     cleaned = cleaned.replace('electronic address:','')# remove 'electronic address:'
#     cleaned = cleaned.replace('Electronic address:','')# remove 'Electronic address:'
#     cleaned = re.sub("^\sand", "", cleaned)# remove 'and' from the beggining (preceeded by whitespace)
#     if not cleaned or len(cleaned) <= len_threshold:
#         indexes_empty.append(i)
#     else:    
#         affiliations_cleaned.append(cleaned.lstrip())#remove potential leading whitespace
#%%
affiliations_cleaned = txtfun.remove_email_txtinparen(affiliations,
                                                      len_threshold = 12,
                                                      delimeter = ';'
                                                     ) 
#%%   
# Get all the unique cleaned affiliations     
(all_affiliations_cleaned, 
 unique_affiliations_cleaned, 
 occurences) = txtmetrics.get_unique_strs(affiliations_cleaned,
                                          exclude=['', ' ']
                                          )
 
# Remove potential leading whitespace in the unique_affiliations_cleaned str
unique_affiliations_cleaned = [uac.lstrip() for uac in unique_affiliations_cleaned if len(uac) > len_threshold] 
                                          
# Extract lat lot
lat,lon,txtforloc = txt2geo.get_lat_lon_from_text_wordwise(
                                                           unique_affiliations_cleaned,
                                                           verbose = True,
                                                           reverse = False,
                                                           rand_wait_time_sec = None
                                                           )

# Remove nan from lat lon and visualize the rest
lat = [item for item in lat if not math.isnan(item)]
lon = [item for item in lon if not math.isnan(item)]
visfun.vis_lon_lat(longitude=lon, latitude=lat)

# Visualize top 5 of affiliations with the max publications
# Do so after the merge of nr of publications between affiliations
# that exceed a string similarity threshold
(affiliations_nrpubs_topmerged, 
 _) = txtmetrics.add_by_similarity(occurences, 
                                   topN = 10, 
                                   look_ahead = 100,
                                   threshold = 0.8
                                  )
                                                     
visfun.visualize_counter_selection(affiliations_nrpubs_topmerged)
                                                     
# Construct the collaboration network based on affiliations.
all_edges = netmetrics.construct_edges_list(unique_items, 
                                 list_coitems=co_items,
                                 exclude=[]
                                 ) 
