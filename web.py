import streamlit as st
from PIL import Image

from query import find_matches, locate_matched_images, _load_data

st.set_page_config(layout="wide")

text_list, text_to_filepath, _ = _load_data()

def fetch_images(query):
    results = find_matches(query, text_list, text_to_filepath)
    img_paths = locate_matched_images(results)
    return img_paths

st.title("全自动VV表情包fetch bot")

query = st.text_input("模糊搜索:")

if query:
    images = fetch_images(query)
    if images:
        cols = st.columns(3)
        for i, img_path in enumerate(images):
            img = Image.open(img_path)
            cols[i % 3].image(img)
    else:
        st.write("没搜到...")