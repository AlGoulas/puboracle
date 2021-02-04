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
save_folder = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/example_puboracle_brain_neuroscience/xmldata/'
query = 'brain or neuroscience'
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
folder_to_xmls = Path('/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/example_puboracle_brain_neuroscience/xmldata/')
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

# Create table author-affiliation if it does not exist
sql_table = """ CREATE TABLE IF NOT EXISTS author_affiliation (
                                  first_name TEXT NOT NULL,
                                  last_name TEXT NOT NULL,
                                  affiliation_name TEXT NOT NULL,
                                  FOREIGN KEY (first_name) REFERENCES publication (first_name),
                                  FOREIGN KEY (last_name) REFERENCES publication (last_name),
                                  FOREIGN KEY (affiliation_name) REFERENCES affiliation (affiliation_name),
                                  PRIMARY KEY (first_name, last_name, affiliation_name)
                                ); """

readwritefun.sql_create_table(conn, 
                              sql_table = sql_table
                              )

# Create table publication-affiliation if it does not exist
sql_table = """ CREATE TABLE IF NOT EXISTS publication_affiliation (
                                  pmid INTEGER NOT NULL,
                                  affiliation_name TEXT NOT NULL,
                                  FOREIGN KEY (pmid) REFERENCES publication (pmid),
                                  FOREIGN KEY (affiliation_name) REFERENCES affiliation (affiliation_name),
                                  PRIMARY KEY (pmid, affiliation_name)
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
    
    # List of rows for the junction tables
    author_publication_rows = []
    author_affiliation_rows = []
    publication_affiliation_rows = []
    
    # For each publication, we have N authors and affiliations - unpack this info
    # in this loop
    for aa, current_pmid in zip(authors_affiliations, pmid):
        # author_publication, author_affiliation, publication_affiliation
        (auth_pub_row, 
         auth_affil_row,
         pub_affil_row) = auxfun.pub_affil_author_junction(list_author_affil = aa,
                                                           pub_id = current_pmid,
                                                           clean_fun = txtfun.remove_email_txtinparen
                                                           )
        author_publication_rows.extend(auth_pub_row)
        author_affiliation_rows.extend(auth_affil_row)
        publication_affiliation_rows.extend(pub_affil_row)
         
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
    # Grab the first and last name from the junction rows above
    # This contains double entries potentially since the junction tables
    # represent N to M relations, but this is OK since the first and last 
    # name is the primary key for Table author so no duplicates will be entered
    all_rows = [(aar[0], aar[1]) for aar in author_affiliation_rows]
    sql_insert = 'INSERT OR IGNORE INTO author VALUES(?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = all_rows, 
                                          conn = conn
                                          ) 

    # Grab the affiliation_name from the junction rows above
    # This contains double entries potentially since the junction tables
    # represent N to M relations, but this is OK since the affiliation_name
    # is the primary key for Table affiliation so no duplicates will be entered

    # Assign country - this simple takes the last entry of the affiliation
    # when splitting the str all_affil[i]
    # TODO: Consider finding the country in a more robust way without the 
    # aforementioned assumption  
    country = [txtfun.keep_only_unicode(aar[2].split(',')[-1]) for aar in author_affiliation_rows]   
    all_affil = [aar[2] for aar in author_affiliation_rows]
    latitude = [0] * len(all_affil)
    longitude = [0] * len(all_affil)
    # Insert into table affiliations
    all_rows = [
               all_affil,
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
    
    # author_affiliation
    sql_insert = 'INSERT OR IGNORE INTO author_affiliation VALUES(?,?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = author_affiliation_rows, 
                                          conn = conn
                                          ) 
    
    # publication_affiliation
    sql_insert = 'INSERT OR IGNORE INTO publication_affiliation VALUES(?,?);'
    readwritefun.sql_insert_many_to_table(sql_insert, 
                                          rows = publication_affiliation_rows, 
                                          conn = conn
                                          ) 

# Test queries - exemplars
#sql_query = "SELECT publication.article_title FROM publication INNER JOIN author_publication ON publication.pmid = author_publication.pmid WHERE author_publication.first_name = ? AND author_publication.last_name = ?"

conn.close()

