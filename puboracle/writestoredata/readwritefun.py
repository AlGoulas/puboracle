#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import listdir
from os.path import isfile, join
import re
import sqlite3
from sqlite3 import Error

import pubmed_parser as pp

def get_files_in_folder(folder_path, order=False):
    '''
    Read all the file names that are contained within folder_path
    
    Input
    -----
    folder_path: pathlib.PosixPath object containing the folder path 
    
    order: bool, default False, denoting if the file names should be 
        reoardered based on one digit that they filenames may contain,
        thus the order will be ..1.ext , ...2.ext etc where ext the file 
        extension
        
    Output
    ------
    filenames: list of str, with the file names in folder_path 
        (including the extension)  
    
    '''
    filenames = [f for f in listdir(folder_path) if isfile(join(folder_path, f)) and f.endswith('.xml')]
    # Order filenames by assuming only one digit in their filename. 
    # This digit will define the ordering. 
    if order is True:
        filenames.sort(key=lambda f: int(re.sub('\D', '', f)))
    
    return filenames  

    
def read_xml_to_dict(folder_to_xmls, 
                     all_xml_files = None,
                     keys_to_parse = None
                     ):
    '''
    Read xml data in dict and store the desired dict values corresponding to
    the values specified in the list keys_to_parse
    
    Input
    -----
    folder_to_xmls: pathlib.PosixPath object denoting the path to the folder 
        containing all the .xml files to be read
        
    all_xml_files: list of str, denoting the file names to be read in the 
        folder_to_xmls. Can be obtained from get_files_in_folder() 
        
    keys_to_parse: list of str, denoting the keys of the dictionary holding 
        all the xml data from each file. The dictionary is created from
        parse_medline_xml() part of the pubmed_parser package 
    
    Output
    ------
    all_values: list of len(keys_to_parse) of lists L
        all_values[i] contains a list L with all the values corresponding to
        key=keys_to_parse[i]. 
        len(L) depends on the data contained in the .xml 
        files that will be read.
    '''
    xml_file = [] #keep here the xml file name from which the data are read
    
    # Initialize a list with N empty lists with N=len(keys_to_parse) 
    # This is where we store all the valeus from the keys_to_parse keys 
    # for a every dict
    all_values = [[]] * len(keys_to_parse)
    for current_xml in all_xml_files:
        print('\nIterating file...:', current_xml)
        # Normaly parse_medline_xml() should work (since we get data from pubmed), 
        # but this does not appear to be the case. 
        # Instead parse_medline_xml() gets the desired info from the xml files. 
        # To be further checked.  
        dicts_out = pp.parse_medline_xml(
                                        str(folder_to_xmls/current_xml),
                                        year_info_only = False,
                                        author_list = True#this returns an author list with the names AND the affiliation!
                                        )
        for d in dicts_out:
            for i, key in enumerate(keys_to_parse):
                try:
                    if all_values[i]:
                        all_values[i].append(d[key])
                    else:
                        # Store the value of key in a list so it can be further 
                        # appended in the loop
                        all_values[i] = [d[key]]
                    xml_file.append(current_xml)# keep xml file name
                except:
                    print('\nKey ', key, ' not found!')
                      
    return all_values, xml_file  

def sql_create_conn_db(db_folder, db_filename = None):
    '''
    Create a database connection to a SQLite database 
    
    Input
    -----
    db_folder: pathlib.PosixPath object containing the folder path 
    db_filename: str, denoting the name of the database 
    
    Output
    ------
    conn: Connection object
    '''
    conn = None
    try:
        conn = sqlite3.connect(db_folder / db_filename)
        return conn
    except Error as e:
        print(e)
            
def sql_create_table(conn, sql_table = None):
    '''
    Create a table from the create_table_sql statement
    
    conn: Connection object
    create_table_sql: a CREATE TABLE statement
    '''
    try:
        c = conn.cursor()
        c.execute(sql_table)
        c.close()
    except Error as e:
        print(e)

def sql_insert_many_to_table(sql_insert, 
                             rows = None, 
                             conn = None,
                             verbose = True
                             ):
    try:
        c = conn.cursor()
        c.executemany(sql_insert, rows)
        conn.commit()
        if verbose is True:
            print('\nWe have inserted', c.rowcount, ' rows')
        c.close()    
    except Error as e:
        print(e)
            
                