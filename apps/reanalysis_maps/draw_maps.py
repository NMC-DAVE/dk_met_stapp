# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.


"""
Synoptic Composite Ploting script

refer to https://github.com/tomerburg/python_gallery
"""


#Import the necessary libraries
import os
import numpy as np
import uuid
from threading import Lock
import xarray as xr
import datetime as dt
import scipy.ndimage as ndimage
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.colors as col
import matplotlib.gridspec as gridspec

import cartopy
from cartopy import crs as ccrs
import cartopy.feature as cfeature
from cartopy import util as cu

import metpy
import metpy.calc as calc

import streamlit as st

from nmc_met_graphics.cmap.cm import gradient
from nmc_met_graphics.plot.util import add_mslp_label
from nmc_met_graphics.magics import dynamics

# thread lock
lock = Lock()

def load_variables(date_obj, map_region=[50, 160, 6, 60]):
    """
    Load the variables from UAlbany's opendap server

    Args:
        date_obj (datetime): a datetime object
    """

    # To make parsing the date easier, convert it into a datetime object
    # and get it into various formats
    yyyy = date_obj.year

    # For loading multiple files in
    files = []

    # Loop through each variable specified
    variables = ['u','v','g','t','pmsl','pwat']
    for var in variables:
        #Append file into list of files to open
        filepath = "http://thredds.atmos.albany.edu:8080/thredds/dodsC/CFSR/%s/%s.%s.0p5.anl.nc"%(yyyy,var,yyyy)
        files.append(filepath)
        
    # Load in the variable(s) as an xarray Dataset and assign them into "data"
    st.info("Load CFSR data from http://thredds.atmos.albany.edu:8080/thredds/dodsC/")
    data = xr.open_mfdataset(files, combine='by_coords', cache=False)
    
    # construct sub region
    sub_region = {'lon':slice(map_region[0], map_region[1]),
                  'lat':slice(map_region[2], map_region[3])}

    # Subset and load data
    data = data.sel(time=date_obj) ;  my_bar = st.progress(0)
    u200 = data['u'].sel(lev=200, **sub_region).load()
    my_bar.progress(10)
    v200 = data['v'].sel(lev=200, **sub_region).load()
    my_bar.progress(20)
    gh200 = data['g'].sel(lev=200, **sub_region).load()
    my_bar.progress(30)
    u500 = data['u'].sel(lev=500, **sub_region).load()
    my_bar.progress(40)
    v500 = data['v'].sel(lev=500, **sub_region).load()
    my_bar.progress(50)
    gh500 = data['g'].sel(lev=500, **sub_region).load()
    my_bar.progress(60)
    u850 = data['u'].sel(lev=850, **sub_region).load()
    my_bar.progress(70)
    v850 = data['v'].sel(lev=850, **sub_region).load()
    my_bar.progress(80)
    t850 = data['t'].sel(lev=850, **sub_region).load()
    my_bar.progress(90)
    mslp = data['pmsl'].sel(**sub_region).load()
    my_bar.progress(95)
    pwat = data['pwat'].sel(**sub_region).load()
    my_bar.progress(100)
    
    # convert units
    t850.metpy.convert_units('degC')
    pwat.metpy.convert_units('mm')
    mslp.metpy.convert_units('hPa')
    
    # close data
    #data.close()

    return u200, v200, gh200, u500, v500, gh500, u850, v850, t850, mslp, pwat


#Spatially smooth a 2D variable
def smooth(prod,sig):
    
    #Check if variable is an xarray dataarray
    try:
        lats = prod.lat.values
        lons = prod.lon.values
        prod = ndimage.gaussian_filter(prod,sigma=sig,order=0)
        prod = xr.DataArray(prod, coords=[lats, lons], dims=['lat', 'lon'])
    except:
        prod = ndimage.gaussian_filter(prod,sigma=sig,order=0)
    
    return prod


def draw_composite_map(date_obj, t850, u200, v200, u500, v500, mslp, gh500, u850, v850, pwat):
    """
    Draw synoptic composite map.

    Args:
        map_subset (int, optional): [description]. Defaults to 1.
        map_region (list, optional): [description]. Defaults to [70, 140, 20, 60].
    """
     
    #Get lat and lon arrays for this dataset:
    lat = t850.lat.values
    lon = t850.lon.values

    #========================================================================================================
    # Create a Basemap plotting figure and add geography
    #========================================================================================================

    #Create a Plate Carree projection object
    proj_ccrs = ccrs.Miller(central_longitude=0.0)

    #Create figure and axes for main plot and colorbars
    fig = plt.figure(figsize=(18,12),dpi=125)
    gs = gridspec.GridSpec(12, 36, figure=fig) #[ytop:ybot, xleft:xright]
    ax = plt.subplot(gs[:, :-1],projection=proj_ccrs) #main plot
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax2 = plt.subplot(gs[:4, -1]) #top plot
    ax2.set_xticklabels([])
    ax2.set_yticklabels([])
    ax3 = plt.subplot(gs[4:8, -1]) #bottom plot
    ax3.set_xticklabels([])
    ax3.set_yticklabels([])
    ax4 = plt.subplot(gs[8:, -1]) #bottom plot
    ax4.set_xticklabels([])
    ax4.set_yticklabels([])

    #Add political boundaries and coastlines
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=1.2)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidths=1.2)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidths=0.5)

    #Add land/lake/ocean masking
    land_mask = cfeature.NaturalEarthFeature('physical', 'land', '50m',
                                        edgecolor='face', facecolor='#e6e6e6')
    sea_mask = cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                        edgecolor='face', facecolor='#ffffff')
    lake_mask = cfeature.NaturalEarthFeature('physical', 'lakes', '50m',
                                        edgecolor='face', facecolor='#ffffff')
    ax.add_feature(sea_mask,zorder=0)
    ax.add_feature(land_mask,zorder=0)
    ax.add_feature(lake_mask,zorder=0)

    #========================================================================================================
    # Fill contours
    #========================================================================================================

    #--------------------------------------------------------------------------------------------------------
    # 850-hPa temperature
    #--------------------------------------------------------------------------------------------------------

    #Specify contour settings
    clevs = np.arange(-40,40,1)
    cmap = plt.cm.jet
    extend = "both"

    #Contour fill this variable
    norm = col.BoundaryNorm(clevs,cmap.N)
    cs = ax.contourf(lon,lat,t850,clevs,cmap=cmap,norm=norm,extend=extend,transform=proj_ccrs,alpha=0.1)

    #--------------------------------------------------------------------------------------------------------
    # PWAT
    #--------------------------------------------------------------------------------------------------------

    #Specify contour settings
    clevs = np.arange(20,71,0.5)

    #Define a color gradient for PWAT
    pwat_colors = gradient([[(255,255,255),0.0],[(255,255,255),20.0]],
                [[(205,255,205),20.0],[(0,255,0),34.0]],
                [[(0,255,0),34.0],[(0,115,0),67.0]])
    cmap = pwat_colors.get_cmap(clevs)
    extend = "max"

    #Contour fill this variable
    norm = col.BoundaryNorm(clevs,cmap.N)
    cs = ax.contourf(lon,lat,pwat,clevs,cmap=cmap,norm=norm,extend=extend,transform=proj_ccrs,alpha=0.9)

    #Add a color bar
    cbar = plt.colorbar(cs,cax=ax2,shrink=0.75,pad=0.01,ticks=[20,30,40,50,60,70])

    #--------------------------------------------------------------------------------------------------------
    # 250-hPa wind
    #--------------------------------------------------------------------------------------------------------

    #Get the data for this variable
    wind = calc.wind_speed(u200, v200)

    #Specify contour settings
    clevs = [40,50,60,70,80,90,100,110]
    cmap = col.ListedColormap(['#99E3FB','#47B6FB','#0F77F7','#AC97F5','#A267F4','#9126F5','#E118F3','#E118F3'])
    extend = "max"

    #Contour fill this variable
    norm = col.BoundaryNorm(clevs,cmap.N)
    cs = ax.contourf(lon,lat,wind,clevs,cmap=cmap,norm=norm,extend=extend,transform=proj_ccrs)

    #Add a color bar
    cbar = plt.colorbar(cs,cax=ax3,shrink=0.75,pad=0.01,ticks=clevs)

    #--------------------------------------------------------------------------------------------------------
    # 500-hPa smoothed vorticity
    #--------------------------------------------------------------------------------------------------------

    #Get the data for this variable
    dx,dy = calc.lat_lon_grid_deltas(lon,lat)
    vort = calc.vorticity(u500,v500,dx,dy)
    smooth_vort = smooth(vort, 5.0) * 10**5

    #Specify contour settings
    clevs = np.arange(2,20,1)
    cmap = plt.cm.autumn_r
    extend = "max"

    #Contour fill this variable
    norm = col.BoundaryNorm(clevs,cmap.N)
    cs = ax.contourf(lon,lat,smooth_vort,clevs,cmap=cmap,norm=norm,extend=extend,transform=proj_ccrs,alpha=0.3)

    #Add a color bar
    cbar = plt.colorbar(cs,cax=ax4,shrink=0.75,pad=0.01,ticks=clevs[::2])
            
    #========================================================================================================
    # Contours
    #========================================================================================================

    #--------------------------------------------------------------------------------------------------------
    # MSLP
    #--------------------------------------------------------------------------------------------------------

    #Specify contour settings
    clevs = np.arange(960,1040+4,4)
    style = 'solid' #Plot solid lines
    color = 'red' #Plot lines as gray
    width = 0.8 #Width of contours 0.25

    #Contour this variable
    cs = ax.contour(lon,lat,mslp,clevs,colors=color,linewidths=width,linestyles=style,transform=proj_ccrs,alpha=0.9)

    #Include value labels
    ax.clabel(cs, inline=1, fontsize=9, fmt='%d')

    #--------------------------------------------------------------------------------------------------------
    # Geopotential heights
    #--------------------------------------------------------------------------------------------------------

    #Get the data for this variable
    gh500 = gh500 / 10.0

    #Specify contour settings
    clevs = np.arange(480,612,4)
    style = 'solid' #Plot solid lines
    color = 'black' #Plot lines as gray
    width = 2.0 #Width of contours

    #Contour this variable
    cs = ax.contour(lon,lat,gh500,clevs,colors=color,linewidths=width,linestyles=style,transform=proj_ccrs)

    #Include value labels
    ax.clabel(cs, inline=1, fontsize=12, fmt='%d')

    #--------------------------------------------------------------------------------------------------------
    # Surface barbs
    #--------------------------------------------------------------------------------------------------------

    #Plot wind barbs
    quivers = ax.quiver(lon, lat, u850.values, v850.values, transform=proj_ccrs, regrid_shape=(38,30), scale=820, alpha=0.5)

    #--------------------------------------------------------------------------------------------------------
    # Label highs & lows
    #--------------------------------------------------------------------------------------------------------

    #Label highs and lows
    add_mslp_label(ax, proj_ccrs, mslp, lat, lon)

    #========================================================================================================
    # Step 6. Add legend, plot title, then save image and close
    #========================================================================================================

    #Add custom legend
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='#00A123', lw=5),
                    Line2D([0], [0], color='#0F77F7', lw=5),
                    Line2D([0], [0], color='#FFC000', lw=5),
                    Line2D([0], [0], color='k', lw=2),
                    Line2D([0], [0], color='k', lw=0.1, marker=r'$\rightarrow$', ms=20),
                    Line2D([0], [0], color='r', lw=0.8),]

    ax.legend(custom_lines, ['PWAT (mm)', '200-hPa Wind (m/s)', '500-hPa Vorticity', '500-hPa Height (dam)', '850-hPa Wind (m/s)', 'MSLP (hPa)'], loc=2, prop={'size':12})

    #Format plot title
    title = "Synoptic Composite \nValid: " + dt.datetime.strftime(date_obj,'%Y-%m-%d %H%M UTC')
    st = plt.suptitle(title,fontweight='bold',fontsize=16)
    st.set_y(0.92)

    #Return figuration
    return(fig)


def draw_wind_upper_map(date_obj, uwind, vwind, gh, map_region):
    """
    Draw troposphere upper wind map (like 250hPa).

    Args:
        data_input ([type]): [description]
        date_obj ([type]): [description]
        map_region (list, optional): [description]. Defaults to [70, 140, 20, 60].
    """

    # draw the figure
    lock.acquire()

    try:
        # set tempfile
        outfile = '/tmp/wind200_%s' % uuid.uuid4().hex

        # draw the figure
        dynamics.draw_wind_upper(
            uwind.values, vwind.values, uwind['lon'].values, uwind['lat'].values,
            gh=gh.values, skip_vector=2, map_region=map_region, date_obj=date_obj,
            head_info="200hPa Wind[m/s] and Height[gpm]",
            outfile=outfile)
        
        # read image
        outfile = outfile+".png"
        image = Image.open(outfile)
        os.remove(outfile)
    finally:
        lock.release()
    
    # return image
    return image

