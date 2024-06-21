# main.py
import streamlit as st
from grid_class import GridVisualize
from LV_page import lv_page
from MV_page import mv_page

# Dictionary to map page names to their corresponding functions
pages = {
    "Medium Voltage": mv_page,
    "Low Voltage": lv_page,
}

def main():
    #select page
    st.sidebar.title("Navigation")
    page_selection = st.sidebar.radio("Please select", list(pages.keys()))
    with open('visualization/usermanual.md', 'r') as f:
            user_manual = f.read()
    
    with st.sidebar.expander("User Manual", expanded=False):
        st.markdown(
            user_manual,
            unsafe_allow_html=True)
    
    pages[page_selection]()

if __name__ == "__main__":
    main()
