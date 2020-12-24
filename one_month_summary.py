#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from pathlib import Path

from puboracle.writestoredata import getdata,readwritefun
from puboracle.txtprocess import txt2geo, txtfun
from puboracle.visualization import visfun
from puboracle.metrics import txtmetrics

# This project showcases how puboracle can be used to mine PubMed and extract 
# info on geospatial location of research activity, networks of collaborations
# and related matrics

# This example tracks publications with the key word "connectome" or 
# "connectomics" in the last 30 days

# Submit query and fetch data in an XML format
save_folder = '/Users/alexandrosgoulas/Data/work-stuff/projects/example_puboracle_connectomics/xmldata/'
query = 'connectomics OR connectome'
days = 30
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
                 'authors',
                 'journal',
                 'title',
                 'pubdate',
                 'abstract',
                 'pmid'
                ]

# Create SQL database if it does not exist
db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'ndays_pubmed.db'
conn = readwritefun.sql_create_db(db_folder,
                                  db_filename = db_filename
                                  )

# Create table publications if it does not exists
sql_table = """ CREATE TABLE IF NOT EXISTS publications (
                                   id integer PRIMARY KEY,
                                   first_author_first_name text,
                                   first_author_last_name text,
                                   pub_year text,
                                   authors text,
                                   journal text,
                                   title text,
                                   abstract text,
                                   affiliations text,
                                   pubmed_id integer
                               ); """

readwritefun.sql_create_table(conn, 
                              sql_table = sql_table
                              )

# Read one-by-one the xml files and insert rows in the database 
len_threshold = 12#len threshold for keeping an affiliation
delimeter = ';'#delimeter for seperating multiple affiliations and authors
start_sql_int = 0
stop_sql_int = 0
ids = None
for axf in all_xml_files:
    pub_data, _ = readwritefun.read_xml_to_dict(folder_to_xmls, 
                                                all_xml_files = [axf],
                                                keys_to_parse = keys_to_parse
                                                )
    
    # Extract journal, title pubdate and abstract
    journal = pub_data[keys_to_parse.index('journal')]
    title = pub_data[keys_to_parse.index('title')]
    pubdate = pub_data[keys_to_parse.index('pubdate')]
    abstract = pub_data[keys_to_parse.index('abstract')]
    pmid = pub_data[keys_to_parse.index('pmid')]
       
    # Unpack the authors list and dictionaries to get first, last name and 
    # affiliation
    authors_affiliations = pub_data[0]
    all_affiliations = []
    all_author_list = []
    all_first_author_first_name = []
    all_first_author_last_name = []  
    for aa in authors_affiliations:
        affil = [current_aa['affiliation'] for current_aa in aa]
        if any(a for a in affil):#if list contains any non-empty affiliations then join them 
            affil = delimeter.join(affil)
        else:
            affil = ''
        all_affiliations.append(affil)
        #Get first and last name
        first_name = [current_aa['forename'] for current_aa in aa]
        last_name = [current_aa['lastname'] for current_aa in aa]
        all_first_author_first_name.append(first_name[0])
        all_first_author_last_name.append(last_name[0]) 
        # Wrap every first and last name in a string seperating each author 
        # with delimeter  
        first_last_authorlist = [fl[0] + ',' + fl[1] for fl in zip(first_name,last_name)]
        first_last_authorlist = delimeter.join(first_last_authorlist)
        all_author_list.append(first_last_authorlist)
                            
    # Remove unwanted elements from affiliations:
    # i.  email address 
    # ii. author names or initials in parentheses (can also remove acronyms of location but this is OK)   
    # iii. the word "and" from the beginning of an affiliation 
    # iv. length of affiliation above len_threshold 
    all_affiliations_cleaned = txtfun.remove_email_txtinparen(all_affiliations,
                                                              delimeter = delimeter
                                                              ) 
    
    # Insert simultaneously the row corresponing to his xml file in the 
    # sql database
    # We create a tuple for each row  assembled in a list for simultaneous 
    # insertion
    if ids is None:
        start_sql_int = 0
        stop_sql_int = len(all_affiliations_cleaned)  
    ids = list(range(start_sql_int, stop_sql_int))#create unique integer primary ids 
    # TODO this looks redundant since it seems an automatic thign that sqlite 
    # should do - check what is the case
    all_rows = [ids,
                all_first_author_first_name,
                all_first_author_last_name,
                pubdate,
                all_author_list,
                journal,
                title,
                abstract,
                all_affiliations_cleaned,
                pmid
                ]
    
    start_sql_int = start_sql_int + len(all_first_author_first_name)
    stop_sql_int = stop_sql_int + len(all_first_author_first_name)
    
    all_rows = [ar for ar in zip(*all_rows)]
    sql_insert = 'INSERT INTO publications VALUES(?,?,?,?,?,?,?,?,?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = all_rows, 
                                          conn = conn
                                         )
    


