"""
Generate necessary data for visualization
date: 05/12/2023
"""

import os
import json
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import union_all


def get_all_test_id(grid_type, save=False):
    """
    This function gets all the test IDs
    :return: list, all the test IDs
    """
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

    # save the list
    if save:
        with open('data_processing/list_test_id_' + grid_type + '.json', 'w') as fp:
            json.dump(list_ids, fp)
        print('Successfully saved all the test IDs')

    return list_ids


def classify_grids(region_geo, grid_type):
    """
    This function classifies the grids into different cantons
    """
    # for LV network, create a dictionary to store the test ID and the folder name
    if grid_type == 'LV':
        path_base = "LV/"
        list_folders = os.listdir(path_base)
        dict_test_id_folder = {}
        for j in range(len(list_folders)):
            path = path_base + list_folders[j] + "/"
            sub_files = os.listdir(path)
            # create a dictionary, the key is the test ID, the value is the folder name
            sub_dict = {i[:-6]: list_folders[j] for i in sub_files}
            dict_test_id_folder.update(sub_dict)
    else:
        dict_test_id_folder = None

    # get all the test IDs
    test_id_lists = get_all_test_id(grid_type)

    # record the number of nodes in each canton
    print(f'total number of grids: {len(test_id_lists)}')
    iteration = 0

    # # method 1: pointwise check
    # # create a dataframe to store the canton name and the test IDs in the canton
    # df_record = pd.DataFrame(np.zeros((len(test_id_lists), len(cantons['NAME']))), columns=list(cantons['NAME']))
    # df_record.index = test_id_lists
    # for i in test_id_lists:
    #     iteration += 1
    #     print(f'iteration: {iteration}, Processing: {i}')
    #     # read the nodes
    #     if grid_type == 'MV':
    #         path = grid_type + "/"
    #     else:
    #         path = grid_type + "/" + dict_test_id_folder[i] + "/"
    #     file_name = i + '_nodes'
    #     nodes_gpd = gpd.read_file(path + file_name)
    #     # check if the nodes are in the canton
    #     for k, c in enumerate(cantons['NAME']):
    #         nodes_gpd['in_region'] = nodes_gpd['geometry'].within(cantons[cantons['NAME'] == c].geometry[k])
    #         df_record.loc[i, c] = nodes_gpd['in_region'].sum()

    # # for each grid, find the canton with the largest number of nodes
    # grid_canton_belongs = df_record.idxmax(axis=1)
    #
    # # return the index name of each canton, store it in a dictionary
    # dict_canton_grid = {}
    # for i in cantons['NAME']:
    #     dict_canton_grid[i] = list(grid_canton_belongs[grid_canton_belongs == i].index)

    # method 2: check by the transformer of each grid
    # create a new dataframe to store the transformer information
    df_transformer = pd.DataFrame(columns=['grid_id', 'transformer'])

    for i in test_id_lists:
        iteration += 1
        print(f'iteration: {iteration}, Processing: {i}')
        # read the nodes
        if grid_type == 'MV':
            path = grid_type + "/"
        else:
            path = grid_type + "/" + dict_test_id_folder[i] + "/"
        file_name = i + '_nodes'
        nodes_gpd = gpd.read_file(path + file_name)
        # locate the transformer
        if 'source' in nodes_gpd.columns:
            transformer_geo = nodes_gpd[nodes_gpd['source']].geometry
            df_transformer = pd.concat([df_transformer, pd.DataFrame({'grid_id': i, 'transformer': transformer_geo})])
        else:
            # todo: remove 261-990, 2831-15
            pass

    # check which canton the transformer lies
    for k, c in enumerate(region_geo['NAME']):
        df_transformer['in_region'] = df_transformer['transformer'].values.within(region_geo[region_geo['NAME'] == c].geometry[k])
        # if the in_region is true, then the transformer belongs to the canton
        df_transformer.loc[df_transformer['in_region'], 'region_name'] = c
    # delete the in_region column
    df_transformer.drop(columns=['in_region'], inplace=True)

    # return the index name of each canton, store it in a dictionary
    dict_canton_grid = {}
    for i in region_geo['NAME']:
        dict_canton_grid[i] = list(df_transformer[df_transformer['region_name'] == i].grid_id.values)

    # save the dictionary
    if grid_type == 'MV':
        df_transformer[['grid_id', 'region_name']].to_csv('data_processing/table_grid_canton_' + grid_type + '.csv', index=False)

        with open('data_processing/dict_canton_grid_' + grid_type + '.json', 'w') as fp:
            json.dump(dict_canton_grid, fp)
        print(f'Successfully saved the relationship between cantons and grids for {grid_type}')

    if grid_type == 'LV':
        df_transformer[['grid_id', 'region_name']].to_csv('data_processing/table_grid_municipality_' + grid_type + '.csv', index=False)
        with open('data_processing/file_folder_lv.json', 'w') as fp:
            json.dump(dict_test_id_folder, fp)
        print(f'Successfully saved the relationship between test ID and folder name for {grid_type}')
        with open('data_processing/dict_municipality_grid_' + grid_type + '.json', 'w') as fp:
            json.dump(dict_canton_grid, fp)
    return


def convert_multipolygon(multipolygon):
    multipolygon_convex = multipolygon.convex_hull
    holes = multipolygon_convex.difference(multipolygon)

    return multipolygon_convex, holes


def connect_mv_lv():
    """
    This function outputs the connection between the MV and LV grids
    :return:
    """
    # search all mv grids, and find all the connections to the lv grid
    mv_files = os.listdir('MV/')
    mv_ids = [i[:-6] for i in mv_files]
    # create a dictionary to store the mv-lv connection
    dict_mv_lv = {}
    for m in mv_ids:
        print(f'Processing: {m}')
        # read the nodes
        nodes_gpd = gpd.read_file('MV/' + m + '_nodes')
        # select the nodes that are connected to the lv grid
        connected_lv_grid = nodes_gpd[nodes_gpd['lv_grid'] != "-1"]['lv_grid'].values
        # save the mv-lv connection as dictionary
        dict_mv_lv[m] = list(connected_lv_grid)
    # transform it into lv as the key
    dict_lv_mv = {}
    for k, v in dict_mv_lv.items():
        for i in v:
            if i in dict_lv_mv:
                dict_lv_mv[i].append(k)
            else:
                dict_lv_mv[i] = k
    # save the dictionary
    with open('data_processing/dict_mv_lv.json', 'w') as fp:
        json.dump(dict_mv_lv, fp)
    with open('data_processing/dict_lv_mv.json', 'w') as fp:
        json.dump(dict_lv_mv, fp)


if __name__ == '__main__':
    # # get all the test IDs for MV and LV
    # mv_test_list, lv_test_list = get_all_test_id('MV', save=True), get_all_test_id('LV', save=True)
    #
    # # read the canton boundary
    # canton_gpd = gpd.read_file('cantons.geojson')
    # # get all the canton names
    # list_canton_names = list(canton_gpd['NAME'].drop_duplicates())
    # list_canton_names.sort()
    # # create a new dataframe keeping the canton name and the geometry
    # canton_geo = pd.DataFrame(columns=['NAME', 'geometry'])
    # canton_geo['NAME'] = list_canton_names
    # # get the union canton boundary
    # for i in list_canton_names:
    #     print(f'Processing: {i}')
    #     canton_geo.loc[canton_geo['NAME'] == i, 'geometry'] = union_all(canton_gpd[canton_gpd['NAME'] == i].geometry)
    # # see if the regions are overlapping
    # for k, i in enumerate(list_canton_names):
    #     for s, j in enumerate(list_canton_names):
    #         if i != j:
    #             overlap_binary = canton_geo[canton_geo["NAME"] == i].geometry[k].overlaps(canton_geo[canton_geo["NAME"] == j].geometry[s])
    #             # print(f'canton {i} and canton {j} overlapping: {overlap_binary}')
    #             if overlap_binary:
    #                 raise ValueError(f'canton {i} and canton {j} are overlapping')
    # print('There is no overlapping between cantons')
    # # save the union canton boundary
    # canton_geo = gpd.GeoDataFrame(canton_geo, geometry='geometry')
    # canton_geo.crs = 'EPSG:2056'
    # canton_geo.to_file('data_processing/canton_union.geojson', driver='GeoJSON')
    #
    # canton_boundary = gpd.read_file('data_processing/canton_union.geojson')
    #
    # # project the canton boundary to lat long
    # canton_boundary['geometry'] = canton_boundary['geometry'].to_crs(epsg=4326)
    #
    # # convert the polygon to x, y
    # canton_boundary['coordinates'] = 1  # set dummy value
    # canton_boundary['coordinates'] = canton_boundary['coordinates'].astype(object)
    # for i in range(len(canton_boundary)):
    #     if canton_boundary['geometry'][i].geom_type == 'Polygon':
    #         x, y = canton_boundary['geometry'][i].exterior.coords.xy
    #         canton_boundary['coordinates'][i] = [[[x[j], y[j]] for j in range(len(x))]]
    #     else:  # MultiPolygon
    #         convex, holes = convert_multipolygon(canton_boundary['geometry'][i])
    #         x, y = convex.exterior.coords.xy
    #         multi_coordinates = [[[x[j], y[j]] for j in range(len(x))]]
    #         for j in list(holes.geoms):
    #             m, n = j.exterior.coords.xy
    #             multi_coordinates.append([[m[l], n[l]] for l in range(len(m))])
    #         canton_boundary['coordinates'][i] = multi_coordinates
    #
    # # calculate the centroid of each canton
    # canton_boundary['centroid'] = canton_boundary['geometry'].centroid
    # canton_boundary['centroid_x'] = canton_boundary['centroid'].x
    # canton_boundary['centroid_y'] = canton_boundary['centroid'].y
    # canton_boundary.drop(columns=['centroid'], inplace=True)
    # canton_boundary.to_csv('data_processing/canton_coordinates_plot.csv', index=False)
    #
    # # classify the MV grids into different cantons
    # classify_grids(canton_geo, 'MV')
    #
    # # classify the LV grids into different municipalities
    # municipality_gpd = gpd.read_file('nine_zones.geojson')
    # # create a new dataframe keeping the canton name and the geometry
    # municipality_geo = municipality_gpd[['NAME', 'KANTON', 'geometry']]
    # municipality_geo = gpd.GeoDataFrame(municipality_geo, geometry='geometry')
    # municipality_geo.crs = 'EPSG:2056'
    # municipality_geo.to_file('data_processing/municipality_boundary.geojson', driver='GeoJSON')
    # classify_grids(municipality_geo, 'LV')
    connect_mv_lv()


