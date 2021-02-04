#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import itertools

from puboracle.txtprocess import txtfun
    
def peekin_generator(iterable):
    '''
    Check if a geenrator is empty
    
    Input
    -----
    iterable: a generator
    
    Output
    ------
    None if generator is empty, else the first element of the generator
        in addition to the "resetted" generator itself ready to be iterated 
        again 
    
    '''
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first, itertools.chain([first], iterable)    

def pub_affil_author_junction(list_author_affil = None,
                              pub_id = None,
                              clean_fun = None,
                              delimeter_affil = ';'
                              ):
    
    # Get affil - can be multiple affils: str seperated with ';'
    affil = [laa['affiliation'] for laa in list_author_affil]  
    if clean_fun is not None:
        affil = clean_fun(affil,
                          delimeter = delimeter_affil
                         ) 
    #Get first and last name
    first_name = [laa['forename'] for laa in list_author_affil]
    last_name = [laa['lastname'] for laa in list_author_affil]
    
    # Make the rows for the junction tables
    # author_publication
    pub_id_junction = [pub_id] * len(first_name)
    all_rows = [
                pub_id_junction,
                first_name,
                last_name
                ]
    
    all_rows_auth_pub = [ar for ar in zip(*all_rows)]
    
    # author_affil
    all_affil = []
    all_first_name = []
    all_last_name = []
    for a,fn,ln in zip(affil, first_name, last_name):
        if delimeter_affil in a:
            a_splited = a.split(delimeter_affil)
            all_affil.extend(a_splited)
            all_first_name.extend([fn] * len(a_splited))
            all_last_name.extend([ln] * len(a_splited))
        else:
            all_affil.append(a)
            all_first_name.append(fn)
            all_last_name.append(ln)

    all_rows = [
               all_first_name,
               all_last_name,
               all_affil
              ]
    
    all_rows_auth_affil = [ar for ar in zip(*all_rows)]
    
    # pub_affil
    pub_id_junction = [pub_id] * len(all_affil)
    all_rows = [
                pub_id_junction,
                all_affil
                ]
    
    all_rows_pub_affil = [ar for ar in zip(*all_rows)]    

    return all_rows_auth_pub, all_rows_auth_affil, all_rows_pub_affil
    