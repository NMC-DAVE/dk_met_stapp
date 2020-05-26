
# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
检索特定日期和范围的CFSR再分析数据, 并绘制相关的天气图.
"""

import sys
import datetime
import xarray as xr
import streamlit as st

sys.path.append('.')
from nmc_met_graphics.util import  get_map_regions
from draw_maps import load_variables, draw_composite_map, draw_wind_upper_map


def  main():
    # application title
    st.title("历史天气图分析检索")
    st.header('——读取NCEP CFSR再分析资料并绘制天气图')

    # application information
    '''
    ------
    [CFSR](https://climatedataguide.ucar.edu/climate-data/climate-forecast-system-reanalysis-cfsr)(CLIMATE FORECAST SYSTEM REANALYSIS)
    再分析资料是NCEP提供的第三代再分析产品. 本程序从Albany大学Thredds服务器检索指定日期时刻及范围的CFSR数据, 并绘制多种环流天气图.
    '''
    st.sidebar.image('https://github.com/nmcdev/nmc_met_graphics/raw/master/nmc_met_graphics/resources/logo/nmc.png', width=100)

    # Input data date
    data_date = st.sidebar.date_input(
        "输入日期:", datetime.date(2016, 7, 19),
        min_value=datetime.date(1979, 1, 1),
        max_value=datetime.date.today() - datetime.timedelta(days=2))

    # Input data time
    data_time = st.sidebar.selectbox('选择时刻(UTC):', ('00', '06', '12', '18'))

    # construct datetime string
    datetime_str = data_date.strftime('%Y%m%d') + data_time
    date_obj = datetime.datetime.strptime(datetime_str,'%Y%m%d%H')

    # subset data
    map_regions = get_map_regions()
    select_items = list(map_regions.keys())
    select_items.append('自定义')
    select_item = st.sidebar.selectbox('选择空间范围', select_items)
    if select_item == '自定义':
        map_region_str = st.sidebar.text_input('输入空间范围[West, East, South, North]:', '70, 140, 10, 65')
        map_region = list(map(float, map_region_str.split(", ")))
    else:
        map_region = map_regions[select_item]

    # draw the figures
    if st.sidebar.button('绘制天气图'):
        # load data
        # @st.cache(hash_funcs={xr.core.dataset.Dataset: id}, allow_output_mutation=True, suppress_st_warning=True)
        def load_data(date_obj):
            data = load_variables(date_obj, map_region=map_region)
            return data
        u200, v200, gh200, u500, v500, gh500, u850, v850, t850, mslp, pwat = load_data(date_obj)
        
        # draw the synoptic compsite
        fig = draw_composite_map(date_obj, t850, u200, v200, u500, v500, mslp, gh500, u850, v850, pwat)
        st.pyplot(fig)

        # draw the 200hPa wind field
        image = draw_wind_upper_map(date_obj, u200, v200, gh200, map_region)
        st.image(image, use_column_width=True)
    else:
       st.info('请点击左侧**绘制天气图**按钮生成或更新图像.')

if __name__ == "__main__":
    main()
