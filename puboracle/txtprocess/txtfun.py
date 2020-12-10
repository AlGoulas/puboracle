#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re 

from ..metrics import txtmetrics

def remove_digits_from_str(s):
    '''
    Remove digits from str (pretty self-explanatory)
    
    Input
    -----
    s: str
    
    Output
    ------
    s_digit_removed: s after removing all digits
    
    Example
    -------
    s = 'Rice is 1 or 2 times better than no rice. Or maybe 56?'
    s_digit_removed = remove_digits_from_str(s)
    print(s_digit_removed)
    'Rice is  or  times better than no rice. Or maybe ?'
    '''
    s_digit_removed = ''.join([i for i in s if not i.isdigit()])
    return s_digit_removed

def convert_str_float_comma(list_str_comma):
    '''
    Convert a list of floats that have commas ',' instead of dots '.' to denote
    the integer and decimal parts
    
    Input
    -----
    list_str_comma: list, of str each str denoting a "comma float" (e.g. 3,32)
    
    Output
    ------
    list_floats: list of floats nrs, converted from their "comma float" format
        (e.g. 3.32)
    
    '''
    list_floats = [float(item.replace(',','.')) if isinstance(item, str) else item for item in list_str_comma] 
    
    return list_floats 

def list_unique_authors(list_all_authors):
    '''
    Find unique author names in a list of authors.
    
    Input
    -----
    list_all_authors: list of str with the author names of a publication. Each
        str potentially contains many colon-seperated author names
    
    Output
    ------
    unique_authors: list of str with the unique author names 
    '''
    unique_authors = []
    for author_list in list_all_authors:
        authors = author_list.split(';')
        for a in authors:
            if a not in unique_authors: unique_authors.extend(authors)
            
    return unique_authors         

def filter_txt(list_txt, 
               low_limit = None, 
               chars_or_words = 'chars',
               ):
    '''
    Given a list of str, keep only non-empty str and, apply
    a filtering based on the lowest acceptable number of chars or words.
    
    Input
    -----
    list_txt: list of str
    
    low_limit: int indicating the lowest acceptable nr of chars or words
    
    chars_or_words: str {'chars','words'}
    
    Output
    ------
    list_txt_filtered: list of str with all the str in list_txt that met the
        filterign criteria
        
    filter_idx: list of int, where each item is the index of a str such that
        list_txt_filtered[0] == list_txt[filter_idx[0]] 
    '''    
    filter_idx = []
    list_txt_filtered = []
    for idx, abstract in enumerate(list_txt):
        if low_limit is None:
            if abstract!='':
                filter_idx.append(idx)
                list_txt_filtered.append(abstract) 
        elif chars_or_words=='chars':
            nr_c = txtmetrics.count_chars_no_white(abstract, 
                                                [' '])
            if abstract!='' and nr_c > low_limit:
                filter_idx.append(idx)
                list_txt_filtered.append(abstract) 
        elif chars_or_words=='words': 
            nr_w = txtmetrics.count_words(abstract) 
            if abstract!='' and nr_w > low_limit:
                filter_idx.append(idx)
                list_txt_filtered.append(abstract) 
              
    return list_txt_filtered, filter_idx  

def remove_str_newline(txt):
    '''
    Remove words before newline character and newline characters as well
    
    Input
    -----
    txt: str to be processed
    
    Output
    ------
    txt: str the processed str
    
    '''
    pattern = r'\b(\w+)\n'
    to_remove = re.findall(pattern, txt)
    for rc in to_remove:
        txt = txt.replace(rc,'')
    txt = txt.replace('\n','')
    
    return txt

def remove_email_txtinparen(lst_str,
                            len_threshold = 15,
                            delimeter = ';'
                            ):
    '''
    Remove elements from list of strings:
    i.  email address 
    ii. text in parentheses
    iii. the word "and" from the beginning of a string 
    iv. strings with length of string below len_threshold  
    
    Input
    -----
    
    
    Output
    ------
    
    '''
    lst_str_cleaned = []
    for i,affil in enumerate(lst_str):
        all_current_cleaned = []
        affil_splitted = affil.split(delimeter)
        for a in affil_splitted:
            cleaned = re.sub("[\(\[].*?[\)\]]", "", a)#remove text in parentheses
            cleaned = re.sub("\S*@\S*\s?", "", cleaned).rstrip()#remove email address
            cleaned = cleaned.replace('electronic address:','')# remove 'electronic address:'
            cleaned = cleaned.replace('Electronic address:','')# remove 'Electronic address:'
            cleaned = re.sub("^\sand", "", cleaned)# remove 'and' from the beggining (preceeded by whitespace)
            if cleaned and len(cleaned) > len_threshold:   
                all_current_cleaned.append(cleaned.lstrip())#remove potential leading whitespace
        # If we have non-empty all_current_cleaned list then append it in
        # lst_str_cleaned with the joined with the delimeter  
        if all_current_cleaned:
            lst_str_cleaned.append(delimeter.join(all_current_cleaned))
        
    return lst_str_cleaned
        
def keep_only_alpha(string):
    '''
    Keep only alphabetical characters in string
    Processed string is also l+r stripped to remove whitespaces
    
    Input
    -----
    string: str, to be processed
    
    Output
    -----
    str, processed and stripped string
    '''
    return re.sub(r"[^a-zA-Z]+", ' ', string).rstrip().lstrip()

def keep_only_alphanum(string):
    '''
    Keep only alphanumerical characters in string
    Processed string is also l+r stripped to remove whitespaces
    
    Input
    -----
    string: str, to be processed
    
    Output
    -----
    str, processed and stripped string
    '''
    return  re.sub(r"[^a-zA-Z0-9]+", ' ', string).rstrip().lstrip()     
    