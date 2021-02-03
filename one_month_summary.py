#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from puboracle.writestoredata import getdata,readwritefun
from puboracle.txtprocess import txtfun 
from puboracle.aux import auxfun 

# This project showcases how puboracle can be used to mine PubMed and extract 
# info on geospatial location of research activity, networks of collaborations
# and related matrics

# This example tracks publications with the key word "connectome" or 
# "connectomics" in the last 30 days

# Submit query and fetch data in an XML format
save_folder = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/example_puboracle_connectomics/xmldata/'
query = 'connectomics OR connectome'
days = 100
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
                                    pubdate TEXT,
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

# Create table affiliation if it does not exist
sql_table = """ CREATE TABLE IF NOT EXISTS affiliation (
                                    affiliation_name TEXT NOT NULL PRIMARY KEY,
                                    country TEXT,
                                    latitude REAL,
                                    longitude REAL
                                ); """

readwritefun.sql_create_table(conn, 
                              sql_table = sql_table
                              )

# Create table author-publication if it does not exist
sql_table = """ CREATE TABLE IF NOT EXISTS author_publication (
                                  pmid INTEGER NOT NULL,
                                  first_name TEXT NOT NULL,
                                  last_name TEXT NOT NULL,
                                  FOREIGN KEY (pmid) REFERENCES publication (pmid),
                                  FOREIGN KEY (first_name) REFERENCES publication (first_name),
                                  FOREIGN KEY (last_name) REFERENCES publication (last_name),
                                  PRIMARY KEY (first_name, last_name, pmid)
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
    # NOTE certain dates may not have DD or MM so assign to such entries 
    # DD=00 or MM=0
    # TODO: check if this inconsistency of dates has to do with the info 
    # available in PubMed or with how we storre and read the XML files
    pubdate_processed = []
    for p in pubdate:
        p_split = p.split('-')
        if len(p_split) == 3:
            pubdate_processed.append('-'.join(p_split))
        elif len(p_split) == 2:
            pubdate_processed.append('-'.join(p_split) + '-00')
        elif len(p_split) == 1:
            pubdate_processed.append(p_split[0] + '-00-00')
        elif p_split[0]:
            pubdate_processed.append('0000-00-00')
            print('\nEmpty date')
    
    # Unpack the authors list and dictionaries to get first, last name and 
    # affiliation
    # authors_affiliations is a list of N=number of publications for the current xml file 
    authors_affiliations = pub_data[0]
    all_affil = []
    all_first_name = []
    all_last_name = []
    
    # List of rows for the junction tables
    author_publication_rows = []

    # For each publication, we have N authors and affiliations - unpack this info
    # in this loop
    for aa, current_pmid in zip(authors_affiliations, pmid):
        affil = [current_aa['affiliation'] for current_aa in aa]  
        #Get first and last name
        first_name = [current_aa['forename'] for current_aa in aa]
        last_name = [current_aa['lastname'] for current_aa in aa]
        all_first_name.append(first_name)
        all_last_name.append(last_name)
        # Perform some NLP in affil
        # Remove unwanted elements from affiliations:
        # i.  email address 
        # ii. author names or initials in parentheses (can also remove acronyms of location but this is OK)   
        # iii. the word "and" from the beginning of an affiliation 
        # iv. length of affiliation above len_threshold
        affil_cleaned = txtfun.remove_email_txtinparen(affil,
                                                       delimeter = ';'
                                                      ) 
        all_affil.extend(affil_cleaned)
        auth_pub_row = auxfun.pub_affil_author_junction(list_author_affil = aa,
                                                        pub_id = current_pmid
                                                        )
        author_publication_rows.extend(auth_pub_row)
         
    # Insert simultaneously the row corresponing to this xml file in the 
    # sql database
    # We create a tuple for each row  assembled in a list for simultaneous 
    # insertion
    
    # For table publication
    all_rows = [
                pmid,
                doi,
                pubdate_processed,
                journal_title,
                article_title,
                abstract
                ]
    
    all_rows = [ar for ar in zip(*all_rows)]
    sql_insert = 'INSERT OR IGNORE INTO publication VALUES(?,?,?,?,?,?);'
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
    
    # Prepare the rows - extract the country and constuct list with 
    # longitude and latitude info set as 0 (geocoding will be done seperately)
    # First we have to unpack the str in all_affil, since certain str may 
    # contain multiple affiliations (authors may have more than one affiliation)
    all_affil_unpacked = []
    for aa in all_affil:
        if ';' in aa:
            aa_split = aa.split(';')
            aa_split = [aas.rstrip().lstrip() for aas in aa_split] 
            all_affil_unpacked.extend(aa_split) 
        else:
            all_affil_unpacked.append(aa.rstrip().lstrip()) 
    # Assign country - this simple takes the last entry of the affiliation
    # when splitting the str all_affil[i]
    # TODO: Consider finding the country in a more robust way without the 
    # aforementioned assumption
    country = []
    for aa in all_affil_unpacked:
        country.append(txtfun.keep_only_unicode(aa.split(',')[-1]))    
    latitude = [0] * len(all_affil_unpacked)
    longitude = [0] * len(all_affil_unpacked)
    # Insert into table affiliations
    all_rows = [
               all_affil_unpacked,
               country,
               latitude,
               longitude
               ]
  
    all_rows = [ar for ar in zip(*all_rows)]
    sql_insert = 'INSERT OR IGNORE INTO affiliation VALUES(?,?,?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = all_rows, 
                                          conn = conn
                                          ) 
    
    # Junction tables
    # author_publication
    sql_insert = 'INSERT OR IGNORE INTO author_publication VALUES(?,?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = author_publication_rows, 
                                          conn = conn
                                          ) 


conn.close()

