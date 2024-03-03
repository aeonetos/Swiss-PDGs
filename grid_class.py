import folium
from streamlit_folium import st_folium, folium_static
import streamlit as st
import geopandas as gpd
import numpy as np
import pydeck as pdk
import os
import pandas as pd
from copy import deepcopy
import json
import ast
import shutil
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
from sklearn.neighbors import KernelDensity
from scipy.stats import gaussian_kde


def copy_files(source_folder, destination_folder, files_to_copy):
    # Ensure the destination folder exists; create it if not.
    os.makedirs(destination_folder, exist_ok=True)

    # Copy each file to the destination folder.
    for file_name in files_to_copy:
        source_path = os.path.join(source_folder, file_name)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy2(source_path, destination_path)


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
        path = None
        if self.grid_type == 'MV':
            path = self.grid_type + "/"
        else:
            # ----------------------- Process LV ----------------------
            # load the dictionary connecting the test ID and the folder name
            with open('data_processing/file_folder_lv.json') as json_file:
                dict_test_id_folder = json.load(json_file)
            # consider the path for LV single grid
            if isinstance(self.test_id, str):
                path = self.grid_type + "/" + dict_test_id_folder[self.test_id] + "/"

        if isinstance(self.test_id, str):
            file_n, file_e = self.test_id + "_nodes", self.test_id + "_edges"
            # check if the edge file exists, if yes, create the empty dataframes
            if not os.path.exists(path + file_e):
                edges_gdf = gpd.GeoDataFrame()
            else:
                edges_gdf = gpd.read_file(path + file_e)
            nodes_gdf = gpd.read_file(path + file_n)

        elif isinstance(self.test_id, list) and len(self.test_id) != 0:
            # consider the canton case or the multiple grids
            nodes_gdf = gpd.GeoDataFrame()
            edges_gdf = gpd.GeoDataFrame()
            for i in self.test_id:
                if self.grid_type == 'MV':
                    pass
                else:
                    path = self.grid_type + "/" + dict_test_id_folder[i] + "/"

                sub_nodes = gpd.read_file(path + i + "_nodes")
                # add a column to mark the substation
                sub_nodes['source_id'] = None
                index_substation = sub_nodes[sub_nodes['source']].index[0]
                sub_nodes.loc[index_substation, 'source_id'] = i

                # mark the grid
                sub_nodes['grid_id'] = str(i)
                nodes_gdf = pd.concat([nodes_gdf, sub_nodes])

                # check if the edge file exists
                if not os.path.exists(path + i + "_edges"):
                    sub_edges = gpd.GeoDataFrame()
                else:
                    sub_edges = gpd.read_file(path + i + "_edges")
                edges_gdf = pd.concat([edges_gdf, sub_edges])

        elif isinstance(self.test_id, list) and len(self.test_id) == 0:
            # st.write("💥Warning: you haven't entered a test case ID")
            nodes_gdf, edges_gdf = None, None
            st.stop()
        else:
            # st.write("There is no such grid within the canton")
            raise ValueError

        # rename the x and y columns
        nodes_gdf.rename(columns={'x': 'longitude', 'y': 'latitude'}, inplace=True)
        # convert the x y (epsg=2056) to lat long with geopandas
        nodes_gdf['geometry'] = nodes_gdf['geometry'].to_crs(epsg=4326)
        if edges_gdf.empty:
            pass
        else:
            edges_gdf['geometry'] = edges_gdf['geometry'].to_crs(epsg=4326)
        # get the lat long from the geometry
        nodes_gdf['latitude'] = nodes_gdf['geometry'].y
        nodes_gdf['longitude'] = nodes_gdf['geometry'].x
        return nodes_gdf, edges_gdf

    def get_routed_nodes_in_edges(self):
        """
        This function gets the nodes in the edges
        :return: list, the nodes in the edges
        """
        # first, check if the edges are empty
        if self.edges.empty:
            # in this case, return an empty list; use the nodes to calculate the initial view instead
            return []
        else:
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
        if not list_routed_nodes:
            # in this case, use the nodes to calculate the initial view instead
            max_lat_e, min_lat_e, max_lon_e, min_lon_e = max_lat_n, min_lat_n, max_lon_n, min_lon_n
        else:
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
        # record the substation's test ID

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
            polygon_plot = pd.read_csv('data_processing/canton_coordinates_plot.csv')
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

    def draw_layers_folium(self, substation_show=False, grid_show=False):
        """
        This function draws the layers with folium
        """
        self.nodes, self.edges = self.data_preprocessing_for_drawing()
        # specify the initial location
        m = folium.Map(location=self.get_initial_middle_point(), zoom_start=self.get_initial_zoom(), opacity=0.1)
        if substation_show:
            # mark the substation
            substation_nodes = self.nodes[self.nodes['source']]
            for k, s in substation_nodes.iterrows():
                folium.Marker(
                    location=[s['latitude'],
                              s['longitude']],
                    # popup=f"{s['source_id']}",
                    tooltip=f"{s['source_id']}",
                    icon=folium.Icon(color='green', icon='flash')
                ).add_to(m)
        if grid_show:
            # draw the nodes
            folium.GeoJson(
                self.nodes,
                name="Nodes",
                marker=folium.Circle(radius=40, fill_color="red", fill_opacity=0.4, weight=1),
                style_function=lambda x: {"radius": (x['properties']['size']),
                                          },
                zoom_on_click=True,
            ).add_to(m)
            # draw the edges
            # check if the edges are empty
            if not self.edges.empty:
                self.edges['geometry'] = self.edges['geometry'].to_crs(epsg=4326)
                raw_edges = [list(i.coords) for i in self.edges.geometry]
                raw_edges = [[[i[1], i[0]] for i in j] for j in raw_edges]

                folium.PolyLine(
                    locations=raw_edges,
                    color="green",
                    weight=2,
                    opacity=1,
                ).add_to(m)

        # # check where the last click was
        # st_data = st_folium(m, key='nodes_edges', width=1200, height=600)
        # lat, lon = None, None
        # if st_data['last_clicked']:
        #     # just show the lat/lon we clicked
        #     lat = st_data['last_clicked']['lat']
        #     lon = st_data['last_clicked']['lng']
        #     st.write('You clicked: ', lat, lon)
        # # determine which canton the point is in
        # point = gpd.points_from_xy([lon], [lat])

        # load the canton boundary
        canton_boundary = gpd.read_file('data_processing/canton_union.geojson')
        canton_boundary['geometry'] = canton_boundary['geometry'].to_crs(epsg=4326)
        # add the canton centroid
        canton_boundary['centroid'] = canton_boundary['geometry'].centroid

        # load the municipality boundary
        municipality_boundary = gpd.read_file('data_processing/municipality_boundary.geojson')
        municipality_boundary['geometry'] = municipality_boundary['geometry'].to_crs(epsg=4326)
        # add the municipality centroid
        municipality_boundary['centroid'] = municipality_boundary['geometry'].centroid

        # # determine which canton the point is in
        # canton = None
        # for k, c in enumerate(canton_boundary['NAME']):
        #     if point.within(canton_boundary[canton_boundary['NAME'] == c].geometry[k])[0]:
        #         canton = c
        #         st.write(f'You are in {c}')
        #         break

        # if canton is None:
        #     st.write('You are not in any canton')
        # else:
        #     st.write('The canton boundary is:')
        #     canton_geo = canton_boundary[canton_boundary['NAME'] == canton]['geometry']
        # canton_geo = gpd.GeoSeries(canton_geo).simplify(tolerance=0.001)
        # canton_geo = canton_geo.to_json()
        # folium.GeoJson(
        #     canton_geo,
        #     name="Canton",
        #     style_function=lambda x: {"fillColor": "grey"},
        #     zoom_on_click=True,
        #     tooltip=f"{canton}",
        #     marker=folium.Marker(icon=folium.DivIcon()),
        # ).add_to(m)
        # # add the
        # st_folium(m, key='canton', width=1200, height=600)

        # add 'selected_region' to the session state
        if 'selected_region' not in st.session_state:
            st.session_state['selected_region'] = None
        # update the selected canton with the last clicked object
        session_keys = list(st.session_state.keys())
        # remove the keys
        # # todo: to improve, now abandoned
        # object_name = [i for i in session_keys if
        #                i not in ['selected_region', 'MV_text_input_id', 'MV_input_canton_by_click',
        #                          'MV_text_input_canton', 'MV_test_id_checkbox', 'MV_show_canton_grids',
        #                          'MV_multiselect_grid_id', 'MV_checkbox_show_multi_grid']]
        # if len(object_name) != 0:  # means that the map is loaded for the first time
        #     last_clicked = st.session_state[object_name[0]]['last_object_clicked_tooltip']
        #     if last_clicked is not None:
        #         st.session_state['selected_region'] = last_clicked
        #         st.write('You clicked %s' % st.session_state['selected_region'])

        # add the feature group
        fg = folium.FeatureGroup(name="NAME")

        for n in canton_boundary['NAME']:
            fg.add_child(
                folium.Marker(
                    location=[canton_boundary[canton_boundary['NAME'] == n]['centroid'].y,
                              canton_boundary[canton_boundary['NAME'] == n]['centroid'].x],
                    # popup=f"{n}",
                    tooltip=f"{n}",
                )
            )
            if n == st.session_state["selected_region"] and self.grid_type == 'MV':
                fg.add_child(
                    folium.features.GeoJson(
                        canton_boundary[canton_boundary['NAME'] == n]['geometry']),
                )

        for n in municipality_boundary['NAME']:
            if n == st.session_state["selected_region"] and self.grid_type == 'LV':
                fg.add_child(
                    folium.features.GeoJson(
                        municipality_boundary[municipality_boundary['NAME'] == n]['geometry']),
                )
                fg.add_child(
                    folium.Marker(
                        location=[municipality_boundary[municipality_boundary['NAME'] == n]['centroid'].y,
                                  municipality_boundary[municipality_boundary['NAME'] == n]['centroid'].x],
                        # popup=f"{n}",
                        tooltip=f"{n}",
                    )
                )

        st_data = st_folium(
            m,
            feature_group_to_add=fg,
            width=1200,
            height=500,
        )

        return st_data['last_object_clicked_tooltip']

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

    def get_statistics_by_grid(self):
        """
        This function gets the statistics of the demand by grid
        :return:
        """
        # get the min, max, average and standard deviation of the demand, among which remove the non-demand nodes
        self.nodes['el_dmd'] = self.nodes['el_dmd'].replace(0, np.nan)
        # get the total demand and the number of demand nodes
        total_dmd = {}
        for i in self.test_id:
            total_dmd[i] = self.nodes[self.nodes['grid_id'] == i]['el_dmd'].sum()
        return total_dmd

    def show_statistics(self):
        """
        This function shows the statistics of the demand
        :return:
        """
        # get the statistics of the demand in the unit of MW
        min_dmd, max_dmd, avg_dmd, std_dmd, total_dmd, num_dmd = self.get_statistics()
        # show the statistics in a table
        if self.grid_type == 'MV':
            st.write("The statistics of the demand (MW)")
            df = {'min': [min_dmd], 'max': [max_dmd], 'average': [avg_dmd], 'standard deviation': [std_dmd],
                  'total': [total_dmd],
                  'number of loads': [num_dmd]}
        else:
            st.write("The statistics of the demand (kW)")
            df = {'min': [min_dmd * 1000], 'max': [max_dmd * 1000], 'average': [avg_dmd * 1000],
                  'standard deviation': [std_dmd * 1000],
                  'total': [total_dmd * 1000],
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

    def download(self):
        """
        This function downloads the data
        :return:
        """
        if self.grid_type == 'MV':
            copy_files(self.grid_type + '/', 'data_download/', [i + "_nodes" for i in self.test_id])
            # check if all the edge files exists
            for i in self.test_id:
                if not os.path.exists(self.grid_type + '/' + i + "_edges"):
                    pass
                else:
                    copy_files(self.grid_type + '/', 'data_download/', [i + "_edges"])
            # copy_files(self.grid_type + '/', 'data_download/', [i + "_edges" for i in self.test_id])
        else:
            with open('data_processing/file_folder_lv.json') as json_file:
                dict_test_id_folder = json.load(json_file)
            for i in self.test_id:
                copy_files(self.grid_type + '/' + dict_test_id_folder[i] + '/', 'data_download/', [i + "_nodes"])
                if not os.path.exists(self.grid_type + '/' + dict_test_id_folder[i] + '/' + i + "_edges"):
                    pass
                else:
                    copy_files(self.grid_type + '/' + dict_test_id_folder[i] + '/', 'data_download/', [i + "_edges"])
        # convert the files to zip
        shutil.make_archive('data_download', 'zip', 'data_download')
        shutil.rmtree('data_download')
        # download the zip file
        with open('data_download.zip', 'rb') as f:
            file_download = f.read()
            st.download_button(label='Download the data', data=file_download, file_name='data_download.zip',
                               mime='application/zip', key=None)
        # remove the zip file
        os.remove('data_download.zip')

    def show_histogram(self):
        """
        This function shows the histogram of the power demands in certain region
        :return:
        """
        # get the dictionary of the demand by grid
        total_dmd = self.get_statistics_by_grid()
        # show the histogram of the demand
        demand_arr = np.array([t for t in total_dmd.values()])
        fig, ax_his = plt.subplots()
        n, bins, patches = ax_his.hist(demand_arr)
        # modify the axis
        ax_his.set_xlabel('Total active power demand (kW)')
        ax_his.set_ylabel('Number of grids')
        ax_his.yaxis.get_major_locator().set_params(integer=True)

        # show the density with the shared x axis
        ax_density = ax_his.twinx()
        xs = np.linspace(demand_arr.min(), demand_arr.max(), 1000)

        kde = KernelDensity(bandwidth=1.0, kernel='gaussian', )
        kde.fit(demand_arr[:, None])
        logprob = kde.score_samples(xs[:, None])
        ax_density.plot(xs, np.exp(logprob), color='orange')

        # kde = gaussian_kde(demand_arr, bw_method='silverman')
        # ax_density.plot(xs, kde(xs), color='orange')

        st.pyplot(fig)











