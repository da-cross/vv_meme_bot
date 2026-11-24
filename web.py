import hashlib
import os

import streamlit as st
from PIL import Image

from query import find_matches, locate_matched_images, _load_data
from text_classify import DIMENSIONS, SORT_KEYS, build_groups

WORDS_FILE = "picked_words.txt"
IMAGES_FILE = "picked_images.txt"

st.set_page_config(layout="wide", page_title="全自动VV表情包fetch bot")

st.markdown(
    """
    <style>
    /* 文案色块：矩形、无圆角、比纯黑底只浅一点点
       注意：单选模式父容器是 role=radiogroup，多选（选择模式）是 role=toolbar */
    div[role="radiogroup"],
    div[role="toolbar"] {
        gap: 10px !important;
        row-gap: 10px !important;
    }
    button[data-variant="pills"] {
        height: auto !important;
        min-height: 40px;
        padding: 8px 16px !important;
        border-radius: 0 !important;
        background-color: #141414 !important;
        border: 1px solid #242424 !important;
        color: #e8e8e8 !important;
        transition: background-color 0.12s ease, border-color 0.12s ease;
    }
    button[data-variant="pills"] p {
        font-size: 1.05rem !important;
        line-height: 1.55 !important;
        letter-spacing: 0.02em;
        color: inherit !important;
    }
    button[data-variant="pills"]:hover {
        background-color: #1d1d1d !important;
        border-color: #333333 !important;
    }
    /* 选中态：反色（单选用 aria-checked，多选用 aria-pressed） */
    button[data-variant="pills"][aria-checked="true"],
    button[data-variant="pills"][aria-pressed="true"] {
        background-color: #e8e8e8 !important;
        border-color: #e8e8e8 !important;
        color: #000000 !important;
    }
    /* 图片墙：等高裁切，直角 */
    [data-testid="stImage"] img {
        height: 150px !important;
        object-fit: cover;
        border-radius: 0 !important;
    }
    /* 其他控件跟随：面板边框压暗、统一直角 */
    [data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"] {
        border-color: #242424 !important;
        border-radius: 0 !important;
    }
    [data-testid="stTextInputRootElement"],
    [data-testid="stSelectbox"] div {
        border-radius: 0 !important;
    }
    hr { border-color: #1c1c1c !important; }
    /* 图片勾选框标签：只显示小号文件名 */
    div[data-testid="stCheckbox"] label p {
        font-size: 0.72rem !important;
        color: #8a8a8a !important;
        word-break: break-all;
    }</style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- 选择清单读写
def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(f"{line}\n" for line in lines))


def sync_words(add, remove):
    """立刻写回 picked_words.txt（保留原顺序，新词追加在末尾）。"""
    lines = read_lines(WORDS_FILE)
    present = set(lines)
    dirty = False
    if remove:
        gone = set(remove)
        lines = [line for line in lines if line not in gone]
        present -= gone
        dirty = dirty or bool(gone)
    for word in add:
        if word not in present:
            lines.append(word)
            present.add(word)
            dirty = True
    if dirty:
        write_lines(WORDS_FILE, lines)


def sync_images(paths):
    """点击图片即切换收录状态（有则删、无则加）。"""
    if not paths:
        return
    lines = read_lines(IMAGES_FILE)
    present = set(lines)
    for path in paths:
        if path in present:
            lines = [line for line in lines if line != path]
            present.discard(path)
        else:
            lines.append(path)
            present.add(path)
    write_lines(IMAGES_FILE, lines)


# ---------------------------------------------------------------- 数据
# 点击文案 → 作为搜索词。必须在输入框创建之前写入 session_state
if "pending_query" in st.session_state:
    st.session_state["search_text"] = st.session_state.pop("pending_query")
st.session_state.setdefault("search_text", "")

text_list, text_to_filepath, _ = _load_data()

picked_words = read_lines(WORDS_FILE)
picked_images = read_lines(IMAGES_FILE)


def fetch_images(query):
    results = find_matches(query, text_list, text_to_filepath)
    return locate_matched_images(results)


def group_images(words):
    """一组文案对应的所有图片（去重、保持顺序）。"""
    paths, seen = [], set()
    for word in words:
        for txt_name in text_to_filepath.get(word, ()):
            path = os.path.join("vvs", txt_name.replace(".txt", ".jpg"))
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def render_images(paths, key_prefix, selectable, picked_set, per_row=4):
    """图片网格。

    selectable 时整张图就是一个按钮（透明按钮盖在图上），点图即切换收录，
    已收录的图带一圈高亮描边。返回本轮被点击的图片路径列表。
    """
    if not selectable:
        cols = st.columns(per_row)
        for i, path in enumerate(paths):
            with cols[i % per_row]:
                st.image(Image.open(path), use_container_width=True)
        return []

    style, clicked = [], []
    cols = st.columns(per_row)
    for i, path in enumerate(paths):
        digest = hashlib.md5(path.encode("utf-8")).hexdigest()[:10]
        picked = path in picked_set
        tile_key = f"{key_prefix}-tile-{digest}"
        button_key = f"{key_prefix}-pick-{digest}"

        with cols[i % per_row]:
            with st.container(key=tile_key):
                st.image(Image.open(path), use_container_width=True)
                if st.button(" ", key=button_key, use_container_width=True):
                    clicked.append(path)

        style.append(
            f".st-key-{tile_key} {{ position: relative; }}"
            f".st-key-{button_key} {{ position: absolute; top: 0; left: 0; z-index: 5;"
            f" width: 100%; height: 150px; }}"
            f".st-key-{button_key} > div, .st-key-{button_key} [data-testid^='stButton']"
            f" {{ width: 100% !important; height: 150px !important; }}"
            f".st-key-{button_key} button {{ width: 100% !important; height: 150px !important;"
            f" min-height: 150px !important; opacity: 0; cursor: pointer; }}"
            + (
                f".st-key-{tile_key}::after {{ content: '✓'; position: absolute; top: 4px;"
                f" right: 6px; z-index: 6; font-size: 1.1rem; color: #000;"
                f" background: #e8e8e8; width: 22px; height: 22px; line-height: 22px;"
                f" text-align: center; }}"
                f".st-key-{tile_key} [data-testid='stImage'] {{ outline: 2px solid #e8e8e8;"
                f" outline-offset: -2px; }}"
                if picked
                else ""
            )
        )

    st.markdown(f"<style>{''.join(style)}</style>", unsafe_allow_html=True)
    return clicked


# ---------------------------------------------------------------- 页面
st.title("全自动VV表情包fetch bot")

select_mode = st.toggle(
    "选择模式：点词＝搜索并收录，点图＝收录/取消（立即写入文件）", key="select_mode"
)

query = st.text_input("模糊搜索:", key="search_text")

if query:
    images = fetch_images(query)
    if images:
        clicked = render_images(
            images, "search", select_mode, set(picked_images), per_row=4
        )
        if select_mode and clicked:
            sync_images(clicked)
            st.rerun()
    else:
        st.write("没搜到...")

st.divider()

st.subheader("全部文案")
st.caption(f"共 {len(text_list)} 条" + (" · 选择模式：点一次收录，再点一次取消" if select_mode else " · 点击即搜索"))

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

picked_set = set(picked_words)
with st.container(height=520, border=True):
    if select_mode:
        selected = st.pills(
            "点击文案即搜索并收录",
            groups[group],
            selection_mode="multi",
            default=[w for w in groups[group] if w in picked_set],
            key=f"pills_sel_{dimension}_{group}",
        ) or []
        added = [w for w in selected if w not in picked_set]
        removed = [w for w in groups[group] if w in picked_set and w not in set(selected)]
        if added or removed:
            sync_words(added, removed)
            if len(added) == 1 and not removed:
                st.session_state["pending_query"] = added[0]
                st.rerun()
    else:
        picked = st.pills(
            "点击文案即搜索",
            groups[group],
            selection_mode="single",
            key=f"pills_{dimension}_{group}",
        )
        if picked and picked != st.session_state["search_text"]:
            st.session_state["pending_query"] = picked
            st.rerun()

if select_mode:
    picked_images = read_lines(IMAGES_FILE)
    picked_set = set(picked_images)

    st.divider()
    st.subheader("图片墙")
    wall = group_images(groups[group])
    st.caption(f"当前分组「{group}」共 {len(wall)} 张图 · 点图即收录/取消，写入 {IMAGES_FILE}")
    if wall:
        LIMIT = 60
        if len(wall) > LIMIT:
            st.caption(f"（仅显示前 {LIMIT} 张，选更小的分组或直接用搜索看其余）")
        clicked = render_images(wall[:LIMIT], "wall", True, picked_set, per_row=4)
        if clicked:
            sync_images(clicked)
            st.rerun()

    st.divider()
    st.subheader("已选清单")
    picked_words = read_lines(WORDS_FILE)
    picked_images = read_lines(IMAGES_FILE)
    col_words, col_images = st.columns(2)
    with col_words:
        st.markdown(f"**词 · {len(picked_words)} 条** → `{WORDS_FILE}`")
        st.code("\n".join(picked_words) if picked_words else "(空)", language="text")
    with col_images:
        st.markdown(f"**图 · {len(picked_images)} 张** → `{IMAGES_FILE}`")
        st.code("\n".join(picked_images) if picked_images else "(空)", language="text")
    if st.button("清空两个清单"):
        write_lines(WORDS_FILE, [])
        write_lines(IMAGES_FILE, [])
        st.rerun()
