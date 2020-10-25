#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import itertools
    
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
    