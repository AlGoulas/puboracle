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
                              pub_id = None
                              ):
    
    # Get affil - can be multiple affils: str seperated with ';'
    affil = [laa['affiliation'] for laa in list_author_affil]  
    affil = txtfun.remove_email_txtinparen(affil,
                                           delimeter = ';'
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
    
    all_rows = [ar for ar in zip(*all_rows)]
    
    return all_rows 
    