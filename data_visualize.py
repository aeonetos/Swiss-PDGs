import streamlit as st
import geopandas as gpd
import numpy as np
import pydeck as pdk
import os
import pandas as pd
from copy import deepcopy
import json
import math
import random
import ast


def get_all_test_id(grid_type):
    """
    This function gets all the test IDs
    :return: list, all the test IDs
    """
    # todo: first click, store it in a dictionary, then read from the dictionary
    if grid_type == 'MV':
        path_base = grid_type + "/"
        # get all the files in the path
        list_files = os.listdir(path_base)

    else:
        path_base = grid_type + "/"
        list_files = []
        list_folders = os.listdir(path_base)
        for j in range(len(list_folders)):
            path = path_base + list_folders[j] + "/"
            sub_files = os.listdir(path)
            list_files += sub_files

    # get all the possible test IDs, that is remove the "_nodes" and "_edges" from the file names
    list_ids = [i[:-6] for i in list_files]
    # remove the duplicates
    list_ids = list(set(list_ids))
    # sort the list
    list_ids.sort()
    return list_ids


# create a class containing the functions to visualize the data
def show_all_possible_test_ids(id_list):
    """
    This function shows all the possible test IDs
    :param id_list: list, all the possible test IDs
    :return:
    """
    # write them into a table of 5 columns
    if len(id_list) % 5 != 0:
        # add some empty elements to make the length of the list a multiple of 10
        id_list = id_list + [''] * (5 - len(id_list) % 5)
    df = pd.DataFrame(np.array(id_list).reshape(-1, 5))
    st.dataframe(df)


class GridVisualize:
    def __init__(self, grid_type, test_id):
        self.grid_type = grid_type
        self.test_id = test_id
        self.nodes, self.edges = self.select_test_id()

    def select_test_id(self):
        """
        This function creates a box to type in the ID of the test case
        :return: selected nodes and edges
        """
        if self.grid_type == 'MV':
            path = self.grid_type + "/"
        else:
            path = self.grid_type + "/" + dict_test_id_folder[self.test_id] + "/"

        if isinstance(self.test_id, str):
            file_n, file_e = self.test_id + "_nodes", self.test_id + "_edges"
            nodes_gdf, edges_gdf = gpd.read_file(path + file_n), gpd.read_file(path + file_e)
        elif isinstance(self.test_id, list) & (len(self.test_id) != 0):
            # consider the canton case
            nodes_gdf = gpd.GeoDataFrame()
            edges_gdf = gpd.GeoDataFrame()
            for i in self.test_id:
                sub_nodes = gpd.read_file(path + i + "_nodes")
                sub_edges = gpd.read_file(path + i + "_edges")
                nodes_gdf = pd.concat([nodes_gdf, sub_nodes])
                edges_gdf = pd.concat([edges_gdf, sub_edges])
        else:
            st.write("There is no such grid within the canton")
            raise ValueError

        # rename the x and y columns
        nodes_gdf.rename(columns={'x': 'longitude', 'y': 'latitude'}, inplace=True)
        # convert the x y (epsg=2056) to lat long with geopandas
        edges_gdf['geometry'] = edges_gdf['geometry'].to_crs(epsg=4326)
        nodes_gdf['geometry'] = nodes_gdf['geometry'].to_crs(epsg=4326)
        # get the lat long from the geometry
        nodes_gdf['latitude'] = nodes_gdf['geometry'].y
        nodes_gdf['longitude'] = nodes_gdf['geometry'].x
        return nodes_gdf, edges_gdf

    def get_routed_nodes_in_edges(self):
        """
        This function gets the nodes in the edges
        :return: list, the nodes in the edges
        """
        list_path = [list(i.coords) for i in self.edges.geometry]
        list_routed_nodes = [item for sublist in list_path for item in sublist]
        return list_routed_nodes

    def get_initial_middle_point(self):
        """
        This function gets the initial middle point of the network
        :return: tuple, (lat, long), the initial middle point of the network
        """
        # find the max and min of the lat and long in the nodes
        max_lat_n, min_lat_n = self.nodes['latitude'].max(), self.nodes['latitude'].min()
        max_lon_n, min_lon_n = self.nodes['longitude'].max(), self.nodes['longitude'].min()
        # find the max and min of the lat and long in the edges
        list_routed_nodes = self.get_routed_nodes_in_edges()
        max_lat_e, min_lat_e = max([i[1] for i in list_routed_nodes]), min([i[1] for i in list_routed_nodes])
        max_lon_e, min_lon_e = max([i[0] for i in list_routed_nodes]), min([i[0] for i in list_routed_nodes])
        # get the midpoint
        max_lat, min_lat = max(max_lat_n, max_lat_e), min(min_lat_n, min_lat_e)
        max_lon, min_lon = max(max_lon_n, max_lon_e), min(min_lon_n, min_lon_e)
        midpoint = (np.average([max_lat, min_lat]), np.average([max_lon, min_lon]))
        return midpoint

    def get_initial_zoom(self):
        # find nodes in the edges
        list_routed_nodes = self.get_routed_nodes_in_edges()
        # add the nodes in the edges to the nodes dataframe
        nodes_in_edges = pd.DataFrame(list_routed_nodes, columns=['longitude', 'latitude'])
        nodes_all = pd.concat([self.nodes[['longitude', 'latitude']], nodes_in_edges])
        cv = pdk.data_utils.compute_view(points=nodes_all)
        initial_zoom = cv.zoom
        return initial_zoom

    def data_preprocessing_for_drawing(self):
        """
        This function preprocesses the data, including adding the size of the nodes, the color of the nodes, and mark
        the substation
        :return: the preprocessed nodes and edges
        """
        # data preprocessing
        if self.grid_type == 'MV':
            size_scale = 50  # todo: automatically adjust the size scale
        else:
            size_scale = 500
        self.nodes['size'] = self.nodes['el_dmd'] * size_scale
        self.nodes['r'], self.nodes['g'], self.nodes['b'] = 255, 0, 0
        # mark the substation
        osmid_sub = self.nodes[self.nodes['source']].index[0]
        self.nodes.loc[osmid_sub, 'size'] = self.nodes['size'].max() * 1.1
        self.nodes.loc[osmid_sub, 'r'] = 105
        self.nodes.loc[osmid_sub, 'g'] = 204
        self.nodes.loc[osmid_sub, 'b'] = 164
        return self.nodes, self.edges

    def draw_layers(self, pitch=None):
        """
        This function draws the layers, including ScatterplotLayer and PathLayer
        :return:
        """
        # data preprocessing
        self.nodes, self.edges = self.data_preprocessing_for_drawing()
        # get the map style
        mapstyle = st.sidebar.selectbox(
            "Choose Map Style for %s:" % self.grid_type,
            options=["road", "satellite"],
            format_func=str.capitalize,
            key=self.grid_type,
        )
        available_map_styles = {'road': pdk.map_styles.ROAD, 'satellite': 'mapbox://styles/mapbox/satellite-v9'}
        # add a layer to show the edges and nodes
        pathlayer = pdk.Layer(
                    "PathLayer",
                    data=[list(i.coords) for i in self.edges.geometry],
                    get_filled_color=[0, 255, 0],
                    pickable=True,
                    width_min_pixels=2,
                    get_width=0.1,
                    get_path='-'

                )
        scatterplotlayer = pdk.Layer(
                    "ScatterplotLayer",
                    data=self.nodes,
                    pickable=True,
                    opacity=0.8,
                    stroked=True,
                    filled=True,
                    radius_scale=10,
                    radius_min_pixels=1,
                    radius_max_pixels=20,
                    line_width_min_pixels=0.2,
                    get_position=['longitude', 'latitude'],
                    get_radius="size",
                    get_fill_color=['r', 'g', 'b'],
                    get_line_color=[0, 0, 0],
                )
        if self.grid_type == 'MV':
            polygon_plot = pd.read_csv('../data_processing/canton_coordinates_plot.csv')
            polygon_plot['coordinates'] = polygon_plot['coordinates'].apply(ast.literal_eval)
        else:
            # todo
            polygon_plot = pd.read_csv('data_processing/canton_coordinates_plot_LV.csv')
            polygon_plot['coordinates'] = polygon_plot['coordinates'].apply(ast.literal_eval)
        polygonlayer = pdk.Layer(
                    "PolygonLayer",
                    polygon_plot,
                    # id="geojson",
                    # opacity=0.8,
                    # stroked=False,
                    get_polygon="coordinates",
                    # filled=True,
                    # extruded=True,
                    # wireframe=True,
                    get_fill_color="fill_color",
                    # get_line_color=[255, 255, 255],
                    auto_highlight=True,
                    pickable=True,
                )
        textlayer = pdk.Layer(
                    "TextLayer",
                    data=polygon_plot,
                    get_position=['centroid_x', 'centroid_y'],
                    get_text="NAME",
                    # get_color=[255, 255, 255],
                    get_angle=0,
                    get_size=16,
                    get_alignment_baseline="'center'",
                )
        pydeck_layers = pdk.Deck(
            map_style=f"{available_map_styles[mapstyle]}",
            initial_view_state={
                "latitude": self.get_initial_middle_point()[0],
                "longitude": self.get_initial_middle_point()[1],
                "zoom": self.get_initial_zoom(),
                "pitch": pitch,
            },
            layers=[
                pathlayer,
                scatterplotlayer,
                polygonlayer,
                textlayer,
            ]
        )
        st.write(pydeck_layers)
        # add a button to make the map back to the initial view
        if st.button('Reset the map for %s' % self.grid_type):
            pydeck_layers.update()
        return pydeck_layers

    def get_statistics(self):
        """
        This function gets the statistics of the demand
        :return:
        """
        # get the min, max, average and standard deviation of the demand, among which remove the non-demand nodes
        self.nodes['el_dmd'] = self.nodes['el_dmd'].replace(0, np.nan)
        min_dmd, max_dmd, avg_dmd, std_dmd = self.nodes['el_dmd'].min(), self.nodes['el_dmd'].max(), \
                                             self.nodes['el_dmd'].mean(), self.nodes['el_dmd'].std()
        # get the total demand and the number of demand nodes
        total_dmd, num_dmd = self.nodes['el_dmd'].sum(), self.nodes['el_dmd'].count()
        return min_dmd, max_dmd, avg_dmd, std_dmd, total_dmd, num_dmd

    def show_statistics(self):
        """
        This function shows the statistics of the demand
        :return:
        """
        # get the statistics of the demand in the unit of MW
        min_dmd, max_dmd, avg_dmd, std_dmd, total_dmd, num_dmd = self.get_statistics()
        # show the statistics in a table
        if self.grid_type=='MV':
            st.write("The statistics of the demand (MW)")
            df = {'min': [min_dmd], 'max': [max_dmd], 'average': [avg_dmd], 'standard deviation': [std_dmd],
                  'total': [total_dmd],
                  'number of loads': [num_dmd]}
        else:
            st.write("The statistics of the demand (kW)")
            df = {'min': [min_dmd*1000], 'max': [max_dmd*1000], 'average': [avg_dmd*1000],
                  'standard deviation': [std_dmd*1000],
                  'total': [total_dmd*1000],
                  'number of loads': [num_dmd]}
        df = pd.DataFrame(df)
        st.write(df)
        return

    def show_raw_data(self):
        """
        This function shows the raw data of the network
        :return:
        """
        # data preprocessing, transform the geometry to wkt
        # for nodes
        show_nodes = deepcopy(self.nodes)
        show_nodes['geo'] = show_nodes.geometry.to_wkt()
        # replace the geometry with the wkt
        show_nodes.drop(columns=['geometry'], inplace=True)
        show_nodes.rename(columns={'geo': 'geometry'}, inplace=True)
        # for edges
        show_edges = deepcopy(self.edges)
        show_edges['geo'] = show_edges.geometry.to_wkt()
        # replace the geometry with the wkt
        show_edges.drop(columns=['geometry'], inplace=True)
        show_edges.rename(columns={'geo': 'geometry'}, inplace=True)

        # show the raw data
        if st.checkbox('Show raw data of %s' % self.grid_type):
            st.subheader('Nodes')
            st.dataframe(pd.DataFrame(show_nodes))
            st.subheader('Edges')
            st.dataframe(pd.DataFrame(show_edges))
        return


if __name__ == '__main__':
    data_path = '../data_processing/'
    # ----------------------- Process LV ----------------------
    # load the dictionary connecting the test ID and the folder name
    with open(data_path + 'file_folder_lv.json') as json_file:
        dict_test_id_folder = json.load(json_file)

    # ----------------------- Process cantons ----------------------
    # load the dictionary connecting the canton and the grid
    with open(data_path + 'dict_canton_grid_MV.json') as json_file:
        dict_canton_grid_mv = json.load(json_file)
    with open(data_path + 'dict_canton_grid_LV.json') as json_file:
        dict_canton_grid_lv = json.load(json_file)
    list_canton_names = list(dict_canton_grid_mv.keys())

    # --------------------------- MV network ---------------------------
    # set the title of the page
    st.title("The MV network")
    # get all the test IDs
    with open(data_path + 'list_test_id_MV.json') as json_file:
        list_ids_mv = json.load(json_file)
    # get the ids and the corresponding canton names
    table_ids_canton = pd.read_csv(data_path + 'table_grid_canton_MV.csv')
    # create a text field to type in the ID of the test case
    st.subheader("Please choose the test case")
    # create a text field to type in canton name in the same line
    cols = st.columns(2)
    with cols[0]:
        test_id = st.text_input('test case ID', list_ids_mv[0], key='MV_text_input_id')
    with cols[1]:
        test_canton = st.selectbox('canton name', list_canton_names, key='MV_text_input_canton')
    # create a checkbox that can be clicked to show all possible test IDs
    if st.checkbox('Show all possible test IDs', key='MV_checkbox'):
        # show_all_possible_test_ids(list_ids_mv)
        st.dataframe(table_ids_canton)

    # add a single checkbox to choose the test case
    genre = st.radio(
        "Which one do you want to show?",
        ["***Single grid***", "***Canton region***"],
        captions=["show selected test id.", "show the whole canton region"])

    # check if the test case ID is valid
    if test_id not in list_ids_mv:
        st.write("Please enter a valid test case ID")
        st.stop()

    if genre == "***Single grid***":
        test_case = test_id
    else:
        # get the test IDs in the canton
        test_case = dict_canton_grid_mv[test_canton]

    # create an object of the class
    mv = GridVisualize('MV', test_case)
    # draw the layers
    mv_layers = mv.draw_layers()
    # add some legend for substation and demand nodes, including a logo with the color
    st.write("🟢Substation  🔴Demand node")
    # show the statistics in a table
    mv.show_statistics()
    # add a checkbox that can be clicked to show the raw data
    mv.show_raw_data()

    # --------------------------- LV network ---------------------------
    # set the title of the page
    st.title("The LV network")
    # get all the test IDs
    with open(data_path + 'list_test_id_LV.json') as json_file:
        list_ids_lv = json.load(json_file)
    # create a box to type in the ID of the test case
    st.subheader("Please enter the ID of the test case")
    test_case_lv = st.text_input("test case ID", list_ids_lv[0], key='LV_text_input')
    # check if the test case ID is valid
    if test_case_lv not in list_ids_lv:
        st.write("Please enter a valid test case ID")
        st.stop()

    # create a checkbox that can be clicked to show all possible test IDs
    if st.checkbox('Show all possible test IDs', key='LV_checkbox'):
        show_all_possible_test_ids(list_ids_lv)

    # create an object of the class
    lv = GridVisualize('LV', test_case_lv)
    # draw the layers
    lv_layers = lv.draw_layers()
    # add some legend for substation and demand nodes, including a logo with the color
    st.write("🟢Substation  🔴Demand node")
    # show the statistics in a table
    lv.show_statistics()
    # add a checkbox that can be clicked to show the raw data
    # lv.show_raw_data()
    lv.show_raw_data()

    # --------------------------- Canton ---------------------------

    st.title("The canton")
    # # load the canton boundary
    # canton_boundary = gpd.read_file('data_processing/canton_union.geojson')
    # # project the canton boundary to lat long
    # canton_boundary['geometry'] = canton_boundary['geometry'].to_crs(epsg=4326)
    # # convert the polygon to x, y
    # canton_boundary['coordinates'] = 1  # set dummy value
    # canton_boundary['coordinates'] = canton_boundary['coordinates'].astype(object)
    # for i in range(len(canton_boundary)):
    #     if canton_boundary['geometry'][i].geom_type == 'Polygon':
    #         x, y = canton_boundary['geometry'][i].exterior.coords.xy
    #         canton_boundary['coordinates'][i] = [[[x[j], y[j]] for j in range(len(x))]]
    #     else:  # MultiPolygon
    #         multi_coordinates = []
    #         for k, j in enumerate(list(canton_boundary['geometry'][i].geoms)):
    #             m, n = j.exterior.coords.xy
    #             multi_coordinates.append([[m[l], n[l]] for l in range(len(m))])
    #         canton_boundary['coordinates'][i] = multi_coordinates
    #
    # # get the canton name
    # list_canton_names = list(canton_boundary['NAME'])
    # # assign different colors to different cantons
    # canton_colors = {
    #     'Aargau': [0, 0, 255],
    #     'Appenzell Ausserrhoden': [0, 255, 0],
    #     'Appenzell Innerrhoden': [255, 0, 0],
    #     'Basel-Landschaft': [255, 255, 0],
    #     'Basel-Stadt': [255, 0, 255],
    #     'Bern': [0, 255, 255],
    #     'Fribourg': [255, 128, 0],
    #     'Genève': [0, 128, 255],
    #     'Glarus': [128, 0, 255],
    #     'Graubünden': [0, 255, 128],
    #     'Jura': [128, 255, 0],
    #     'Luzern': [255, 0, 128],
    #     'Neuchâtel': [0, 255, 128],
    #     'Nidwalden': [128, 0, 255],
    #     'Obwalden': [0, 128, 255],
    #     'Schaffhausen': [128, 255, 0],
    #     'Schwyz': [255, 0, 128],
    #     'Solothurn': [0, 255, 128],
    #     'St. Gallen': [128, 0, 255],
    #     'Thurgau': [0, 128, 255], # not shown
    #     'Ticino': [128, 255, 0],
    #     'Uri': [255, 0, 128],
    #     'Valais': [0, 255, 128],
    #     'Vaud': [128, 0, 255],
    #     'Zug': [0, 128, 255],
    #     'Zürich': [128, 255, 0],
    # }
    # canton_boundary['fill_color'] = canton_boundary['NAME'].apply(lambda x: canton_colors[x])
    # # create a polygon layer
    # canton_boundary.to_csv('data_processing/canton_coordinates_plot.csv', index=False)
    data_plot = pd.read_csv('../data_processing/canton_coordinates_plot.csv')
    data_plot['coordinates'] = data_plot['coordinates'].apply(ast.literal_eval)
    # data_plot.iloc[0, 'coordinates'] = data_plot[data_plot['NAME'] == 'Aargau']['coordinates'][0][1]

    polygon_layer = pdk.Layer(
        "PolygonLayer",
        # a[a['NAME'] == 'Jura'],
        data_plot,
        # id="geojson",
        # opacity=0.8,
        # stroked=True,
        get_polygon="coordinates",
        # filled=True,
        # extruded=True,
        # wireframe=True,
        get_fill_color='fill_color',
        # get_line_color=[255, 255, 255],
        auto_highlight=True,
        pickable=True,
        pickable_color=[255, 255, 255],
    )
    st.write(pdk.Deck(
        polygon_layer,
        initial_view_state=pdk.ViewState(
            latitude=46.8,
            longitude=8.3,
            zoom=7,
            maxZoom=16,
        ),
        map_style=pdk.map_styles.DARK,
    ))

