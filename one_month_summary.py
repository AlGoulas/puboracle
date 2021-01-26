#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from puboracle.writestoredata import getdata,readwritefun

# This project showcases how puboracle can be used to mine PubMed and extract 
# info on geospatial location of research activity, networks of collaborations
# and related matrics

# This example tracks publications with the key word "connectome" or 
# "connectomics" in the last 30 days

# Submit query and fetch data in an XML format
save_folder = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/example_puboracle_connectomics/xmldata/'
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
folder_to_xmls = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/example_puboracle_connectomics/xmldata/')
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
                 'pmid',
                 'doi'
                ]

# Create SQL database if it does not exist
db_folder = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/sqlite_tryout')
db_filename = 'pubmed_design1.db'
conn = readwritefun.sql_create_conn_db(db_folder,
                                       db_filename = db_filename
                                      )

# Create table publication if it does not exists
sql_table = """ CREATE TABLE IF NOT EXISTS publication (
                                    pmid INTEGER NOT NULL PRIMARY KEY,
                                    doi TEXT,
                                    pubdate_year TEXT,
                                    pubdate_month TEXT,
                                    pubdate_day TEXT,
                                    journal_title TEXT,
                                    article_title TEXT,
                                    abstract TEXT
                                ); """

readwritefun.sql_create_table(conn, 
                              sql_table = sql_table
                              )

# Create table author if it does not exists
sql_table = """ CREATE TABLE IF NOT EXISTS author (
                                    first_name TEXT NOT NULL,
                                    last_name TEXT NOT NULL,
                                    PRIMARY KEY (first_name, last_name)
                                ); """

readwritefun.sql_create_table(conn, 
                              sql_table = sql_table
                              )

# Read one-by-one the xml files and insert rows in the database 
for axf in all_xml_files:
    pub_data, _ = readwritefun.read_xml_to_dict(folder_to_xmls, 
                                                all_xml_files = [axf],
                                                keys_to_parse = keys_to_parse
                                                )
    
    # Extract desired data from the publication
    journal_title = pub_data[keys_to_parse.index('journal')]
    article_title = pub_data[keys_to_parse.index('title')]
    pubdate = pub_data[keys_to_parse.index('pubdate')]
    abstract = pub_data[keys_to_parse.index('abstract')]
    pmid = pub_data[keys_to_parse.index('pmid')]
    doi = pub_data[keys_to_parse.index('doi')]
    
    # Unpack the list pubdate in year month day
    # Each entry pubdate[i] is a str in the format YYYY-MM-DD
    # NOTE certain dates may not have DD so assgin to this entry DD=00
    # TODO: check if this inconsistency of dates has to do with the info 
    # available in PubMed or with how we storre and read the XML files
    pubdate_year = []
    pubdate_month = []
    pubdate_day = []
    for p in pubdate:
        p_split = p.split('-')
        if len(p_split) == 3:
            pubdate_year.append(p_split[0])
            pubdate_month.append(p_split[1])
            pubdate_day.append(p_split[2])
        elif len(p_split) == 2:
            pubdate_year.append(p_split[0])
            pubdate_month.append(p_split[1])
            pubdate_day.append('00')
        elif len(p_split) == 1:
            pubdate_year.append(p_split[0])
            pubdate_month.append('00')
            pubdate_day.append('00')
        elif p_split[0]:
            pubdate_year.append('0000')
            pubdate_month.append('00')
            pubdate_day.append('00')
            print('\nEmpty date')
    
    # Unpack the authors list and dictionaries to get first, last name and 
    # affiliation
    # authors_affiliations is a list of N=number of publications for the current xml file 
    authors_affiliations = pub_data[0]
    all_affil = []
    all_first_name = []
    all_last_name = []
    # For each publication, we have N authors and affiliations - unpack this info
    # in this loop
    for aa, current_pmid in zip(authors_affiliations, pmid):
        affil = [current_aa['affiliation'] for current_aa in aa]  
        #Get first and last name
        first_name = [current_aa['forename'] for current_aa in aa]
        last_name = [current_aa['lastname'] for current_aa in aa]
        all_first_name.append(first_name)
        all_last_name.append(last_name) 
   
    # Remove unwanted elements from affiliations:
    # i.  email address 
    # ii. author names or initials in parentheses (can also remove acronyms of location but this is OK)   
    # iii. the word "and" from the beginning of an affiliation 
    # iv. length of affiliation above len_threshold 
    # all_affiliations_cleaned = txtfun.remove_email_txtinparen(all_affiliations,
    #                                                           delimeter = delimeter
    #                                                           ) 
    
    # Insert simultaneously the row corresponing to this xml file in the 
    # sql database
    # We create a tuple for each row  assembled in a list for simultaneous 
    # insertion
    
    # For table publication
    all_rows = [
                pmid,
                doi,
                pubdate_year,
                pubdate_month,
                pubdate_day,
                journal_title,
                article_title,
                abstract
                ]
    
    all_rows = [ar for ar in zip(*all_rows)]
    sql_insert = 'INSERT OR IGNORE INTO publication VALUES(?,?,?,?,?,?,?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = all_rows, 
                                          conn = conn
                                          )
    
    # For table author
    # Prepare the rows for table author by assigning the N authors
    # to each publication based on the unique pmid
    all_pmid_for_rows = []
    all_first_name_for_rows = []
    all_last_name_for_rows = []
    for idx_p,p in enumerate(pmid):
        all_pmid_for_rows.extend([p] * len(all_first_name[idx_p]))
        all_first_name_for_rows.extend(all_first_name[idx_p])
        all_last_name_for_rows.extend(all_last_name[idx_p])
       
    all_rows = [
                all_first_name_for_rows,
                all_last_name_for_rows
               ]
    
    all_rows = [ar for ar in zip(*all_rows)]
    sql_insert = 'INSERT OR IGNORE INTO author VALUES(?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = all_rows, 
                                          conn = conn
                                          ) 
       
conn.close()

