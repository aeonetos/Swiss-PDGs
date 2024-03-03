# main.py
import streamlit as st
from LV_page import lv_page
from MV_page import mv_page

# Dictionary to map page names to their corresponding functions
pages = {
    "Medium Voltage": mv_page,
    "Low Voltage": lv_page,
}


def main():
    st.sidebar.title("Navigation")
    page_selection = st.sidebar.radio("Please select", list(pages.keys()))

    # Execute the selected page function
    pages[page_selection]()


if __name__ == "__main__":
    main()
