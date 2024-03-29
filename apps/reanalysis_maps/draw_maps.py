# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.


"""
Synoptic Composite Ploting script

refer to https://github.com/tomerburg/python_gallery
"""


#Import the necessary libraries
import collections
import numpy as np
import xarray as xr
import pandas as pd
import datetime as dt
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import matplotlib.colors as col
import matplotlib.gridspec as gridspec

from cartopy import crs as ccrs
import cartopy.feature as cfeature
from cartopy import util as cu

import nmc_met_io.config as CONFIG
import plotly.express as px

import metpy.calc as calc
from metpy.units import units

from nmc_met_graphics.cmap.cm import gradient
from nmc_met_graphics.plot.util import add_mslp_label
from nmc_met_graphics.plot.mapview import add_china_map_2cartopy
from nmc_met_graphics.magics import dynamics, thermal, pv, moisture


def draw_observation(data, date_obj, map_region):
    """
    Draw observation map with plotly
    """

     # set mapbox token
    px.set_mapbox_access_token(CONFIG.CONFIG['MAPBOX']['token'])

    # create figures
    map_center = {'lat':(map_region[2] + map_region[3]) * 0.5,
                  'lon':(map_region[0] + map_region[1]) * 0.5}
    figs = collections.OrderedDict()

    # draw precipitation
    bins = [0.1, 10, 25, 50, 100, 250, 1200]
    keys = ['0.1~10', '10~25', '25~50', '50~100', '100~250', '>=250']
    cols = ['lightgreen', 'yellow', 'lightskyblue', 'blue', 'magenta','maroon']
    cols_map = dict(zip(keys, cols))
    data['rain'] = pd.cut(data['PRE_Time_0808'], bins=bins, labels=keys)
    data['Rainfall'] = '['+data['Lon'].round(2).astype(str) + ',' + data['Lat'].round(2).astype(str) + ']: ' + \
                       data['PRE_Time_0808'].astype(str)
    data['rain_size'] = data['PRE_Time_0808'] + data['PRE_Time_0808'].mean()
    df = data[data['rain'].notna()]
    if df.shape[0] >= 2:
        figs['Rainfall'] = px.scatter_mapbox(
            df, lat="Lat", lon="Lon", color="rain", category_orders={'rain': keys}, color_discrete_map = cols_map,
            hover_data={'Rainfall':True, 'Lon':False, 'Lat':False, 'rain':False, 'rain_size':False},
            mapbox_style='satellite-streets', size="rain_size", center=map_center, size_max=10, zoom=4,
            title = 'Accumulated precipitation ({})'.format(date_obj.strftime("%Y%m%d 08-08")),
            width=900, height=700)

    # draw maximum temperature
    bins = [35, 37, 40, 60]
    keys = ['35~37', '37~40', '>=40']
    cols = ['rgb(255,191,187)', 'rgb(250,89,0)', 'rgb(230,0,8)']
    cols_map = dict(zip(keys, cols))
    data['max_temp_warning'] = pd.cut(data['TEM_Max'], bins=bins, labels=keys)
    data['max_temp'] = '['+data['Lon'].round(2).astype(str) + ',' + data['Lat'].round(2).astype(str) + ']: ' + \
                       data['TEM_Max'].astype(str)
    df = data[data['max_temp_warning'].notna()]
    if df.shape[0] >= 2:
        figs['Max_temperature'] = px.scatter_mapbox(
            df, lat="Lat", lon="Lon", color="max_temp_warning", category_orders={'max_temp_warning': keys}, 
            color_discrete_map = cols_map,
            hover_data={'max_temp':True, 'Lon':False, 'Lat':False, 'max_temp_warning':False, 'TEM_Max':False},
            mapbox_style='satellite-streets', size="TEM_Max", center=map_center, size_max=10, zoom=4,
            title = 'Maximum temperature ({})'.format(date_obj.strftime("%Y%m%d 08-08")),
            width=900, height=700)

    # draw minimum temperature
    bins = [-120, -40, -30, -20, -10, 0]
    keys = ['<=-40','-40~-30', '-30~-20', '-20~-10', '-10~0']
    cols = ['rgb(178,1,223)', 'rgb(8,7,249)', 'rgb(5,71,162)', 'rgb(5,109,250)', 'rgb(111,176,248)']
    cols_map = dict(zip(keys, cols))
    data['min_temp_warning'] = pd.cut(data['TEM_Min'], bins=bins, labels=keys)
    data['min_temp'] = '['+data['Lon'].round(2).astype(str) + ',' + data['Lat'].round(2).astype(str) + ']: ' + \
                       data['TEM_Min'].astype(str)
    df = data[data['min_temp_warning'].notna()]
    if df.shape[0] >= 2:
        figs['Min_temprature'] = px.scatter_mapbox(
            df, lat="Lat", lon="Lon", color="min_temp_warning", category_orders={'min_temp_warning': keys}, 
            color_discrete_map = cols_map,
            hover_data={'min_temp':True, 'Lon':False, 'Lat':False, 'min_temp_warning':False, 'TEM_Min':False},
            mapbox_style='satellite-streets', size=-1.0*df["TEM_Min"], center=map_center, size_max=10, zoom=4,
            title = 'Minimum temperature ({})'.format(date_obj.strftime("%Y%m%d 08-08")),
            width=900, height=700)

    # draw low visibility
    data['VIS_Min'] /= 1000.0
    bins = [0, 0.05, 0.2, 0.5, 1]
    keys = ['<=0.05','0.05~0.2', '0.2~0.5', '0.5~1']
    cols = ['rgb(0,82,77)', 'rgb(0,153,160)', 'rgb(0,210,204)', 'rgb(95,255,252)']
    cols_map = dict(zip(keys, cols))
    data['min_vis_warning'] = pd.cut(data['VIS_Min'], bins=bins, labels=keys)
    data['VIS_Min_size'] = 2.0-data["VIS_Min"]
    data['min_vis'] = '['+data['Lon'].round(2).astype(str) + ',' + data['Lat'].round(2).astype(str) + ']: ' + \
                      data['VIS_Min'].astype(str)
    df = data[data['min_vis_warning'].notna()]
    if df.shape[0] >= 2:
        figs['Low_visibility'] = px.scatter_mapbox(
            df, lat="Lat", lon="Lon", color="min_vis_warning", category_orders={'min_vis_warning': keys}, 
            color_discrete_map = cols_map,
            hover_data={'min_vis':True, 'Lon':False, 'Lat':False, 'min_vis_warning':False, 'VIS_Min_size':False},
            mapbox_style='satellite-streets', size="VIS_Min_size", center=map_center, size_max=10, zoom=4,
            title = 'Low visibility ({})'.format(date_obj.strftime("%Y%m%d 08-08")),
            width=900, height=700)

    # draw high wind
    bins = [10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.7, 37.0, 120]
    keys = ['10.8~13.8','13.9~17.1', '17.2~20.7', '20.8~24.4', '24.5~28.4', '28.5~32.6', '32.7~36.9', '>=37.0']
    cols = ['rgb(0,210,244)', 'rgb(0,125,255)', 'rgb(253,255,0)', 'rgb(247,213,0)',
            'rgb(255,141,0)', 'rgb(251,89,91)', 'rgb(255,3,0)', 'rgb(178,1,223)']
    cols_map = dict(zip(keys, cols))
    data['max_win_warning'] = pd.cut(data['WIN_S_Max'], bins=bins, labels=keys)
    data['max_win'] = '['+data['Lon'].round(2).astype(str) + ',' + data['Lat'].round(2).astype(str) + ']: ' + \
                      data['WIN_S_Max'].astype(str)
    df = data[data['max_win_warning'].notna()]
    if df.shape[0] >= 2:
        figs['High_wind'] = px.scatter_mapbox(
            df, lat="Lat", lon="Lon", color="max_win_warning", category_orders={'max_win_warning': keys}, 
            color_discrete_map = cols_map,
            hover_data={'max_win':True, 'Lon':False, 'Lat':False, 'max_win_warning':False, 'WIN_S_Max':False},
            mapbox_style='satellite-streets', size="WIN_S_Max", center=map_center, size_max=10, zoom=4,
            title = 'Maximum wind speed ({})'.format(date_obj.strftime("%Y%m%d 08-08")),
            width=1000, height=800)

    return figs


def draw_weather_analysis(date_obj, data, map_region, return_dict):
    """
    Draw weather analysis map.
    """

    # image dictionary
    images = collections.OrderedDict()
    return_dict[0] = None

    # draw 2PVU surface pressure
    image = pv.draw_pres_pv2(
        data['pres_pv2'].values, data['pres_pv2']['lon'].values, data['pres_pv2']['lat'].values,
        map_region=map_region, title_kwargs={'name':'CFSR', 'time': date_obj})
    images['2PVU_Surface_Pressure'] = image

    # draw 200hPa wind field
    image = dynamics.draw_wind_upper(
        data['u200'].values, data['v200'].values, 
        data['u200']['lon'].values, data['u200']['lat'].values,
        gh=data['gh200'].values, map_region=map_region, 
        title_kwargs={'name':'CFSR', 'head': "200hPa Wind | GH", 'time': date_obj})
    images['200hPa_Wind'] = image

    # draw 500hPa height and temperature
    image = dynamics.draw_height_temp(
        data['gh500'].values, data['t500'].values, 
        data['gh500']['lon'].values, data['gh500']['lat'].values, map_region=map_region, 
        title_kwargs={'name':'CFSR', 'head': "500hPa GH | T", 'time': date_obj})
    images['500hPa_Height'] = image

    # draw 500hPa vorticity
    image = dynamics.draw_vort_high(
        data['u500'].values, data['v500'].values, 
        data['u500']['lon'].values, data['u500']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "500hPa Wind | Vorticity | GH", 'time': date_obj})
    images['500hPa_Vorticity'] = image

    # draw 700hPa vertical velocity
    image = dynamics.draw_vvel_high(
        data['u700'].values, data['v700'].values, data['w700'].values, 
        data['w700']['lon'].values, data['w700']['lat'].values,
        gh=data['gh700'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "700hPa Vertical Velocity | Wind | GH", 'time': date_obj})
    images['700hPa_Vertical_Velocity'] = image

    # draw 700hPa wind field
    image = dynamics.draw_wind_high(
        data['u700'].values, data['v700'].values, 
        data['u700']['lon'].values, data['u700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "700hPa Wind | 500hPa GH", 'time': date_obj})
    images['700hPa_Wind'] = image

    # draw 700hPa temperature field
    image = thermal.draw_temp_high(
        data['t700'].values, data['t700']['lon'].values, data['t700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "700hPa T | 500hPa GH", 'time': date_obj})
    images['700hPa_Temperature'] = image

    # draw 700hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(700 * units.hPa, data['t700'], data['q700']) * 100
    image = moisture.draw_rh_high(
        data['u700'].values, data['v700'].values, rh.values,
        data['u700']['lon'].values, data['u700']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "700hPa RH | Wind | 500hPa GH", 'time': date_obj})
    images['700hPa_Relative_Humidity'] = image

    # draw 850hPa wind field
    image = dynamics.draw_wind_high(
        data['u850'].values, data['v850'].values, 
        data['u850']['lon'].values, data['u850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "850hPa Wind | 500hPa GH", 'time': date_obj})
    images['850hPa_Wind'] = image

    # draw 850hPa temperature field
    image = thermal.draw_temp_high(
        data['t850'].values, data['t850']['lon'].values, data['t850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "850hPa T | 500hPa GH", 'time': date_obj})
    images['850hPa_Temperature'] = image

    # draw 850hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(850 * units.hPa, data['t850'], data['q850']) * 100
    image = moisture.draw_rh_high(
        data['u850'].values, data['v850'].values, rh.values,
        data['u850']['lon'].values, data['u850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "850hPa RH | Wind | 500hPa GH", 'time': date_obj})
    images['850hPa_Relative_Humidity'] = image

    # draw 850hPa specific field
    image = moisture.draw_sp_high(
        data['u850'].values, data['v850'].values, data['q850'].values*1000.,
        data['q850']['lon'].values, data['q850']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "850hPa SP | Wind | 500hPa GH", 'time': date_obj})
    images['850hPa_Specific_Humidity'] = image

    # draw 925hPa temperature field
    image = thermal.draw_temp_high(
        data['t925'].values, data['t925']['lon'].values, data['t925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "925hPa T | 500hPa GH", 'time': date_obj})
    images['925hPa_Temperature'] = image

    # draw 925hPa wind field
    image = dynamics.draw_wind_high(
        data['u925'].values, data['v925'].values, 
        data['u925']['lon'].values, data['u925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "925hPa Wind | 500hPa GH", 'time': date_obj})
    images['925hPa_Wind'] = image

    # draw 925hPa relative humidity
    rh = calc.relative_humidity_from_specific_humidity(925 * units.hPa, data['t925'], data['q925']) * 100
    image = moisture.draw_rh_high(
        data['u925'].values, data['v925'].values, rh.values,
        data['u925']['lon'].values, data['u925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "925hPa RH | Wind | 500hPa GH", 'time': date_obj})
    images['925hPa_Relative_Humdity'] = image

    # draw 925hPa specific field
    image = moisture.draw_sp_high(
        data['u925'].values, data['v925'].values, data['q925'].values*1000.,
        data['q925']['lon'].values, data['q925']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "925hPa SP | Wind | 500hPa GH", 'time': date_obj})
    images['925hPa_Specific_Humidity'] = image

    # draw precipitable water field
    image = moisture.draw_pwat(
        data['pwat'].values, data['pwat']['lon'].values, data['pwat']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "Precipitable Water | 500hPa GH", 'time': date_obj})
    images['Precipitable_Water'] = image

    # draw mean sea level pressure field
    image = dynamics.draw_mslp(
        data['mslp'].values, data['mslp']['lon'].values, data['mslp']['lat'].values,
        gh=data['gh500'].values, map_region=map_region,
        title_kwargs={'name':'CFSR', 'head': "MSLP | 500hPa GH", 'time': date_obj})
    images['Mean_Sea_Level_Pressure'] = image

    return_dict[0] = images


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
    All variables must have the same region.

    Args:
        date_obj (datetime) : datetime ojbect.
        t850 (xarray): 850hPa temperature, must have lat and lon coordinates.
        u200, v200 (xarray): 200hPa u and v wind component.
        u500, v500 (xarray): 500hPa u and v wind component.
        mslp (xarray): mean sea level pressure.
        gh500 (xarray): 500hPa geopotential height.
        u850, v850 (xarray): 850hPa u and v wind component.
        pwat (xarray): precipitable water.
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
    cmap = plt.get_cmap('jet')
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
    _ = plt.colorbar(cs,cax=ax2,shrink=0.75,pad=0.01,ticks=[20,30,40,50,60,70])

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
    _ = plt.colorbar(cs,cax=ax3,shrink=0.75,pad=0.01,ticks=clevs)

    #--------------------------------------------------------------------------------------------------------
    # 500-hPa smoothed vorticity
    #--------------------------------------------------------------------------------------------------------

    #Get the data for this variable
    dx,dy = calc.lat_lon_grid_deltas(lon,lat)
    vort = calc.vorticity(u500, v500, dx=dx, dy=dy)
    smooth_vort = smooth(vort, 5.0) * 10**5

    #Specify contour settings
    clevs = np.arange(2,20,1)
    cmap = plt.get_cmap('autumn_r')
    extend = "max"

    #Contour fill this variable
    norm = col.BoundaryNorm(clevs,cmap.N)
    cs = ax.contourf(lon,lat,smooth_vort,clevs,cmap=cmap,norm=norm,extend=extend,transform=proj_ccrs,alpha=0.3)

    #Add a color bar
    _ = plt.colorbar(cs,cax=ax4,shrink=0.75,pad=0.01,ticks=clevs[::2])
            
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
    _ = ax.quiver(lon, lat, u850.values, v850.values, transform=proj_ccrs, regrid_shape=(38,30), scale=820, alpha=0.5)

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



