import streamlit as st
from PIL import Image

from query import find_matches, locate_matched_images, _load_data
from text_classify import DIMENSIONS, SORT_KEYS, build_groups

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
st.caption(f"共 {len(text_list)} 条 · 点击任意文案即用该条发起搜索")

left, right = st.columns([1, 3])
with left:
    dimension = st.radio("分类维度", list(DIMENSIONS), key="dimension")
    sort_by = st.selectbox("排序依据", list(SORT_KEYS), key="sort_by")
    descending = (
        st.radio("排序方向", ["升序", "降序"], key="order", horizontal=True) == "降序"
    )

groups = build_groups(text_list, text_to_filepath, dimension, sort_by, descending)
group = right.selectbox(
    f"分组（{len(groups)} 组）", list(groups), key=f"group_{dimension}"
)
right.caption(f"当前：{dimension} 分组 · {sort_by} {'降序' if descending else '升序'}")

picked = st.pills(
    "点击文案即搜索",
    groups[group],
    selection_mode="single",
    key=f"pills_{dimension}_{group}",
)
if picked and picked != st.session_state["search_text"]:
    st.session_state["pending_query"] = picked
    st.rerun()
