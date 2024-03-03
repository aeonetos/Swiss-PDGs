from grid_class import *
from streamlit_extras.switch_page_button import switch_page
import time


def mv_page():

    data_path = 'data_processing/'

    # ----------------------- Process cantons ----------------------
    # load the dictionary connecting the canton and the grid
    with open(data_path + 'dict_canton_grid_MV.json') as json_file:
        dict_canton_grid_mv = json.load(json_file)
    list_canton_names = list(dict_canton_grid_mv.keys())
    table_ids_canton = pd.read_csv(data_path + 'table_grid_canton_MV.csv')

    # --------------------------- MV network ---------------------------
    # set the title of the page
    st.title("The MV network")
    # add a single checkbox to choose the test case
    genre = st.radio(
        "Which one do you want to show?",
        ["***Select grids by IDs***", "***Select grids by canton***"],
        captions=["show selected test ids", "show the whole canton region"],
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

    # --------------------------- canton region --------------------------
    # create a session state
    if 'stage' not in st.session_state:
        st.session_state['stage'] = 'story_generation'

    if genre == "***Select grids by canton***":

        with st.form(key='MV_form_canton'):
            cols = st.columns(2)
            with cols[0]:
                test_canton = st.selectbox('canton name', list_canton_names, index=None, placeholder='Please select',
                                           key='MV_text_input_canton')
                # update the session state
                st.session_state['selected_region'] = test_canton
            with cols[1]:
                if st.checkbox('Show all grids in this canton', key='MV_show_canton_grids'):
                    grid_option = True
                    # check if the canton name is vacant
                    if test_canton is None:
                        st.write("💥Warning: please select a canton")
                        st.stop()
                else:
                    grid_option = False
                if st.checkbox('Show substation (grid name)', key='MV_test_id_checkbox'):
                    substation_option = True
                    if test_canton is None:
                        st.write("💥Warning: please select a canton")
                        st.stop()

                    st.dataframe(table_ids_canton[table_ids_canton['region_name'] == test_canton])
                else:
                    substation_option = False
            mv = None
            # create a submit button to show the map
            submitted = st.form_submit_button('Show the map')

            if test_canton is not None:
                # create an object of the class
                mv = GridVisualize('MV', dict_canton_grid_mv[test_canton])
                if submitted:
                    # when the app is running, give the hint that the map is loading
                    placeholder = st.empty()
                    placeholder.write("The map is loading..Please wait for a few seconds..")
                    # draw the layers
                    mv.draw_layers_folium(substation_show=substation_option, grid_show=grid_option)
                    # remove the hint above
                    placeholder.empty()

        if mv:
            # show the statistics
            mv.show_histogram()
            # add a button to download the data
            mv.download()

    # --------------------------- single grid --------------------------
    # single grid part, if the user chooses to show the single grid,
    # first show the text field to type in the test ID,
    # then show the map of the selected test ID
    else:
        test_id = st.multiselect('test case IDs', table_ids_canton['grid_id'].values, key='MV_multiselect_grid_id')
        # create an object of the class
        mv = GridVisualize('MV', test_id)
        with st.form(key='MV_form_grid_id'):
            submitted = st.form_submit_button('Show the map')
            if submitted:
                # when the app is running, give the hint that the map is loading
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                # draw the layers
                mv.draw_layers_folium(substation_show=True, grid_show=True)
                # remove the hint above
                placeholder.empty()

        if submitted:
            # show the statistics
            mv.show_histogram()
            # add a button to download the data
            mv.download()


if __name__ == '__main__':
    mv_page()