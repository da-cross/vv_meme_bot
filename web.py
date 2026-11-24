import streamlit as st
from PIL import Image

from query import find_matches, locate_matched_images, _load_data
from text_classify import DIMENSIONS, build_groups

st.set_page_config(layout="wide", page_title="全自动VV表情包fetch bot")

# 点击文案 → 作为搜索词。必须在输入框创建之前写入 session_state
if "pending_query" in st.session_state:
    st.session_state["search_text"] = st.session_state.pop("pending_query")
st.session_state.setdefault("search_text", "")

text_list, text_to_filepath, _ = _load_data()


def fetch_images(query):
    results = find_matches(query, text_list, text_to_filepath)
    img_paths = locate_matched_images(results)
    return img_paths


st.title("全自动VV表情包fetch bot")

query = st.text_input("模糊搜索:", key="search_text")

if query:
    images = fetch_images(query)
    if images:
        cols = st.columns(4)
        for i, img_path in enumerate(images):
            cols[i % 4].image(Image.open(img_path))
    else:
        st.write("没搜到...")

st.divider()

st.subheader("全部文案")
st.caption(f"共 {len(text_list)} 条 · 点击任意文案即用该条发起搜索 · 组内按首字、长度排序")

left, right = st.columns([1, 4])
dimension = left.radio("分类维度", list(DIMENSIONS), key="dimension")
groups = build_groups(text_list, text_to_filepath, dimension)
group = right.selectbox(
    f"分组（{len(groups)} 组）", list(groups), key=f"group_{dimension}"
)

picked = st.pills(
    "点击文案即搜索",
    groups[group],
    selection_mode="single",
    key=f"pills_{dimension}_{group}",
)
if picked and picked != st.session_state["search_text"]:
    st.session_state["pending_query"] = picked
    st.rerun()
