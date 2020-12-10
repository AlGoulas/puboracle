#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pycountry

from . import txtfun

def get_lat_lon_from_text(all_txt_location,
                          geophrase_delimeter = ',',
                          clean_string = None,
                          reverse = True,
                          verbose = False, 
                          user_agent = 'testing',
                          min_delay_seconds = 1,
                          timeout = 10
                          ):
    '''
    Get latitude and longitude information by using individual words from 
    a list of strings (e.g., an affiliation or address)
    
    all_txt_location: list of str, len M, containing the strings to be used
        for extracting latitude and longitude information
        
        Strings can be ';' comma-seperated and in that case the will be split
        and each part processed sequentially
    
    geophrase_delimeter: str, default ',', that is used to split the text in
        substrings (geophrases) to be used for geocoding
    
    clean_string: str, {'unicode','alphanum', 'alpha'}, default None, 
        specifying if the text to be used for geocoding should be processed
            'unicode': only unicode characters are kept
            'alphanum': only alphanumeric characters are kept
            'alpha': only alphabetical characters (A-Za-Z) are kept
    
    reverse: bool, default True, reversing the order of geophrases found 
        in a string
        
        This is usefull if we want to exploit a string where spatial
        location is structured, e.g. in an affiliation words specify location
        in a concrete-to-abstract with cities and countries being at the
        end of string
        
    user_agent: str, default 'testing', specifying user id
        (used by: geopy.geocoders Nominatim)
                
    min_delay_seconds: int, default 1, specifying the seconds that 
        we must wait before sending a request to the server for geocoding
        between [1,rand_wait_time_sec]
        So at least 1 sec of waiting time as NEEDED from the Nominatim 
        geocoder of geopy
      
    timeout: int, default 10, specifying the time waiting before the server for
        the geocoding times out
        
    Output
    ------
    lat: list of float, len M, containing the estimated latitude such that
        lat[i] is the estimated latitude for all_txt_location[i] 
        
    lon: list of float, len M, containing the estimated longitude such that
        lon[i] is the estimated longitude for all_txt_location[i]  
        
    full_txt_location: list of str, containing the string that was used to 
        estimate lat lon
        
    NOTE: the function will keep the first lat and lot that is not None and
        stop iterating further words in a string
        
    Examples
    --------   
    s = [ 
        'University of Tusk, Arizona',
        'Indoor AG, Arndstrasse 30, Bonn, Germany',
        'Signal Pro, Rue de la Port 5, Bordeaux'
        ]

    lat,lon,txt = get_lat_lon_from_text_wordwise(s)
    
    print(lat)
    [34.395342, 51.0834196, 44.841225]
    
    print(lon)
    [-111.7632755, 10.4234469, -0.5800364]
    
    print(txt)
    ['Arizona', 'Germany', 'Bordeaux']
    '''
    geolocator = Nominatim(user_agent = user_agent, timeout = timeout)
    if min_delay_seconds is not None:#if wait time specified use a RateLimiter
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds = min_delay_seconds) 
    else:
        geocode = geolocator.geocode   
    lat=[]
    lon=[]
    full_txt_location = []
    nr_txt_loc = len(all_txt_location)
    # Iterate all lists in all_txt_location
    for counter,atl in enumerate(all_txt_location):
        if verbose is True:
            print('\nUnpacking textual location descriptions...:', counter+1, '/', nr_txt_loc)
        #current_affil_split = current_affil.rsplit(main_delimeter)#str is a comma (;) seperated str with affiliations
        if verbose is True:
            print('\nSearching for latitude and longitude for location description:', atl)
        location = None
        atl_split = atl.split(geophrase_delimeter)#get geophrase to be decoded, assuming they are seperated by geophrase_delimeter
        if reverse is True:atl_split = atl_split[::-1]#reverse so that we process the city faster (with affiliation formats, city usually near the end)
        atl_split_not_found = []#keep here all the strings that did not lead to geolocation for each step (not for all in all_txt_location)
        for loc in atl_split:
            if clean_string == 'unicode': loc = txtfun.keep_only_unicode(loc)
            if clean_string == 'alphanum': loc = txtfun.keep_only_alphanum(loc)
            location = None    
            if loc:#if the processed string in non empty, start geocoding
                if verbose is True:
                    print('\nGeolocation based on...:', loc)
                #Geocoding
                location = geocode(loc)                                        
                if location is None:atl_split_not_found.append(loc)
                if location is not None:
                    full_txt_location.append(loc)#keep the textual description of the location that resulted in the lat lon
                    break#if valid location is returned, exit 
        if location is None:
            if verbose is True:
                print('\nNo latitude and longitude for...:', atl_split_not_found)
            lat.append(np.nan)
            lon.append(np.nan)
        else:
            lat.append(location.latitude)
            lon.append(location.longitude)
            
    return lat, lon, full_txt_location

def trace_countries_in_text(txt, allowed_countries = []):
    '''
    Find countries in a string and keep the string based on a list of allowed
    countries
    
    Note: the function uses pycountry to trace countries and countries are 
    detected based on the capacity of this package
    
    Input
    -----
    txt: list of str
    
    allowed_countries: list of str, default [], with the counries that are 
        allowed
    
    Output
    ------
    txt_allowed: list of str containing countries that are allowed 
        (not in allowed_countries list)
        
    txt_not_allowed: list of str containing countries that are not allowed 
        (in allowed_countries list) 
        
    Example
    ------- 
    s = [
         'I was in Spain last week', 
         'French fries do not originate from France.', 
         'I went for vacations to Ireland. It was fun.'
         ]

    (txt_allowed, 
     txt_not_allowed) = trace_countries_in_text(s, 
                                                allowed_countries = ['France', 'Ireland']
                                                )
    print(txt_allowed)
    ['French fries do not originate from France.',
     'I went for vacations to Ireland. It was fun.']
    
    print(txt_not_allowed)
    ['I was in Spain last week']
    '''
    txt_allowed = []
    txt_not_allowed = []
    for t in txt:
        not_allowed = False
        for country in pycountry.countries:
            if country.name in t and country.name not in allowed_countries:
                not_allowed = True
        if not_allowed is True:
            txt_not_allowed.append(t)
        else:
            txt_allowed.append(t)
                           
    return txt_allowed, txt_not_allowed 
