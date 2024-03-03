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
    # add a button to jump to the help page
    if st.button('Help? Show the user manual!'):
        with open('usermanual.md', 'r') as f:
            user_manual = f.read()
            st.sidebar.markdown(
                user_manual,
                unsafe_allow_html=True,
            )
    # add a divider
    st.markdown("---")

    # --------------------------- municipality region --------------------------
    if genre == "***Select grids by municipality***":

        with st.form(key='LV_form_municipality'):
            cols = st.columns(2)
            with cols[0]:
                test_municipality = st.selectbox('municipality name', list_municipality_names, index=None, placeholder='Please select',
                                           key='LV_text_input_municipality')
                # update the session state
                st.session_state['selected_region'] = test_municipality
            with cols[1]:
                if st.checkbox('Show all grids in this municipality', key='LV_show_municipality_grids'):
                    grid_option = True
                    # check if the canton name is vacant
                    if test_municipality is None:
                        st.write("💥Warning: please select a municipality")
                        st.stop()
                else:
                    grid_option = False
                if st.checkbox('Show substation (grid name)', key='LV_test_id_checkbox'):
                    substation_option = True
                    if test_municipality is None:
                        st.write("💥Warning: please select a municipality")
                        st.stop()

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
                else:
                    substation_option = False
            lv = None
            # create a submit button to show the map
            submitted = st.form_submit_button('Show the map')
            if test_municipality is not None:
                # create an object of the class
                lv = GridVisualize('LV', dict_municipality_grid_lv[test_municipality])
                if submitted:
                    # when the app is running, give the hint that the map is loading
                    placeholder = st.empty()
                    placeholder.write("The map is loading..Please wait for a few seconds..")
                    # draw the layers
                    lv_layers = lv.draw_layers_folium(substation_show=substation_option, grid_show=grid_option)
                    # remove the hint above
                    placeholder.empty()

        if lv:
            # show the statistics of the selected region
            lv.show_histogram()
            # add a button to download the data
            lv.download()

    # --------------------------- single grid --------------------------
    else:
        test_id = st.multiselect('test case IDs', list_lv_ids, key='LV_multiselect_grid_id')
        # create an object of the class
        lv = GridVisualize('LV', test_id)
        with st.form(key='LV_form_grid_id'):

            # # add a dataframe to show the canton name of the selected test IDs
            # if st.checkbox('Show data of selected test IDs', key='LV_checkbox_show_multi_grid'):
            #     st.write('The canton name of the selected test IDs:')
            #     st.dataframe(table_ids_municipality[table_ids_municipality['grid_id'].isin(test_id)])

            # create a submit button to show the map
            submitted = st.form_submit_button('Show the map')
            if submitted:
                # when the app is running, give the hint that the map is loading
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                # draw the layers
                lv.draw_layers_folium(substation_show=True, grid_show=True)
                # remove the hint above
                placeholder.empty()

        if submitted:
            # show the statistics
            lv.show_histogram()
            # add a button to download the data
            lv.download()


if __name__ == '__main__':
    lv_page()
