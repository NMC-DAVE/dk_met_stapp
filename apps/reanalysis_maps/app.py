# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
检索特定日期和范围的CFSR再分析数据, 并绘制相关的天气图.
"""

import sys
import os
import uuid
import requests
import pickle
import datetime
from multiprocessing import Process, Manager
import numpy as np
import xarray as xr
import metpy
import streamlit as st

# set page title
st.beta_set_page_config(page_title="历史天气图分析", layout="wide")

from nmc_met_io.retrieve_cmadaas import cmadaas_obs_by_time
from nmc_met_graphics.util import  get_map_regions
from nmc_met_graphics.web import SessionState, ipyplot

sys.path.append('.')
import draw_maps

# set session state
state = SessionState.get(img1=None, img2=None, img3=None)


def  main():
    # application title
    st.title("历史天气图分析")
    st.header('——检索1979年1月1日以来的地面观测日值和天气图')

    # application information
    st.sidebar.image('http://image.nmc.cn/assets/img/index/nmc_logo_3.png', width=300)
    st.sidebar.markdown('**天气预报技术研发室**')

    # Input data date
    data_date = st.sidebar.date_input(
        "输入日期:", datetime.date(2016, 7, 19),
        min_value=datetime.date(1979, 1, 1),
        max_value=datetime.date.today() - datetime.timedelta(days=2))

    # Input data time
    data_time = st.sidebar.selectbox('选择时刻(UTC):', ('00', '06', '12', '18'), index=2)

    # construct datetime string
    datetime_str = data_date.strftime('%Y%m%d') + data_time
    date_obj = datetime.datetime.strptime(datetime_str,'%Y%m%d%H')

    # subset data
    map_regions = get_map_regions()
    select_items = list(map_regions.keys())
    select_items.append('自定义')
    select_item = st.sidebar.selectbox('选择空间范围:', select_items)
    if select_item == '自定义':
        map_region_str = st.sidebar.text_input('输入空间范围[West, East, South, North]:', '70, 140, 10, 65')
        map_region = list(map(float, map_region_str.split(", ")))
    else:
        map_region = map_regions[select_item]

    # draw the figures
    if st.sidebar.button('绘制天气图'):
        # load data
        st.info('载入CFSR数据, http://thredds.atmos.albany.edu:8080/thredds/dodsC/ (taking 30s)')
        data = load_variables(date_obj, map_region=map_region)
        
        # draw the synoptic compsite
        fig = draw_maps.draw_composite_map(
            date_obj, data['t850'], data['u200'], data['v200'], data['u500'], 
            data['v500'], data['mslp'], data['gh500'], data['u850'], data['v850'], data['pwat'])
        state.img1 = fig

        # draw weather analysis maps
        manager = Manager()
        return_dict = manager.dict()
        p = Process(target=draw_maps.draw_weather_analysis, args=(date_obj, data, map_region, return_dict))
        p.start()
        p.join()
        if return_dict[0] is not None:
            state.img2 = return_dict[0]
        else:
            st.info('制作各层天气图失效!')
            state.img2 = None
        return_dict.clear()
        manager.shutdown()
        p.close()
        del data

        # load observation data
        obs_data = cmadaas_obs_by_time(
            date_obj.strftime('%Y%m%d000000'), data_code="SURF_CHN_MUL_DAY", sta_levels="011,012,013",
            elements="Station_Id_C,Lat,Lon,Alti,TEM_Max,TEM_Min,VIS_Min,PRE_Time_0808,SPRE_Time_0808,WIN_S_Max")
        if obs_data is not None:
            state.img3 = draw_maps.draw_observation(obs_data, date_obj, map_region)
        else:
            state.img3 = None

    if state.img1 is None or state.img2 is None:
        st.info('请点击左侧**绘制天气图**按钮生成或更新图像.')
    else:
        # display observation
        if state.img3 is not None:
            st.markdown(
                '''
                ------
                ### 选择站点实况观测''')
            options = [key for key in state.img3.keys()]
            option = st.selectbox('', options, 0)
            st.plotly_chart(state.img3[option], use_container_width=False)

        # display synoptic composite
        st.markdown(
                '''
                ------
                ### 环流形势综合图''')
        st.pyplot(state.img1)

        # display weather analysis maps
        st.markdown(
                '''
                ------
                ### 点击天气图弹出放大''')
        images = np.asarray([*state.img2.values()], dtype=np.object)
        labels = np.asarray([*state.img2.keys()])
        html = ipyplot.display_image_gallery(images, labels, img_width=200)
        st.markdown(html, unsafe_allow_html=True)
        # options = [key for key in state.img2.keys()]
        #options = st.multiselect(
        #    '', options, ['500hPa_height', 'precipitable_water', 'mean_sea_level_pressure'])
        #for option in options:
        #    st.image(state.img2[option], use_column_width=True)

    st.sidebar.markdown(
    '''
    ------
    [CFSR](https://climatedataguide.ucar.edu/climate-data/climate-forecast-system-reanalysis-cfsr)(CLIMATE FORECAST SYSTEM REANALYSIS)
    再分析资料是NCEP提供的第三代再分析产品. 本程序从Albany大学Thredds服务器检索指定日期时刻及范围的CFSR数据（从1979年1月1日以来每日4次, 全球范围）, 
    并绘制高空环流形势天气图. 
    ''')


def read_variable(varname, date_obj):
    """
    read varaible from load or remote thredds server.
    """
    # To make parsing the date easier, convert it into a datetime object
    # and get it into various formats
    yyyy = date_obj.year

    filepath_html   = "http://10.28.49.118:8080/thredds/dodsC/CFSR/%s/%s.%s.0p5.anl.nc.html"%(yyyy,'%s',yyyy)
    filepath_local  = "http://10.28.49.118:8080/thredds/dodsC/CFSR/%s/%s.%s.0p5.anl.nc"%(yyyy,'%s',yyyy)
    filepath_remote = "http://thredds.atmos.albany.edu:8080/thredds/dodsC/CFSR/%s/%s.%s.0p5.anl.nc"%(yyyy,'%s',yyyy)

    result = requests.get(filepath_html%(varname))
    if result.status_code == 200:
        data = xr.open_dataset(filepath_local%(varname))
    else:
        data = xr.open_dataset(filepath_remote%(varname))
    data = data.sel(time=date_obj)

    return data


def load_variables(date_obj, map_region=[50, 160, 6, 60]):
    """
    Load the variables from UAlbany's opendap server

    Args:
        date_obj (datetime): a datetime object
    """

    # construct sub region
    sub_region = {'lon':slice(map_region[0], map_region[1]),
                  'lat':slice(map_region[2], map_region[3])}

    # Subset and load data
    subdata = {}

    # wind field
    my_bar = st.progress(0)
    data = read_variable('u', date_obj)
    subdata['u200'] = data['u'].sel(lev=200, **sub_region).load()      ; my_bar.progress(4)
    subdata['u500'] = data['u'].sel(lev=500, **sub_region).load()      ; my_bar.progress(8)
    subdata['u700'] = data['u'].sel(lev=700, **sub_region).load()      ; my_bar.progress(12)
    subdata['u850'] = data['u'].sel(lev=850, **sub_region).load()      ; my_bar.progress(16)
    subdata['u925'] = data['u'].sel(lev=925, **sub_region).load()      ; my_bar.progress(20)
    data = read_variable('v', date_obj)
    subdata['v200'] = data['v'].sel(lev=200, **sub_region).load()      ; my_bar.progress(24)
    subdata['v500'] = data['v'].sel(lev=500, **sub_region).load()      ; my_bar.progress(28)
    subdata['v700'] = data['v'].sel(lev=700, **sub_region).load()      ; my_bar.progress(32)
    subdata['v850'] = data['v'].sel(lev=850, **sub_region).load()      ; my_bar.progress(36)
    subdata['v925'] = data['v'].sel(lev=925, **sub_region).load()      ; my_bar.progress(40)

    # vertical velocity field
    data = read_variable('w', date_obj)
    subdata['w700'] = data['w'].sel(lev=700, **sub_region).load()      ; my_bar.progress(45)

    # pressure on pv surface
    data = read_variable('pres_pv', date_obj)
    subdata['pres_pv2'] = data['pres_pv'].sel(lev=2.0E-6, **sub_region).load()   ; my_bar.progress(50)
    subdata['pres_pv2'].metpy.convert_units('hPa')

    # geopotential height
    data = read_variable('g', date_obj)
    subdata['gh200'] = data['g'].sel(lev=200, **sub_region).load()  ; my_bar.progress(55)
    subdata['gh500'] = data['g'].sel(lev=500, **sub_region).load()  ; my_bar.progress(60)
    subdata['gh700'] = data['g'].sel(lev=700, **sub_region).load()  ; my_bar.progress(62)

    # high temperature
    data = read_variable('t', date_obj)
    subdata['t500'] = data['t'].sel(lev=500, **sub_region).load()   ; my_bar.progress(64)
    subdata['t700'] = data['t'].sel(lev=700, **sub_region).load()   ; my_bar.progress(66)
    subdata['t850'] = data['t'].sel(lev=850, **sub_region).load()   ; my_bar.progress(68)
    subdata['t925'] = data['t'].sel(lev=925, **sub_region).load()   ; my_bar.progress(70)
    subdata['t500'].metpy.convert_units('degC')
    subdata['t700'].metpy.convert_units('degC')
    subdata['t850'].metpy.convert_units('degC')
    subdata['t925'].metpy.convert_units('degC')
    
    # high moisture field
    data = read_variable('q', date_obj)
    subdata['q700'] = data['q'].sel(lev=700, **sub_region).load()   ; my_bar.progress(75)
    subdata['q850'] = data['q'].sel(lev=850, **sub_region).load()   ; my_bar.progress(80)
    subdata['q925'] = data['q'].sel(lev=925, **sub_region).load()   ; my_bar.progress(85)

    # mean sea level pressure
    data = read_variable('pmsl', date_obj)
    subdata['mslp'] = data['pmsl'].sel(**sub_region).load()         ; my_bar.progress(90)
    subdata['mslp'].metpy.convert_units('hPa')

    # precipitable water
    data = read_variable('pwat', date_obj)
    subdata['pwat'] = data['pwat'].sel(**sub_region).load()         ; my_bar.progress(100)
    subdata['pwat'].metpy.convert_units('mm')

    # surface temperature, 2018-, this data is wrong.
    #data = read_variable('tsfc', date_obj)
    #subdata['tsfc'] = data['tsfc'].sel(**sub_region).load()         ; my_bar.progress(100)
    #subdata['tsfc'].metpy.convert_units('degC')

    return subdata


if __name__ == "__main__":
    main()
