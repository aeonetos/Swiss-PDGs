from grid_class import *

def lv_page():

    data_path = 'data_processing/'

    # ----------------------- Process municipality ----------------------
    # load the dictionary connecting the municipality and the grid
    with open(data_path + 'dict_municipality_grid_LV.json') as json_file:
        dict_municipality_grid_lv = json.load(json_file)
    list_municipality_names = list(dict_municipality_grid_lv.keys())
    list_lv_ids = [i for j in dict_municipality_grid_lv.values() for i in j]
    # sort the list
    list_municipality_names.sort()
    list_lv_ids.sort()

    # load the table connecting the test IDs and the canton name
    table_ids_municipality = pd.read_csv(data_path + 'table_grid_municipality_LV.csv')

    # --------------------------- LV network ---------------------------
    # set the title of the page
    st.title("The LV network")
    # add a single checkbox to choose the test case
    genre = st.radio(
        "Which one do you want to show?",
        ["***Select grids by IDs***", "***Select grids by municipality***"],
        captions=["show selected test ids", "show the whole municipality region"],
        horizontal=True)
    
    # add a divider
    st.markdown("---")

    # --------------------------- municipality region --------------------------
    if genre == "***Select grids by municipality***":
        lv = None
        with st.form(key='LV_form_municipality'):
            cols = st.columns(2)
            with cols[0]:
                test_municipality = st.selectbox('municipality name', list_municipality_names, index=None, placeholder='Please select',
                                           key='LV_text_input_municipality')
                # update the session state
                st.session_state['selected_region'] = test_municipality
                mapstyle = st.selectbox('Map style',['road','satellite'],placeholder='Please select',key='LV_map_style')
            with cols[1]:
                show = st.checkbox('Show the map', key='LV_show_municipality')
                with st.expander("Show substation (grid name)", expanded=False):
                    table_to_show = table_ids_municipality[table_ids_municipality['region_name'] == test_municipality]
                    with open(data_path + 'dict_lv_mv.json') as json_file:
                        dict_lv_mv = json.load(json_file)
                    table_to_show['mv_supplier'] = table_to_show['grid_id'].map(dict_lv_mv)
                    st.dataframe(table_to_show)
                    mv_supplier_list = list(table_to_show['mv_supplier'].unique())
                    # remove the nan value
                    mv_supplier_list = [x for x in mv_supplier_list if str(x) != 'nan']
                    st.write("This region is supplied by the following MV suppliers: ")
                    st.write(*mv_supplier_list, sep=",")
                
            # create a submit button to show the map
            lv=None
            st.form_submit_button('Submit')
            if test_municipality is not None:
                lv = GridVisualize('LV', dict_municipality_grid_lv[test_municipality], mapstyle=mapstyle)

        if lv:
            with st.expander("Download data", expanded=False):
                col_download = st.columns(3)
                with col_download[0]:
                    st.write("Press this button to download geojson file:")
                    lv.download_geo()
                with col_download[1]:
                    st.write("Press this button to download pandapower file:")
                    lv.download_pandapower()
                with col_download[2]:
                    st.write("Press this button to download matpower file:")
                    lv.download_matpower()
            # show the statistics of the selected region
            if show:
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                #lv.draw_layers_folium(substation_show=substation_option, grid_show=grid_option)
                lv.draw_layers()
                placeholder.empty()
            with st.expander("Loads Statistic Data", expanded=False):
                lv.show_histogram()
                lv.show_statistics()
            # add a button to download the data
            with st.expander("Power Flow Data", expanded=False):
                lv.PSA()
            with st.expander("Raw Data", expanded=False):
                lv.show_raw_data()
            

    # --------------------------- single grid --------------------------
    else:
        with st.form(key='LV_form_grid'):
            test_id = st.multiselect('test case IDs', list_lv_ids, key='LV_multiselect_grid_id')
            mapstyle = st.selectbox('Map style',['road','satellite'],placeholder='Please select',key='LV_map_style')
            show = st.checkbox('Show the map', key='LV_show_map')
            st.session_state['selected_region'] = test_id
            submitted = st.form_submit_button('Submit')
            # create an object of the class
            lv = GridVisualize('LV', test_id, mapstyle=mapstyle)

        if lv:
            with st.expander("Download data", expanded=False):
                col_download = st.columns(3)
                with col_download[0]:
                    st.write("Press this button to download geojson file:")
                    lv.download_geo()
                with col_download[1]:
                    st.write("Press this button to download pandapower file:")
                    lv.download_pandapower()
                with col_download[2]:
                    st.write("Press this button to download matpower file:")
                    lv.download_matpower()
            # show the statistics
            if show:
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                # draw the layers
                #lv.draw_layers_folium(substation_show=True, grid_show=True)
                lv.draw_layers()  
                # remove the hint above
                placeholder.empty()
            # add a button to download the data
            with st.expander("Power Flow Data", expanded=False):
                lv.PSA()
            with st.expander("Raw Data", expanded=False):
                lv.show_raw_data()
            
                
            


if __name__ == '__main__':
    lv_page()
