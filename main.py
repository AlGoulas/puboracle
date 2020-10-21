#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#import numpy as np
import math
import numpy as np
from pathlib import Path

import auxfun
import readwritefun
import visfun

# Read XML files
folder_to_xmls = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/xmls/2010-2020/')
all_xml_files = readwritefun.get_files_in_folder(folder_to_xmls, 
                                                 order = True
                                                 )

# Swap the author Initials and ForeName in the xml files 
# We do this swap since the current xml parser fetched by default the 
# Initials - maybe a parameter can control this but for now just swap XML
# fields Initials and ForeName 
folder_to_xmls_swapped = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/xmls/2010-2020_swapped/')
for xml_file in all_xml_files:
    readwritefun.read_swap_write(folder_to_xmls / xml_file, 
                                  path_new_file = folder_to_xmls_swapped, 
                                  filename_new = xml_file,
                                  str_to_swap1 = 'ForeName',
                                  str_to_swap2 = 'Initials'
                                  )

# Extract info of interest: 
# abstract text, article title, journal title, affiliations   
# journal title will be used to match the database with the 
# journal impact info and thus extract impact metrics (metrics_from_csv)  
keys_to_parse = ['journal', 
                 'title', 
                 'abstract', 
                 'authors', 
                 'affiliations', 
                 'pubdate'
                 ]
pub_data, xml_filenames = auxfun.read_xml_to_dict(folder_to_xmls_swapped, 
                                                  all_xml_files = all_xml_files,
                                                  keys_to_parse = keys_to_parse
                                                  )

year = pub_data[5] 
years_of_interest = [
                      '2010',
                      '2011',
                      '2012',
                      '2013',
                      '2014',
                      '2015',
                      '2016',
                      '2017',
                      '2018',
                      '2019',
                      '2020'
                    ]

# years_of_interest = [
#                       '2010'
#                     ]

folder_save = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/results_de')

for current_year in years_of_interest:
    print('\nProcessing data for year...:', current_year)
    year_idx = []
    for counter,y in enumerate(year):
        if y == current_year:
            year_idx.append(counter)
    
    affiliations = pub_data[4]
    affiliations = [affiliations[idx] for idx in year_idx]
        
    # Get German affiliations
    # The affiliations for each study are contained in a ';' seperated string
    # Loop through each string
    de_affiliations = [] 
    for s in affiliations:
        s_splitted = s.split(';')
        current_affiliations_de = []
        current_affiliations_de = [affil for affil in s_splitted if 'Germany' in affil]
        if current_affiliations_de:
            # Here we have to include only the unique affiliations per publication.
            # Otherwise we bias the list with papers that just have many authors 
            # with the same affiliation. Thus get unique affiliations
            current_affiliations_de = list(set(current_affiliations_de))
            de_affiliations.extend(current_affiliations_de)
            
    # Remove affilaitions that contain more than one country
    de_affiliations, txt_not_allowed = auxfun.trace_countries_in_text(de_affiliations, 
                                                                      allowed_countries=['Germany']
                                                                      )
   
    # Remove 'Germany' from affiliations in order to get a latitude/longitude 
    # information with city as the most location abstract feature
    de_affiliations_trimcountry = []
    for s in de_affiliations: 
        s_splitted = s.split('Germany')[0]
        s_splitted = s_splitted.split(',')
        s_splitted = ', '.join(s_splitted[:-1])
        de_affiliations_trimcountry.append(s_splitted)        
     
    # Get unique and nr of pubs per unique affiliation in Germany
    # What we feed in this function basically determines the top10 and results
    all_affiliations_de, un_affiliations_de, occurences_de = auxfun.get_unique_strs(de_affiliations_trimcountry,
                                                                                    exclude = ['', ' ']
                                                                                    )     
    # Merge affiliations that have a high string similarity and their
    # corresponding nr of pubs
    (affiliations_nrpubs_top10_merged, 
     excluded_items_list) = auxfun.add_by_similarity(occurences_de, 
                                                     topN = 10, 
                                                     look_ahead = 300,
                                                     threshold = 0.8
                                                     )
    
    #affiliations_nrpubs_top10 = occurences_de.most_common()[:10]
    
    # Visualize top 10 as a bar plot
    visfun.visualize_counter_selection(affiliations_nrpubs_top10_merged,
                                       file_name = current_year + '_bar_top10',
                                       folder_save = folder_save
                                       )
    
    # Get nr of pubs and affiliations in seperate lists
    affiliations_top10 = []
    nr_pubs_top10 = []
    for affil in affiliations_nrpubs_top10_merged: 
        affiliations_top10.append(affil[0])
        nr_pubs_top10.append(affil[1])
    
    lat, lon, full_txt_location = auxfun.get_lat_lon_from_text_wordwise(affiliations_top10) 
                                                            
    # Remove nan
    lat = [item for item in lat if not math.isnan(item)]
    lon = [item for item in lon if not math.isnan(item)]
    
    # Visualize DE map
    lonlat = []
    for x,y in zip(lat,lon):
        lonlat.append((y,x))#reverse order of lat lon for the vis_lon_lat_de function  
    
    size = visfun.rescale_size(np.asarray(nr_pubs_top10), 35)
    file = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/DE_maps/plz-gebiete.shp/plz-gebiete.shp'
    title = 'Locations of top 10 universities and institutes (number of publications in ' + current_year + ')'
    visfun.vis_lon_lat_de(lonlat, 
                          size = size,
                          file_de_map = file,
                          title = title,
                          folder_save = folder_save
                          )

# TESTING
paper_title = pub_data[1]
paper_title = [paper_title[idx] for idx in year_idx]

journal = pub_data[0]
journal = [journal[idx] for idx in year_idx]

target_affil = affiliations_nrpubs_top10_merged[0][0]
target_affil + ', Germany'

paper_idx = []
for counter,affil in enumerate(affiliations):
    s = affil.split(';')
    for sub in s:
        sim = auxfun.string_similarity(
                                       [sub],
                                       source_str = target_affil,
                                       similarity = 'jaccard'
                                      )
        sim = 1-sim
        if sim > 0.7: 
            paper_idx.append(counter)
            break#if citation found exit loop - one match is all we want


# Get address, nr, postcode
# latlon = []
# for x,y in zip(lat,lon):
#     latlon.append(str(x) + ',' + str(y)) 
 
# address, nr, postcode = auxfun.get_address_from_latlon(latlon)

# Build co-authorship graph
# coauth_adges = netfun.construct_edge_wei_list(un_strs, 
#                                               list_coauthorships = authors,
#                                               exclude = ['', ' ']
#                                               )


# googlescholar_results = auxfun.get_author_googlescholar(authors[0].split(';')[1] 
#                                                        )

# # Peek in the generator and see if it contains results to be iterated
# res = auxfun.peekin_generator(googlescholar_results)
# thres_affil_similarity = 0.6

# if res is None:
#     print('Empty results!')
# else:
#     first, results_sequence = res
#     for result in results_sequence:
#         (all_similarities, 
#          all_str, 
#          max_similarity, 
#          str_max_similarity) = auxfun.string_similarity(result.affiliation,
#                                                         string_list = affiliations[0]
#                                                         )
#         # If the affiliation returned from google scholar search for 
#         # the current result for the current author is higher than
#         # the chosen threshold, then grab info on the paper with 
#         # current_paper_title                                             
#         if max_similarity > thres_affil_similarity:
#             result_with_full_info = result.fill(['publications'])
#             (all_pubs,
#              all_cites) = auxfun.grab_publications_from_scolarlyauthor(result_with_full_info)
                                                                                
# # Check how many articles have an empty abstract
# nr_no_abstract = all_abstracts.count('') 

# # Find the unique number of journal titles
# nr_unique_journals = len(set(all_journal_titles))

# # Convert to lower case to avoid mismatches based on case
# all_journal_titles = [i.lower() for i in all_journal_titles]

# # Clean the journal title by removing info at the end of the title
# all_journal_titles_cln = []
# for journal in all_journal_titles:
#     all_journal_titles_cln.append(aux_fun.trim_txt(
#                                   journal, 
#                                   chars_for_trim=[':', '(', '.', ';'] 
#                                   ).strip()#remove trailing and leading whitespaces
#                                  )
    
# # Use the journal title to extract impact measures
# path_to_csv = '/Users/alexandrosgoulas/Data/work-stuff/python-code/development/manuscript_oracle/journal_metrics_info/scimagojr_2019.csv'
# (journal_metrics, 
#  SJR,  
#  matched_journal_titles,
#  matched_idx) = metrics_from_csv(all_journal_titles_cln, 
#                                  path_to_csv = path_to_csv
#                                  )
                                            
# nr_unique_matched_journals = len(set(matched_journal_titles))

# # Convert str to float (by replacing the comma)
# SJR_float = aux_fun.convert_str_float_comma(SJR) 

# # Get the abstracts and author lists that correspond to matched journals 
# # to the metrics database
# matched_abstracts_cln = []
# matched_abstracts = []
# matched_authors = []
# for idx in matched_idx:
#     matched_abstracts.append(all_abstracts[idx])
#     matched_abstracts_cln.append(aux_fun.remove_str_newline(all_abstracts[idx])
#                                     )
#     matched_authors.append(all_authors[idx])

# # Confine the variables based on abstracts that are non-empty and that 
# # correspond to a word or character limit
# list_variables = [SJR_float, matched_journal_titles, matched_authors] 
# (matched_abstracts_cln, 
#  filter_idx, 
#  variables_filtered)=aux_fun.filter_txt(matched_abstracts_cln, 
#                                         low_limit = 100, 
#                                         chars_or_words = 'words',
#                                         list_variables = list_variables
#                                         )
                                      
# matched_journal_titles_cln = variables_filtered[1]#get filtered matched_journal_titles  
                                       
# # Extract the nr of chars and words of the abstracts
# nr_chars_abs, nr_words_abs = aux_fun.get_chars_words(matched_abstracts_cln, 
#                                                      chrs_to_remove=[' ']
#                                                      )

# # Get nr of noun phrases, verbs and entitites of the abstracts
# (nr_noun_phrases_abs, 
#  nr_verbs_abs, 
#  nr_entities_abs)=aux_fun.get_nounphrases_verbs(matched_abstracts_cln) 

# # Perform a  term frequency–inverse document frequency similarity analysis of 
# # the abstracts content 
# tfidf, pairwise_similarity = aux_fun.tf_idf_similarity(matched_abstracts_cln) 
# pair_sim = pairwise_similarity.todense()
# avg_sim = np.mean(pair_sim, axis=1)
# avg_sim_abs = np.squeeze(np.asarray(avg_sim))
                                              
# # Extract the nr of chars and words of the titles
# nr_chars_tls, nr_words_tls = aux_fun.get_chars_words(matched_journal_titles_cln, 
#                                                      chrs_to_remove=[' ']
#                                                      )

# # Get nr of noun phrases, verbs and entitites of the titles
# (nr_noun_phrases_tls, 
#  nr_verbs_tls, 
#  nr_entities_tls)=aux_fun.get_nounphrases_verbs(matched_journal_titles_cln)

# # Perform a  term frequency–inverse document frequency similarity analysis of 
# # the abstracts content 
# tfidf, pairwise_similarity = aux_fun.tf_idf_similarity(matched_journal_titles_cln) 
# pair_sim = pairwise_similarity.todense()
# avg_sim = np.mean(pair_sim, axis=1)
# avg_sim_tls = np.squeeze(np.asarray(avg_sim))

# # Use random forests to predict SJR
# param_grid = {
#                   'n_estimators': [10, 40, 120, 160, 200],
#                   'max_depth': [None, 2, 4, 6, 8]
#               }

# Y = np.asarray(variables_filtered[0])#get filtered SJR 
# idx_not_nan = ~np.isnan(Y)
# Y = Y[idx_not_nan]

# X = np.vstack((
#                 np.asarray(nr_chars_abs)[idx_not_nan],
#                 np.asarray(nr_chars_tls)[idx_not_nan]
#                 )
#               )
# X = X.T

# x_tick_labels = [
#                   'nr_chars_abs', 'nr_chars_tls'
#                  ]

# import pred_models
# pred_models.cv_rf(X, Y, 
#                   param_grid=param_grid, 
#                   cv_folds=5, 
#                   x_tick_labels=x_tick_labels
#                   )

