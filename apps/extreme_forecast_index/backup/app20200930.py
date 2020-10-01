# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
  分析显示极端天气指数产品.
  本程序从集合预报网格共享文件夹中读取解压好的grib原始数据, 读取原始数据并绘制图像.

  . Ubuntu环境下, 将欧洲中心极端天气指数数据加载到本地硬盘上, 例如
      sudo mount //10.20.xx.xx/eps_grib/efi /media/efi_data -o username=liwei,password=xxxxxx
  . 设置config.ini的路径信息
  . streamlit run app.py

  # 本程序依赖程序库
     - eccodes, conda install -c conda-forge eccodes
     - cfgrib, pip install cfgrib
     - nmc_met_io, pip install nmc-met-io
     - nmc_met_graphics, pip install nmc-met-graphics
"""

import os
import shutil
import time
import configparser
import datetime
import collections
from multiprocessing import Process, Manager
import numpy as np
import streamlit as st

from nmc_met_io.read_grib import read_ecmwf_ens_efi
from nmc_met_graphics.util import get_map_global_regions
from nmc_met_graphics.magics.efi import draw_efi
from nmc_met_graphics.web import ipyplot

# set page title
st.beta_set_page_config(page_title="极端天气指数", layout="wide")

def main():
    # application title
    st.title("集合预报极端天气指数分析")

    # application information
    st.sidebar.image('http://image.nmc.cn/assets/img/index/nmc_logo_3.png', width=300)
    st.sidebar.markdown('**天气预报技术研发室**')

    # get data list
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    data_dir = config['DEFAULT']['data_directory']
    data_subdir = [dir for dir in os.listdir(data_dir) if len(dir) == 10 and dir.isnumeric()]
    data_subdir.sort(reverse=True)
    data_subdir = data_subdir[0:20]
    
    # Input data time
    datetime_str = st.sidebar.selectbox('起报时间:', data_subdir)
    init_time = datetime.datetime.strptime(datetime_str,'%Y%m%d%H')
    init_hour = init_time.hour

    # Select map region
    map_regions = get_map_global_regions()
    select_items = list(map_regions.keys())
    select_items.append('自定义')
    select_item = st.sidebar.selectbox('选择空间范围:', select_items)
    if select_item == '自定义':
        map_region_str = st.sidebar.text_input('输入空间范围[West, East, South, North]:', '70, 140, 10, 65')
        map_region = list(map(float, map_region_str.split(", ")))
    else:
        map_region = map_regions[select_item]

    # Select variables
    variables = {
        'Total precipiation': 'tpi',
        'Mean 2m temperature': '2ti',
        'Maximum 2m temperature': 'mx2ti',
        'Minimum 2m temperature': 'mn2ti',
        '10m wind speed': '10wsi',
        'Maximum wind gust': '10fgi',
        'CAPE-shear': 'capesi',
        'CAPE': 'capei',
        'Snowfall': 'sfi'}
    select_item = st.sidebar.selectbox('选择显示变量:', list(variables.keys()))

    # draw the figures
    if st.sidebar.button('绘制天气图'):
        # create progress bar
        my_bar = st.progress(0)

        # get the datafile path from temporary directory
        temp_dir = config['DEFAULT']['temp_directory']
        datafile = os.path.join(temp_dir, datetime_str+'.EFI.240')
        # if not exist, copy from original directory
        if not os.path.isfile(datafile):
            datafile1 = os.path.join(data_dir, datetime_str, datetime_str+'.EFI.240')
            if not os.path.isfile(datafile1):
                st.markdown('数据文件不存在: '+ datafile1)
            else:
                shutil.copyfile(datafile1, datafile)

        # clear old file in the temporary directory
        now = time.time()
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            filestamp = os.stat(filepath).st_mtime
            filecompare = now - 7 * 86400
            if  filestamp < filecompare:
                os.remove(filepath)

        my_bar.progress(10)
        data_efi = read_ecmwf_ens_efi(
            datafile, short_name=variables[select_item],
            init_hour=init_hour, data_type='efi', number=0, cache_dir=temp_dir)
        my_bar.progress(30)
        data_sot = read_ecmwf_ens_efi(
            datafile, short_name=variables[select_item],
            init_hour=init_hour, data_type='sot', number=90, cache_dir=temp_dir)
        my_bar.progress(50)

        # draw EFI maps
        st.header('预报变量('+select_item+')')
        manager = Manager()
        return_dict = manager.dict()
        p = Process(target=draw_efi_maps, args=(data_efi, data_sot, init_time, select_item, map_region, return_dict))
        p.start()
        p.join()
        if return_dict[0] is not None:
            images_dict = return_dict[0]
        else:
            st.info('制作极端指数图失效!')
            images_dict = None
        return_dict.clear()
        manager.shutdown()
        p.close()
        del data_efi
        del data_sot

        my_bar.progress(90)
        if images_dict is not None:
            # display weather analysis maps
            st.markdown(
                    '''
                    ------
                    ### 点击图像弹出放大(标注为预报时效)''')
            images = np.asarray([*images_dict.values()], dtype=np.object)
            labels = np.asarray([*images_dict.keys()])
            html = ipyplot.display_image_gallery(images, labels, img_width=300)
            st.markdown(html, unsafe_allow_html=True)
        my_bar.progress(100)


def draw_efi_maps(data_efi, data_sot, init_time, select_item, map_region, return_dict):
    """
    Draw EFI maps
    """

    # image dictionary
    images = collections.OrderedDict()
    return_dict[0] = None

    # extract variable informations
    step_ranges = data_efi.coords['stepRange'].values
    varname = list(data_efi.data_vars.keys())[0]

    # loop every step range for plot
    for step_range in step_ranges:
        # extract data
        da_efi = data_efi[varname].sel(stepRange=step_range)
        da_sot = data_sot[varname].sel(stepRange=step_range)
        lon = da_efi.coords['longitude'].values
        lat = da_efi.coords['latitude'].values
        da_efi = da_efi.values
        da_sot = da_sot.values

        # construct title
        fhour_range = [int(i) for i in step_range.split('-')]
        title_kwargs = {
            'head': 'Extreme forecast index and Shift of Tails (black contours 0,1,2,4,8) for '+select_item,
            'time': init_time, 'fhour_range':fhour_range, 'fontsize':0.8}
        image = draw_efi(da_efi, lon, lat, sot90=da_sot, map_region=map_region, title_kwargs=title_kwargs)
        images[step_range] = image

    return_dict[0] = images

if __name__ == "__main__":
    main()
