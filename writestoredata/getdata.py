#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import time

from Bio import Entrez

def submit_query(query, 
                 days = 10,
                 datetype = None,
                 mindate = None,
                 maxdate = None,
                 email = None, 
                 retstart = 0, 
                 retmax = 10000, 
                 rand_wait_time_sec = 5
                 ):
    '''
    Fetch from PubMed info on published articles based on a query of terms
    and possible date constraints. Info is returned in xml format
    
    Input
    -----
    query: str, must contain the terms to be searched
        e.g. 'macromolecule OR receptor'
             'neural AND connectome'
             
    days: int, default 10, leading to results that are published 
        in the past N days
        
    datetype: str, {'pdat', 'mdat', 'edat'} denoting publication, modification,
        and Entrez date
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
    
    mindate: str with the form 'YYY/MM/DD', 'YYYY' or 'YYYY/MM' that specifies
        the earliest date from which results should be obtained
        
    maxdate: str with the form 'YYY/MM/DD', 'YYYY' or 'YYYY/MM' that specifies
        the latest date from which results should be obtained  
        
    email: str, email so that a notification can be sent if excessive queries 
        are sent 
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
        
    retstart: int, default 0, sequential index of the first UID in the 
        retrieved set to be shown in the XML output 
        (default=0, corresponding to the first record of the entire set). 
        This parameter can be used in conjunction with retmax to download an 
        arbitrary subset of UIDs retrieved from a search  
    
    retmax: int, default 10000, total number of UIDs from the retrieved set to 
        be shown in the XML output. 
        Increasing retmax allows more of the retrieved UIDs to be included in the 
        XML output, up to a maximum of 100,000 records
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
        
    rand_wait_time_sec: int, positive int specifying the upper bound of 
        random seconds to wait after submitting each query
   
    Output
    ------
    search_results: Bio.Entrez.Parser.DictionaryElement object
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
    
    '''
    print('\nSubmitting query...')
    time.sleep(np.random.randint(rand_wait_time_sec))
    Entrez.email = email
    search_handle = Entrez.esearch(db = 'pubmed', 
                                   reldate = days,
                                   datetype = datetype,
                                   mindate = mindate,
                                   maxdate = maxdate,
                                   term = query,  
                                   usehistory = 'y',
                                   retstart = retstart,
                                   retmax = retmax
                                   )
    
    search_results = Entrez.read(search_handle)
    search_handle.close()
    
    return search_results

def fetch_by_query(WebEnv = None, 
                   QueryKey = None, 
                   retstart = 0, 
                   retmax = 10000,
                   max_attempts = 5,
                   rand_wait_time_sec = 5
                   ):
    '''
    Input
    -----
    WebEnv: Bio.Entrez.Parser.StringElement (returned from submit_query())
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
        
    QueryKey: Bio.Entrez.Parser.StringElement (returned from submit_query()) 
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/)
                   
    retstart: int, default 0, sequential index of the first UID in the 
        retrieved set to be shown in the XML output 
        (default=0, corresponding to the first record of the entire set). 
        This parameter can be used in conjunction with retmax to download an 
        arbitrary subset of UIDs retrieved from a search  
    
    retmax: int, default 10000, total number of UIDs from the retrieved set to 
        be shown in the XML output. 
        Increasing retmax allows more of the retrieved UIDs to be included in the 
        XML output, up to a maximum of 100,000 records
        (see https://www.ncbi.nlm.nih.gov/books/NBK25499/) 
        
    max_attempts: int, default 5, specifyung the max nr of times to attempt
        to get the data correspondign to a query
        
        Useful since the server may be busy at a given time, and thus
        we avoid an error
    
    rand_wait_time_sec: int, positive int specifying the upper bound of 
        random seconds to wait after getting each chunk of data for each query     
    
    '''
    
    print('\nGetting data...')
    attempt = 1
    retry = True
    data = None
    while retry:
        time.sleep(np.random.randint(rand_wait_time_sec))
        try:
            fetchHandle = Entrez.efetch(db = 'pubmed', 
                                        retmode = 'xml', 
                                        webenv = WebEnv, 
                                        query_key = QueryKey,
                                        retstart = retstart,
                                        retmax = retmax
                                        )     
            data = fetchHandle.read()  
            fetchHandle.close() 
            retry = False
        except:
            # Stop if max_attempts are reached
            if attempt == max_attempts: 
                retry = False
            else:
                print('\nCould not get data after attempt nr...', attempt)
                print('\nRetrying...')
                retry = True
    
            attempt += 1
   
    return data

def fetch_write_data(query = None,
                     datetype = 'pdat',
                     mindate = None,
                     maxdate = None,
                     email = None,
                     days = None,
                     max_batch = None,
                     retmax = 1000,
                     save_folder = None 
                     ):
    '''
    Wrapper function for fetching and storing xml files based on queries to the
    PubMed database
    
    Uses submit_query() and fetch_by_query()
    
    Input
    -----
    save_folder: str containing the path to the folder where the .xml files
        will be stored
    
    For the rest of the parameters, see the doscstring of
    submit_query() and fetch_by_query()
    '''
    rs = 0#counter to start fetching records - will be updated by retmax at every batch 
    batch = 0
    
    # If min or max date is used, then set days to None
    if mindate is not None or maxdate is not None: days = None
    
    # TODO find a rigid valid stoping criterion (this hangs-up after 
    # max_attempts when no more results to fetch exist) 
    while True:
        if max_batch is not None:
            if batch >= max_batch: break
        print('\nBatch nr...:', batch)
        # Submit the query for each incremental retstart and retmax values
        search_results = submit_query(query, 
                                      days = days,
                                      datetype = 'pdat',
                                      mindate = mindate,
                                      maxdate = maxdate,
                                      email = email,
                                      retstart = rs, 
                                      retmax = retmax
                                      )
        # Get data for each incremental retstart and retmax values    
        data = fetch_by_query(WebEnv = search_results['WebEnv'],  
                              QueryKey = search_results['QueryKey'], 
                              retstart = rs, 
                              retmax = retmax,
                              max_attempts = 10
                              ) 
        rs += retmax#increase retstart value so we get the next chunk of data
        if data is None: break#if empty results, exit
        # Save data as xml    
        if data is not None: 
            f=open(save_folder + 'xml_' + str(batch) + '.xml' ,'wb')
            f.write(data)
            f.close()
            
        batch += 1
    
if __name__ == '__main__': 
    query = 'neuroscience OR brain'
    mindate = '2019' 
    maxdate = '2020'
    email = 'a.goulas@uke.de' 
    save_folder = '/Users/alexandrosgoulas/Data/work-stuff/python-code/projects/text_oracle/xmls/2019-2020/'
    
    fetch_write_data(query = query,
                     datetype = 'pdat',
                     mindate = mindate,
                     maxdate = maxdate,
                     email = email,
                     days = None,
                     max_batch = None,
                     retmax = 1000,
                     save_folder = save_folder 
                     )
    