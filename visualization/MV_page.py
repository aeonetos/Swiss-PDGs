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
                mapstyle = st.selectbox('Map style',['road','satellite'],placeholder='Please select',key='MV_map_style')
            with cols[1]:
                show=st.checkbox('Show the map', key='MV_show_canton')
                with st.expander("Show substation (grid name)", expanded=False):
                    st.dataframe(table_ids_canton[table_ids_canton['region_name'] == test_canton])
            mv = None
            # create a submit button to show the map
            st.form_submit_button('Submit')
            if test_canton is not None:
                # create an object of the class
                mv = GridVisualize('MV', dict_canton_grid_mv[test_canton],mapstyle=mapstyle)
            
        if mv: 
            with st.expander("Download Data", expanded=False):
                placeholder = st.empty()
                placeholder.write("Preparing the data..Please wait for a few seconds..")
                col_download = st.columns(3)
                with col_download[0]:
                    st.write("Press this bottom to download geojson file:")
                    mv.download_geo()
                with col_download[1]:
                    st.write("Press this bottom to download pandapower file:")
                    mv.download_pandapower() 
                with col_download[2]:
                    st.write("Press this bottom to download matpower file:")
                    mv.download_matpower()
                placeholder.empty()
            if show:  
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                # draw the layers
                mv.draw_layers()
                # remove the hint above
                placeholder.empty()
            '''with st.expander("Loads Statistic Data", expanded=False):
                mv.show_histogram()
                mv.show_statistics()
            # add a button to download the 
            with st.expander("Power Flow Data", expanded=False):
                mv.PSA()'''
            with st.expander("Raw Data", expanded=False):
                mv.show_raw_data()
            

    # --------------------------- single grid --------------------------
    # single grid part, if the user chooses to show the single grid,
    # first show the text field to type in the test ID,
    # then show the map of the selected test ID
    else:
        with st.form(key='MV_form_grid_id'):
            test_id = st.multiselect('test case IDs', table_ids_canton['grid_id'].values, key='MV_multiselect_grid_id')
            mapstyle = st.selectbox('Map style',['road','satellite'],placeholder='Please select',key='MV_map_style')
            show = st.checkbox('Show the map', key='MV_show_grid_id')
            # create an object of the class     
            st.form_submit_button('Submit')       
            mv = GridVisualize('MV', test_id, mapstyle=mapstyle)   

        if mv:
            with st.expander("Download Data", expanded=False):
                col_download = st.columns(3)
                with col_download[0]:
                    st.write("Press this bottom to download geojson file:")
                    mv.download_geo()
                with col_download[1]:
                    st.write("Press this bottom to download pandapower file:")
                    mv.download_pandapower()
                with col_download[2]:
                    st.write("Press this bottom to download matpower file:")
                    mv.download_matpower()
            # show the statistics
            if show:
                placeholder = st.empty()
                placeholder.write("The map is loading..Please wait for a few seconds..")
                # draw the layers
                mv.draw_layers()
                # remove the hint above
                placeholder.empty()
            # add a button to download the data
            '''with st.expander("Power Flow Data", expanded=False):
                mv.PSA()'''
            with st.expander("Raw Data", expanded=False):
                mv.show_raw_data()
            


if __name__ == '__main__':
    mv_page()