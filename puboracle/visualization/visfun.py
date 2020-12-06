#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plotly as py
from plotly.graph_objs import Figure, Scatter, Layout, layout
import seaborn as sns
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame

def vis_lon_lat(longitude=None, latitude=None):
    '''
    Visualize longitude and latitude on a global atlas
    
    Input
    -----
    longitude: list, float, of len N with all longitude values
    latitude: list, float, of len N with all latitude values
    '''
    # Assemble the lists to an ndarray
    data = np.vstack((np.asarray(longitude),
                      np.asarray(latitude))
                     ).T
    
    # Make data frame from longitude and latitude ndarray
    df = pd.DataFrame({'longitude': data[:, 0], 'latitude': data[:, 1]})
    
    # Use shapely to make a Point obj from lon lat data frame
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = GeoDataFrame(df, geometry=geometry)   
    
    # Basic earth map from geopandas
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    gdf.plot(ax=world.plot(figsize = (10, 6)), 
                           marker = 'o', 
                           color = 'red', 
                           markersize = 2
            )
  
    
def vis_lon_lat_de(latlon, 
                   file_de_map = None, 
                   title = 'Title',
                   folder_save = None,
                   file_name = None,
                   size = None,
                   color_circles = [0/255, 204/255, 204/255],
                   plot_axes = False
                   ):
    '''
    Plot latitude and longitude in a map of Germany. The result is a 
    "bubble map".
    
    Input
    -----
    latlon: list of tuples (lat,lon) to be plotted with len(latlon)=M
    
    file_de_map: str, default None, of the full path to the shape file (.shp) 
        of the map of Germany (available e.g. from this resource:
                     https://www.suche-postleitzahl.org/downloads)
    
    title: str, default 'Title', containing the title of the figure/map
    
    folder_save: pathlib.PosixPath object, default None, 
        specifying the folder where the map will be saved
        
    file_name: str, default None, for the file to be saved. Note that map will 
        be saved as a .png file
    
    size: list of len M or ndarray of shape (M,), default None, 
        with M=len(latlon), of positive int specifying the size of the 
        circle for each pair of (lat,lot) in latlon
      
    color_circles: list of floats of len 3, default [0/255, 204/255, 204/255], 
        specifying the [R,G,B] values of the circles 
        
    plot_axes: bool, default False, soecifying if the map will be plotted
        with lat lon axes (=True) or not(=False)    
    ''' 
    plt.style.use('seaborn')
    plz_shape_df = gpd.read_file(file_de_map, dtype={'plz': str})
    
    #plt.rcParams['figure.figsize'] = [16, 11]    
    fig, ax = plt.subplots()
    if plot_axes is False: ax.axis('off')#no lat lon axes
    plz_shape_df.plot(ax = ax, 
                      color = [201/255, 191/255, 191/255], 
                      alpha = 0.8
                      )
    
    # Plot lat lon
    for counter,ll in enumerate(latlon):    
        ax.scatter(
                ll[0], 
                ll[1], 
                marker = 'o',
                c = color_circles, 
                alpha = 0.5,
                s = size[counter]
                )
    
    ax.set(
           title = title, 
           aspect = 1.3, 
           facecolor = 'white'
          )
     
    if folder_save is not None:
        fig = ax.get_figure()
        file_name = title + '.png'
        file_to_save= folder_save / file_name
        fig.savefig(file_to_save, 
                    format = 'png',
                    dpi = 300,
                    bbox_inches = 'tight')
            

def rescale_size(values, min_val_size = 3):
    '''
    Rescale values such that the min value in values has min_val_size value and
    each of the rest values are scaled such that:
        values / np.min(values)) * min_val_size
    
    This rescalling is usefull for visualizing values as e.g.,size differences
    
    Input
    -----
    values: ndarray of shape (N,) with the values to be rescaled
    
    min_val_size: positive int, default 3, that will be used for the rescaling 
        such that: values / np.min(values)) * min_val_size 
    
    Output
    ------
    rescaled: ndarray of shape (N,) with the rescaled values
    '''
    rescaled = (values / np.min(values)) * min_val_size 
    return rescaled 

def visualize_counter_selection(selection_list,
                                folder_save = None,
                                file_name = None
                                ):
    
    sns.set_theme(style="whitegrid")
    values = []
    names = []
    index = []
    for counter,sl in enumerate(selection_list):
        names.append(sl[0])
        values.append(sl[1])
        index.append(counter)
        
    pubs = {
            'affiliation' : names,
            'nr of pubs' : values
            } 
    
    df = pd.DataFrame(pubs, index=index)
    plt.figure()
    ax = sns.barplot(x = "nr of pubs", 
                     y = "affiliation", 
                     data = df
                     )

    if folder_save is not None:
        fig = ax.get_figure()
        file_name = file_name + '.png'
        file_to_save = folder_save / file_name
        fig.savefig(file_to_save, 
                    format = 'png', 
                    dpi = 300,
                    bbox_inches = 'tight'
                    )
        
def plot_graph(layt,
               net = None,
               filename_save = None,
               title = None
               ):
    '''
    Plot a network layout produced with igraph with plotly 
    
    Input
    -----
    layt: igraph.layout.Layout object
    
    net: igraph.Graph object. The network whose layout will be plotted
    
    filename_save: str specifying a path and a filename for saving 
        the .html that will be produced from the function
        
    title: str for the title of the plot    
    
    NOTE: This function wraps this plotly code:
    https://plotly.com/python/v3/igraph-networkx-comparison/#igraph
    to facilitate plotting of igraph network layouts without writting 
    extensive lines of code. It uses, however, the offline plotting option
    
    For exploiting all plotly capacities, please refer to the corresponding
    tutorials. Current function only offers a basic use of plotly for 
    interactive exploration of network layouts produced by igraph
    '''
    # Get labels, nr of nodes and edge list
    labels = list(net.vs['label'])
    N = len(labels)#nr of nodes
    E = [e.tuple for e in net.es]#list of edges (tuples of node ids)
    
    Xn=[layt[k][0] for k in range(N)]
    Yn=[layt[k][1] for k in range(N)]
    Xe=[]
    Ye=[]
    for e in E:
        Xe+=[layt[e[0]][0],layt[e[1]][0], None]
        Ye+=[layt[e[0]][1],layt[e[1]][1], None]
    
    trace1=Scatter(x=Xe,
                   y=Ye,
                   mode='lines',
                   line= dict(color='rgb(210,210,210)', width=1),
                   hoverinfo='none'
                   )
    
    trace2=Scatter(x=Xn,
                   y=Yn,
                   mode='markers',
                   name='ntw',
                   marker=dict(symbol='circle-dot',
                               size=5,
                               color='#6959CD',
                               line=dict(color='rgb(50,50,50)', 
                                          width=0.5)
                               ),
                   text=labels,
                   hoverinfo='text'
                   )
    
    axis=dict(showline=False, # hide axis line, grid, ticklabels and  title
              zeroline=False,
              showgrid=False,
              showticklabels=False,
              title=''
              )
    
    width=800
    height=800
    layout_to_plot=Layout(title=title,
                          font= dict(size=12),
                          showlegend=False,
                          autosize=False,
                          width=width,
                          height=height,
                          xaxis=layout.XAxis(axis),
                          yaxis=layout.YAxis(axis),
                          margin=layout.Margin(
                            l=40,
                            r=40,
                            b=85,
                            t=100,
                        ),
        hovermode='closest',
        annotations=[
               dict(
                    showarrow=False,
                    text=title,
                    xref='paper',
                    yref='paper',
                    x=0,
                    y=-0.1,
                    xanchor='left',
                    yanchor='bottom',
                    font=dict(size=14)
                   )
            ]
        )
    
    data=[trace1, trace2]
    fig=Figure(data=data, layout=layout_to_plot)
    py.offline.plot(fig, filename=filename_save)