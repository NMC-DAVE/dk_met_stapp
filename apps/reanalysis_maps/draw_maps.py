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
import collections
import xarray as xr
import datetime as dt
import scipy.ndimage as ndimage
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.colors as col
import matplotlib.gridspec as gridspec

import streamlit as st

import cartopy
from cartopy import crs as ccrs
import cartopy.feature as cfeature
from cartopy import util as cu

import metpy.calc as calc
from metpy.units import units

from nmc_met_graphics.cmap.cm import gradient
from nmc_met_graphics.plot.util import add_mslp_label
from nmc_met_graphics.plot.china_map import add_china_map_2cartopy
from nmc_met_graphics.magics import dynamics, thermal, pv, moisture


def _get_image_file(infile):
    """
    Read image file and remove the file.
    """
    infile = infile + ".png"
    if os.path.isfile(infile):
        image = Image.open(infile)
        os.remove(infile)
        return image
    else:
        return None

def draw_weather_analysis(date_obj, data, map_region):
    """
    Draw weather analysis map.
    """

    # image dictionary
    images = collections.OrderedDict()

    # draw 2PVU surface pressure
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    pv.draw_pres_pv2(
        data['pres_pv2'].values, data['pres_pv2']['lon'].values, data['pres_pv2']['lat'].values,
        map_region=map_region, date_obj=date_obj, outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 200hPa wind field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_wind_upper(
        data['u200'].values, data['v200'].values, 
        data['u200']['lon'].values, data['u200']['lat'].values,
        gh=data['gh200'].values, map_region=map_region, date_obj=date_obj,
        head_info="200hPa Wind[m/s] and Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 500hPa height and temperature
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_height_temp(
        data['gh500'].values, data['t500'].values, 
        data['gh500']['lon'].values, data['gh500']['lat'].values, 
        map_region=map_region, date_obj=date_obj,
        head_info="500hPa Height[gpm] and Temperature[DegC]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 500hPa vorticity
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_vort_high(
        data['u500'].values, data['v500'].values, 
        data['u500']['lon'].values, data['u500']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="500hPa Wind, Vorticity and Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 700hPa vertical velocity
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_vvel_high(
        data['u700'].values, data['v700'].values, data['w700'].values, 
        data['w700']['lon'].values, data['w700']['lat'].values,
        gh=data['gh700'].values, map_region=map_region, date_obj=date_obj,
        head_info="700hPa Wind, Vertical Velocity[Pa/s] and Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 700hPa wind field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_wind_high(
        data['u700'].values, data['v700'].values, 
        data['u700']['lon'].values, data['u700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="700hPa Wind[m/s] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 700hPa temperature field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    thermal.draw_temp_high(
        data['t700'].values, data['t700']['lon'].values, data['t700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="700hPa Temperature[Degree] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 700hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(data['q700'], data['t700'], 700 * units.hPa) * 100
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_rh_high(
        data['u700'].values, data['v700'].values, rh.magnitude,
        data['u700']['lon'].values, data['u700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="700hPa Wind[m/s], Relative Humidity[%] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 850hPa wind field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_wind_high(
        data['u850'].values, data['v850'].values, 
        data['u850']['lon'].values, data['u850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="850hPa Wind[m/s] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 850hPa temperature field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    thermal.draw_temp_high(
        data['t850'].values, data['t850']['lon'].values, data['t850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="850hPa Temperature[Degree] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 850hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(data['q850'], data['t850'], 850 * units.hPa) * 100
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_rh_high(
        data['u850'].values, data['v850'].values, rh.magnitude,
        data['u850']['lon'].values, data['u850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="850hPa Wind[m/s], Relative Humidity[%] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 925hPa specific field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_sp_high(
        data['u850'].values, data['v850'].values, data['q850'].values*1000.,
        data['q850']['lon'].values, data['q850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="850hPa Wind[m/s], Specific Humidity[g/Kg] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 925hPa temperature field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    thermal.draw_temp_high(
        data['t925'].values, data['t925']['lon'].values, data['t925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="925hPa Temperature[Degree] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 925hPa wind field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_wind_high(
        data['u925'].values, data['v925'].values, 
        data['u925']['lon'].values, data['u925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="925hPa Wind[m/s] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 925hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(data['q925'], data['t925'], 925 * units.hPa) * 100
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_rh_high(
        data['u925'].values, data['v925'].values, rh.magnitude,
        data['u925']['lon'].values, data['u925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="925hPa Wind[m/s], Relative Humidity[%] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw 925hPa specific field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_sp_high(
        data['u925'].values, data['v925'].values, data['q925'].values*1000.,
        data['q925']['lon'].values, data['q925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj,
        head_info="925hPa Wind[m/s], Specific Humidity[g/Kg] and 500hPa Height[gpm]", outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw precipitable water field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    moisture.draw_pwat(
        data['pwat'].values, data['pwat']['lon'].values, data['pwat']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj, outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)

    # draw mean sea level pressure field
    outfile = '/tmp/reanalysis_map_%s' % uuid.uuid4().hex
    dynamics.draw_mslp(
        data['mslp'].values, data['mslp']['lon'].values, data['mslp']['lat'].values,
        gh=data['gh500'].values, map_region=map_region, date_obj=date_obj, outfile=outfile)
    image = _get_image_file(outfile)
    st.image(image, use_column_width=True)


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
    # Step 6. Add map boundary, legend, plot title, then save image and close
    #========================================================================================================

    #Add china province boundary
    add_china_map_2cartopy(ax, name='province')

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



