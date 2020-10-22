#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import Counter
import numpy as np
import re

from difflib import SequenceMatcher
import en_core_web_lg
from similarity.jaccard import Jaccard
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

def is_in_topbottomN(counter, 
                     N=10, 
                     top=True, 
                     author_list=None,
                     delimeter=';',
                     remove_entries = []
                     ):
    '''
    Mark a list of str based on if it contains the most or least frequent 
    str with occurences as described from the counter collections.Counter obj
    
    Input
    -----
    counter: collections.Counter obj with all the counts of interest
    
    N: int, default 10, specifying the top (or bottom) N frequent items in 
        counter 
    
    top: bool, default True, specyfying if the top (=True) or bottom(=False)
        N items in counter will be considered 
        
    author_list: list of str - can be seperated strings with the delimeter as a
        character. len(author_list)=N
        The un_strs and all_strs lists will be populated based on the 
        delimeter-based splits of each str in the list_txt
        
    delimeter: str, default ';', specifying the delimeter chracter of each str
        in list author_list 
        
    Output
    ------
    in_list: list of bool, of len N with each entry i specifying the str in
       author_list[i] are contained in the top or bottom N
       
    selected_authors: dict with the e top or bottom N in counter
        keys: str
        values: int
    '''
    
    # Remove entries from the counter, based on the remove_entries list
    if remove_entries: 
        for word in remove_entries:
            if word in counter:
                del counter[word]
    
    if top is True:
        selection=dict(counter.most_common()[:N])
    else:
        selection=dict(counter.most_common()[:-N-1:-1])
    selected_authors = list(selection.keys())#this contains N top or bottom authors
    # Based on the top (or bottom) N items in dictionary selection, check if 
    # any of the keys of selection is in author_list
    in_list = []
    for authors in author_list:
        in_list.append(any(a in selected_authors for a in authors.split(delimeter)))
              
    return in_list, selected_authors 

def add_by_similarity(counter, 
                      topN = 10, 
                      look_ahead = 100,
                      threshold = None,
                      similarity = 'jaccard'
                      ):
    '''
    Given a collections.Counter object of keys str and values int, return
    the top N items by taking into account potential string similarities and
    if so, rearranging the items in the collections.Counter object such that
    string similartiies of keys above certain threshold are grouped together
    
    Input
    -----
    counter: collections.Counter object with keys, str, and values, int
    
    topN: int, default 10, specifying the top N items to be returned after
        the merging of the keys and respective values of counter the top N
        is specified by the values
    
    look_ahead: int, default 100, specifying how many items (keys, values) 
        from counter will be considered for computing string similarities 
        of the keys
        
        Since string similarity is an expensive operation, the 
        look_ahead serves as a way to speed-up the process by taking into
        account only the look_ahead items from counter, and not all
        items in counter 
        
        If computation is not an issue, then specify look_ahead=len(counter)
        
    threshold: float [0 1] specifying the string similarity threshold above
        which two strings are considered the same
        
        Note that this range represents low (0) to high (1) similarity and is
        useful with string similarity measures that are normalized in [0 1]
        
    similarity: string similarity {'jaccard', 'spacy', 'seq_matcher'}, 
        default 'jaccard', to be used when comparing two strings.
        (see function string_similarity)
        
        Note that these metrics are normalized in the [0 1] range (low:0 high:1)
        Roundoff errors due to e.g., vector operations can occur
        
    Output
    ------
    new_count_list: list of tuples (keys, values) of the top N items in counter,
        after keys and respective values are merged based on the string 
        similarity of keys and by taking into account look_ahead items
        
        Note that the list of tuples if ordered in decreasing order of values
        
    excluded_items_list:  list of tuples (keys, values) that were merged with
        the keys and values in new_count_list  
        
    Example
    -------
    a = ['banana', 'bananan', 'banana', 'dog', 'rice', 'riceeeee', 'ricee', 'dog']
    occurences=Counter(a)
    new_count_list, excluded_items_list = add_by_similarity(occurences, 
                    topN = 2, 
                    look_ahead = len(a),
                    threshold = 0.8,
                    similarity = 'jaccard'
                    )  
    
    print(new_count_list)      
    [('banana', 3), ('dog', 2)]
    
    print(excluded_items_list) 
    [('bananan', 1), ('ricee', 1)]
    '''
    # Get list of tuples from the Counter obj
    count_list = counter.most_common()
    count_list_look_ahead = count_list[:look_ahead]

    # Make a list of items
    all_items = []
    all_values = []
    for item in count_list_look_ahead:
        all_items.append(item[0])
        all_values.append(item[1])
        
    # Keep track of the matched positions - mark with 0 the ones not iterated
    iterated = [0]*len(all_items)
    idx_exclude = []#here we keep all the idx for the items that we are merging 
    for c,item in enumerate(all_items):
        if iterated[c] == 0:
            # Get the string similarity for the current string and the rest
            similarities = string_similarity(
                                            all_items,
                                            source_str = item,
                                            similarity = similarity
                                            )   
            
            if similarity == 'jaccard':#jaccard so reverse so that 0=best match
                similarities = 1 - similarities
            idx = np.where(similarities > threshold)[0]
            if idx.size > 1:#enter the merging operation only if we have more than 1 items to merge
                min_idx = np.min(idx)#this contains the top item add the values to it
                val = [all_values[i] for i in idx] 
                val = sum(val)
                all_values[min_idx] = val
                
                # Keep track of the idx of the merged items (everything but the
                # min_idx that gets all the assignements)
                idx_exclude.extend(idx[idx != min_idx])
                
                # Update iterated so we do not consider again these positions in idx
                for i in idx: iterated[i] = 1 
                
    # Return also the exluded items as a control of what takes place
    excluded_items = [item for i,item in enumerate(all_items) if i in idx_exclude]
    excluded_values = [item for i,item in enumerate(all_values) if i in idx_exclude]
                
    # Shrink the list of all_items and all_values by excluding the idx_exclude
    all_items = [item for i,item in enumerate(all_items) if i not in idx_exclude]
    all_values = [item for i,item in enumerate(all_values) if i not in idx_exclude]            
                
    # Populate the new count list with the updated values and items 
    # Check if the merging dropped the len of all_items below topN. If so
    # return topN=len(all_items)
    if len(all_items) < (topN): topN = len(all_items)               
    new_count_list = [(all_items[i], all_values[i]) for i in range(topN)]
    
    # Order the list of tuples with decreasing nr of publications
    new_count_list = sorted(new_count_list, 
                            key = lambda tup: tup[1], 
                            reverse = True
                            )    
    
    # Assemble the excluded items in a list of tuples              
    excluded_items_list = [(excluded_items[i], excluded_values[i]) for i in range(len(excluded_items))]
    
    # Order the list of tuples with decreasing nr of publications
    excluded_items_list = sorted(excluded_items_list, 
                                 key = lambda tup: tup[1], 
                                 reverse = True
                                 ) 
    
    return new_count_list, excluded_items_list

def tf_idf_similarity(list_txt):
    '''
    Compute the term frequency–inverse document frequency (tfidf) 
    give a list of str. Return also the pair-wise similarity based on tfidf.
    
    NOTE: the function uses scikit-learn's TfidfVectorizer
    
    Input
    -----
    list_txt: list of str among which the frequency–inverse document frequency
        will be computed
    
    Output
    ------
    tfidf: sparse matrix of shape (n_samples, n_features) 
        in Compressed Sparse Row format
        (returned from scikit-learn's TfidfVectorizer.fit_transform())
        
    pairwise_similarity: sparse matrix of shape (n_samples, n_samples)
        in Compressed Sparse Row format 
    
    '''
    vect = TfidfVectorizer(min_df=1, 
                           stop_words='english')                                                                                                                                                                                                   
    tfidf = vect.fit_transform(list_txt)                                                                                                                                                                                                                       
    pairwise_similarity = tfidf*tfidf.T 
    
    return tfidf, pairwise_similarity 

   

def get_nounphrases_verbs(list_txt):
    '''
    Count number of noun phrases, verbs and entities in a list of str
    with spacy 
    
    Input
    -----
    list_txt: list of str of len M
    
    Output
    ------
    nr_noun_phrases: list of int of len M
        
    nr_verbs: list of int of len M
        
    nr_entities: list of int of len M
    
    Note: the "english long model" of spacy is used for counting nouns, verbs 
    and entitites (see https://spacy.io/usage/linguistic-features)
    '''
    nlp = spacy.load('en_core_web_lg')# 'long' model 
    nr_noun_phrases = []
    nr_verbs = []
    nr_entities = []
    for txt in list_txt: 
        doc = nlp(txt)
        nr_noun_phrases.append(len([chunk.text for chunk in doc.noun_chunks]))
        nr_verbs.append(len([token.lemma_ for token in doc if token.pos_ == "VERB"]))
        nr_entities.append(len(doc.ents))
    
    return nr_noun_phrases, nr_verbs, nr_entities 

def get_chars_words(list_txt, chrs_to_remove=None):
    '''
    Count the nr of words and chars of the str in the list list_txt
    
    Input
    -----
    list_txt: list of str
    
    chrs_to_remove: list of str, default None, of characters to be removed 
        from txt prior to charcater counting. If None then no removal is 
        applied
        
    nr_chars: list of int containing the nr of chars such that
        nr_chars[i] == nr of chars in list_txt[i]
    
    nr_words: list of int containing the nr of words such that
        nr_chars[i] == nr of chars in list_txt[i]
    '''
    nr_chars = []
    nr_words = []
    for txt in list_txt:
        nr_chars.append(count_chars_no_white(txt, 
                                             chrs_to_remove))
        nr_words.append(count_words(txt))
        
    return nr_chars, nr_words    
 
def get_unique_strs(list_txt, 
                    exclude = []
                    ):
    '''
    Given a list of str that contains S ';' seperated strings, create a list 
    containing all strings, all unique strings and a collections object 
    containg the occurences of each unique str.
    
    Input
    -----
    list_txt: list of str - can be colon ';' seperated. The un_strs and 
        all_strs lists will be populated based on the comma-based splits of 
        each str in the list_txt.
        
    exclude: list of str, default [], containing str that will function as filter
        e.g., ['', ' ']    
        
    Output
    ------
    all_strs: list of str. All the str resulting from the iteration and 
        slitting of the list of str list_txt.
        
    un_strs: list of str. Contains all the unique strings in all_strs.

    occurences: collections.Counter object. Contains info about the occurences
        of each str in un_strs based on all_strs.      
    '''
    strs_interim = [txt.split(';') for txt in list_txt] 
    all_strs = []
    for i in strs_interim:#TODO: I am pretty positive that this can be compressed/refined for speed 
        all_strs.extend(i)
        
    # Exclude from all_strs the str in exclude
    all_strs = [s for s in all_strs if s not in exclude]
    # Get unique str      
    un_strs = list(set(all_strs))    
       
    # Count how many times the unique strings appear
    # Use the Counter and return a collections.Counter obj
    occurences=Counter(all_strs)
        
    return all_strs, un_strs, occurences

def trim_txt(txt, chars_for_trim='.'):
    '''
    Trim txt based on the list chars_for_trim
    The txt will be split based on all characters in chars_for_trim
    and the first half from this split will be returned
    
    Input
    -----
    txt: str, string to be trimmed
    
    chars_for_trim: list of str specifying the chracters to be used for 
        iteratively trimminf txt.
        The split based on each character is sequential and exhastive:
        txt will be split based on chars_for_trim[0] and the first half of this
        split will be split based on chars_for_trim[1] etc
        
    Output
    ------
    txt: str, the trimmed str
    '''
    for c in chars_for_trim:
        txt = txt.rsplit(c)[0]
    if len(txt) > 1:
        txt.rstrip()   
        
    return txt      

def string_similarity(string_list,
                      source_str = None,
                      similarity = 'seq_matcher',
                      ):
    '''
    Compute similarity between strings
    
    Input
    -----
    string_list: list of str
    
    source_str: str, default None - if specified, then the similarities will
        be computed between source_str and all str in string_list
   
   similarity: str,  {'jaccard', 'spacy', 'seq_matcher'}, specifying which 
       similarity measure will be used
       
       'jaccard': jaccard similarity
       'spacy': vector similarity (cosine) will be used based on en_core_web_lg
                 see spaCy documentation: 
                 https://spacy.io/usage/vectors-similarity
                
                Note: this process is quiet slow and there must be a good 
                reason for opting for this 
       'seq_matcher': used the quick_ratio method of the SequenceMatcher class
               see https://docs.python.org/2.4/lib/sequence-matcher.html
               
    NOTE: all the above metrics are normalized in the range [0 1] with 0=low
    and 1=high  similarity, EXCEPT for 'jaccard' where 0=high and 1=low 
    
    Roundoff errors and vector operations may give rise to slight deviations 
    from such range
           
    Output
    ------ 
    all_similarities: ndarray of shape (N,N), if source_str is None, or 
        shape(N,) if source_str is not None
        
        Contains floats denoting the similarity between strings such that:
        if source_str is None: 
        all_similarities[i,j] = similarity between string_list[i] and string_list[j]   
        
        if source_str is None: 
        all_similarities[i] = similarity between source_str and string_list[i] 
    
    Examples
    --------
    s = ['Today I waited and stared to the ocean.', 
         'The owl of Minerva flies only after dusk',
         'ice scream','When the sword wakes, time sleeps',
         'bike',
         'pancak']
    s_source = 'pancake'
    
    #With 'jaccard'
    similarity = string_similarity(s,
                                   source_str = s_source,
                                   similarity = 'jaccard',
                                   )
    print(similarity)
    array([0.96969697, 1.        , 1.        , 0.93103448, 0.875     ,
       0.16666667])
    
    Note that since the jaccard index is used, all it matters are the 
    characters of strings that are compared, and not the semantics. Thus,
    the lower value (for jaccard better match) is observed with the last string
    'pancak'
    
    #With 'spacy'    
    similarity = string_similarity(s,
                                   source_str = s_source,
                                   similarity = 'spacy',
                                   )
    print(similarity)
    array([0.20109747, 0.23185522, 0.33395686, 0.18453109, 0.1748583 ,
       0.        ])
    
    Note that this will generate a warning, since there is no word vector
    for 'pancak' (a non-existent word) and thus similarity is 0 (non-existent)
    
    Note that the higher similarity is observed with 'ice scream' due to the 
    semantic nature of the similarity
    
    #With 'seq_matcher'
    
    similarity = string_similarity(s,
                               source_str = s_source,
                               similarity = 'seq_matcher',
                               )
    print(similarity)
    array([0.2173913 , 0.21276596, 0.35294118, 0.25      , 0.36363636,
       0.92307692])
    
    Similarity highest with 'pancak'
    '''    
    if source_str is None:
        all_similarities = np.zeros((len(string_list), len(string_list)))
        if similarity == 'spacy': nlp = en_core_web_lg.load()
        if similarity == 'jaccard': jaccard = Jaccard(2) 
        for i,source in enumerate(string_list):
            print(i)
            if similarity == 'spacy': 
                token1 = nlp(source)
                current_similarities = [token1.similarity(nlp(target)) for target in string_list]
                all_similarities[i,:] = current_similarities
            if similarity == 'seq_matcher':
               current_similarities = [SequenceMatcher(None, 
                                                       source, target).quick_ratio() for target in string_list]
               all_similarities[i,:] = current_similarities
            if similarity == 'jaccard':
               current_similarities = [jaccard.distance(source, target) for target in string_list]
               all_similarities[i,:] = current_similarities   
               
    if source_str is not None:
        all_similarities = np.zeros((len(string_list),))
        if similarity == 'seq_matcher':
            all_similarities = [SequenceMatcher(None, 
                                                source_str, target).quick_ratio() for target in string_list]
        if similarity == 'spacy': 
            nlp = en_core_web_lg.load()
            token1 = nlp(source_str)
            all_similarities = [token1.similarity(nlp(target)) for target in string_list]
        if similarity == 'jaccard':
            jaccard = Jaccard(2) 
            all_similarities = [jaccard.distance(source_str, target) for target in string_list]
     
    all_similarities = np.asarray(all_similarities)  
      
    return all_similarities 

def count_chars_no_white(txt, chrs_to_remove=None):
    '''
    Count the characters of a string after removing whitespaces or (optinally)
    characters specified in chrs_to_remove.
    
    Input
    -----
    txt: str, containing the string for character counting
    
    chrs_to_remove: list of str, default None, of characters to be removed 
        from txt prior to charcater counting. If None then no removal is 
        applied
    
    Output
    ------
    The number of characters in txt    
    '''
    txt = txt.rstrip()#remove whitespace
    if chrs_to_remove is not None:
        for c in chrs_to_remove:
            txt = txt.replace(c,'')#remove chars in chrs_to_remove
    
    return len(txt)
   
def count_words(txt):
    '''
    Count the words of a string.
    
    Input
    -----
    txt: str, containing the string for character counting
    
    Output
    ------
    The number of words in txt  
    '''
    return len(re.findall(r'\w+', txt))
