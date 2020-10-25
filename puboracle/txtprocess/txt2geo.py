#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np

from geopy.geocoders import Nominatim
import pycountry

from . import txtfun

def get_lat_lon_from_text(all_txt_location, abstract_to_specific=False):
    '''
    Get spatial information (latitude, longitude) from textual description
    of locations
    
    Input
    -----
    all_txt_location: list of str with the textual description of the location
        The str of each list S can be comma ';' seperated, so grouped textual
        descriptions, as str M, can be processed per list entry.
        Moreover each M str in each main str S, can be comma ',' seperated,
        in a way that if split, then the substrings s1,2...n correspond
        from less to more abstract location description (see example).
        
    abstract_to_specific: bool, default False, if True the longitude and 
        latitude will be searched by using abstract to more specific textual
        descriptions of location.
        
    Output
    ------ 
    lat: list of float, with the decoded latitude from the textual description
    lan: list of float, with the decoded longitude from the textual description
    full_txt_location: list of str, with the textual description used for 
        extracting lat and lon
    
    Examples
    --------
    affil = ['Nova Southeastern University, College of Osteopathic Medicine, Fort Lauderdale, FL 33134, USA.;Zhejiang University, College of Pharmaceutical Science, Zhejiang Province 310027, PR China.'] 
    lat, lon, full_txt_location  = get_lat_lon_from_text(affil)
    '''
    geolocator = Nominatim(user_agent='test_affiliation_plot')
    lat=[]
    lon=[]
    full_txt_location = []
    nr_txt_loc = len(all_txt_location)
    # Iterate all lists in all_txt_location
    for counter,current_affil in enumerate(all_txt_location):
        print('\nUnpacking textual location descriptions...:', counter+1, '/', nr_txt_loc)
        current_affil_split = current_affil.rsplit(';')#str is a comma (;) seperated str with affiliations
        for loc in current_affil_split:
            print('\nSearching for latitude and longitude for location description:', loc)
            full_txt_location.append(loc)#keep the textual description of the location
            loc_split = loc.rsplit(',')#str is a comma (,) seperated str with specific to abstract text of the location
            location = None
            # Loop through the loc_split which is a textual location
            # description from concrete to abstract, where more concrete 
            # location is in loc_split[0] and more abstract in loc_split[-1] 
            # If abstract_to_specific is True, then reverse the list
            # loc_split so that we iterate the location text from abstract to 
            # concrete.
            if abstract_to_specific is True:
                loc_split = loc_split[::-1]
            for l in loc_split:
                location = geolocator.geocode(txtfun.remove_digits_from_str(l))
                if location is not None: break#if valid location is returned, exit 
            if location is None:
                print('\nNo latitude and longitude for...:', loc_split)
                lat.append(np.nan)
                lon.append(np.nan)
            else:
                lat.append(location.latitude)
                lon.append(location.longitude)
            
    return lat, lon, full_txt_location

def get_lat_lon_from_text_wordwise(all_txt_location,
                                   reverse = True,
                                   user_agent = 'testing'
                                   ):
    '''
    Get latitude and longitude information by using individual words from 
    a list of strings (e.g., an affiliation or address)
    
    all_txt_location: list of str, len M, containing the strings to be used
        for extracting latitude and longitude information
        
        Strings can be ';' comma-seperated and in that case the will be split
        and each part processed sequentially
        
    reverse: bool, default True, reversing the order of words found in a string
        This is usefull if we want to exploit a string where spatial
        location is structured, e.g. in an affiliation words specify location
        in a concrete-to-abstract with cities and countries being at the
        end of string
        
    user_agent: str, default 'testing', specifying user id
        (used by: geopy.geocoders Nominatim)
        
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
    geolocator = Nominatim(user_agent=user_agent)
    lat=[]
    lon=[]
    full_txt_location = []
    nr_txt_loc = len(all_txt_location)
    # Iterate all lists in all_txt_location
    for counter,current_affil in enumerate(all_txt_location):
        print('\nUnpacking textual location descriptions...:', counter+1, '/', nr_txt_loc)
        current_affil_split = current_affil.rsplit(';')#str is a comma (;) seperated str with affiliations
        for loc in current_affil_split:
            print('\nSearching for latitude and longitude for location description:', loc)
            location = None
            loc_split = loc.split(' ')#get words, assuming they are seperated by space
            if reverse is True:
                loc_split = loc_split[::-1]#reverse so that we process the city faster (with affiliation formats, city usually near the end)
            for l in loc_split:
                l = l.replace(',','')#TODO: remove all non-character elements not only ','
                location = geolocator.geocode(l)
                if location is not None:
                    full_txt_location.append(l)#keep the textual description of the location that resulted in the lat lon
                    break#if valid location is returned, exit 
            if location is None:
                print('\nNo latitude and longitude for...:', loc_split)
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
