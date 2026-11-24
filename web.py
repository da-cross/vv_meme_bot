import hashlib
import json
import os

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from query import find_matches, locate_matched_images, _load_data
from text_classify import DIMENSION_SORT, DIMENSIONS, build_groups

DEFAULT_DIMENSION = "字数"   # 默认分类维度（排序方向默认升序）
IMAGES_FILE = "picked_images.txt"
NOTES_FILE = "image_notes.json"

# 右键收录桥：iframe 里监听父页面的 contextmenu，把点中的文案回传给 Python
rightclick = components.declare_component("rightclick", path="components/rightclick")

st.set_page_config(layout="wide", page_title="全自动VV表情包fetch bot")

st.markdown(
    """
    <style>
    /* 文案色块：矩形、无圆角、比纯黑底只浅一点点 */
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
    /* 选中（搜索词）：反色 */
    button[data-variant="pills"][aria-checked="true"],
    button[data-variant="pills"][aria-pressed="true"] {
        background-color: #e8e8e8 !important;
        border-color: #e8e8e8 !important;
        color: #000000 !important;
    }
    /* 侧边栏：加宽一档，文案块收紧 */
    [data-testid="stSidebar"] {
        min-width: 380px !important;
        max-width: 380px !important;
    }
    [data-testid="stSidebar"] button[data-variant="pills"] {
        min-height: 28px;
        padding: 3px 8px !important;
    }
    [data-testid="stSidebar"] button[data-variant="pills"] p {
        font-size: 0.82rem !important;
        line-height: 1.35 !important;
        letter-spacing: 0;
    }
    [data-testid="stSidebar"] div[role="radiogroup"],
    [data-testid="stSidebar"] div[role="toolbar"] {
        gap: 6px !important;
        row-gap: 6px !important;
    }
    /* 图片下方对应文案：做成无框小字按钮 */
    [class*="st-key-cap-"] button {
        background: transparent !important;
        border: none !important;
        min-height: 0 !important;
        height: auto !important;
        padding: 2px 4px !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    [class*="st-key-cap-"] button p {
        font-size: 0.78rem !important;
        line-height: 1.4 !important;
        color: #8f8f8f !important;
    }
    [class*="st-key-cap-"] button:hover p {
        color: #ffffff !important;
    }
    /* 视图切换：无边框、无圆角，只靠底色区分 */
    [class*="st-key-view_pick"] button[data-variant="pills"] {
        border: none !important;
        border-radius: 0 !important;
        min-height: 34px;
        padding: 6px 16px !important;
        background-color: #141414 !important;
        color: #b9b9b9 !important;
    }
    [class*="st-key-view_pick"] button[data-variant="pills"]:hover {
        background-color: #202020 !important;
        color: #ffffff !important;
    }
    [class*="st-key-view_pick"] button[data-variant="pills"][aria-checked="true"],
    [class*="st-key-view_pick"] button[data-variant="pills"][aria-pressed="true"] {
        background-color: #e8e8e8 !important;
        color: #000000 !important;
    }
    /* 文案行尾的删除按钮 */
    [class*="st-key-del-"] button {
        background: transparent !important;
        border: none !important;
        min-height: 0 !important;
        height: auto !important;
        padding: 0 2px !important;
        color: #5c5c5c !important;
        font-size: 0.85rem !important;
        line-height: 1 !important;
    }
    [class*="st-key-del-"] button:hover { color: #ffffff !important; }
    /* 图片下的自定义文案 */
    .note {
        margin: 2px 0 4px 0;
        padding: 4px 6px;
        border-left: 2px solid #e8e8e8;
        color: #e8e8e8;
        font-size: 0.82rem;
        line-height: 1.45;
        text-align: left;
        word-break: break-word;
    }
    /* 缩略图：等高但完整展示（contain，不裁切）；高度由侧边栏滑块注入 */
    [data-testid="stImage"] img {
        width: 100% !important;
        object-fit: contain !important;
        background-color: #000000;
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
    /* 侧边栏收起时，主区吃满释放出来的宽度（侧栏是 translateX 移出，仍占 380px 布局宽度） */
    [data-testid="stMain"] {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][data-collapsed="true"])
        [data-testid="stMain"] {
        width: calc(100vw - 80px) !important;
        margin-left: -300px !important;
    }
    [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    hr { border-color: #1c1c1c !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- 清单读写
def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(f"{line}\n" for line in lines))


def read_notes():
    """图片 -> 自定义文案。"""
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2, sort_keys=True)


def toggle_word_images(word):
    """点图下文案：该句对应的图片整组收录 / 整组取消。"""
    paths = images_of_word(word)
    if not paths:
        return
    lines = read_lines(IMAGES_FILE)
    present = set(lines)
    if all(path in present for path in paths):
        gone = set(paths)
        lines = [line for line in lines if line not in gone]
    else:
        for path in paths:
            if path not in present:
                lines.append(path)
                present.add(path)
    write_lines(IMAGES_FILE, lines)


def add_images(paths):
    """只追加不删除，返回是否有新增。"""
    if not paths:
        return False
    lines = read_lines(IMAGES_FILE)
    present = set(lines)
    added = False
    for path in paths:
        if path not in present:
            lines.append(path)
            present.add(path)
            added = True
    if added:
        write_lines(IMAGES_FILE, lines)
    return added


def toggle_images(paths):
    """收录 / 取消收录图片（立刻写回文件）。"""
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
# 点文案 → 搜索词。必须在输入框创建之前写入 session_state
if "pending_query" in st.session_state:
    st.session_state["search_text"] = st.session_state.pop("pending_query")
    # 点文案进来的一律走精确搜索（手打关键词仍是模糊）
    st.session_state["exact_query"] = st.session_state["search_text"]
st.session_state.setdefault("search_text", "")

text_list, text_to_filepath, _ = _load_data()

# 图片 -> 对应文案（text_to_filepath 反向索引）
IMAGE_TO_TEXTS = {}
for _text, _files in text_to_filepath.items():
    for _file in _files:
        IMAGE_TO_TEXTS.setdefault(_file, []).append(_text)


# 右键入编辑：digest -> 图片路径。放 session_state 里，跨 rerun 保留
DIGEST_PATHS = st.session_state.setdefault("digest_paths", {})


def on_type_query():
    """手打关键词：清掉精确标记，回到模糊搜索。"""
    st.session_state["exact_query"] = None


def pick_word(key):
    """侧边栏点文案：把选中的词交给下一轮，走精确搜索。"""
    value = st.session_state.get(key)
    if value:
        st.session_state["pending_query"] = value


def fetch_images(query, exact=False):
    if exact:
        files = text_to_filepath.get(query, [])
        return [
            os.path.join("vvs", name.replace(".txt", ".jpg")) for name in files
        ]
    results = find_matches(query, text_list, text_to_filepath)
    return locate_matched_images(results)


def group_images(words):
    paths, seen = [], set()
    for word in words:
        for txt_name in text_to_filepath.get(word, ()):
            path = os.path.join("vvs", txt_name.replace(".txt", ".jpg"))
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def delete_caption(image_path, sentence):
    """从该图的 OCR 文本里删掉一句，并重建索引（text_list / text_to_filepath）。"""
    txt_name = os.path.basename(image_path).replace(".jpg", ".txt")
    txt_path = os.path.join("txts", txt_name)
    if not os.path.exists(txt_path):
        return
    with open(txt_path, encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]
    kept = [line for line in lines if line.strip() != sentence]
    if len(kept) == len(lines):
        return
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("".join(f"{line}\n" for line in kept if line.strip()))

    # 索引跟着重建，页面上的分组/搜索立刻一致
    from data_update import read_and_save_txt_files

    read_and_save_txt_files("txts")




def images_of_word(word):
    """某条文案对应的所有图片路径。"""
    return [
        os.path.join("vvs", name.replace(".txt", ".jpg"))
        for name in text_to_filepath.get(word, [])
    ]


def sentences_of(image_path):
    stem = os.path.basename(image_path).replace(".jpg", ".txt")
    return IMAGE_TO_TEXTS.get(stem, [])


def render_images(paths, key_prefix, picked_images_set, thumb_h=150, per_row=5):
    """图片网格：点图＝收录图，点图下文案＝收录句子。返回 (点击的图, 点击的句子)。"""
    clicked_images, clicked_words, clicked_deletes = [], [], []
    notes = read_notes()
    style = []
    cols = st.columns(per_row)

    for i, path in enumerate(paths):
        digest = hashlib.md5(path.encode("utf-8")).hexdigest()[:10]
        DIGEST_PATHS[digest] = path
        picked = path in picked_images_set
        tile_key = f"{key_prefix}-tile-{digest}"
        button_key = f"{key_prefix}-pick-{digest}"

        with cols[i % per_row]:
            with st.container(key=tile_key):
                st.image(Image.open(path), use_container_width=True)
                if st.button(" ", key=button_key, use_container_width=True):
                    clicked_images.append(path)

                custom = notes.get(path)
                if custom:
                    st.markdown(
                        f'<div class="note">✎ {custom}</div>', unsafe_allow_html=True
                    )

                sentences = sentences_of(path)[:2]
                can_delete = len(sentences_of(path)) >= 2
                for sentence in sentences:
                    group = images_of_word(sentence)
                    collected = bool(group) and all(p in picked_images_set for p in group)
                    sh = hashlib.md5(sentence.encode("utf-8")).hexdigest()[:8]
                    label = f"{'✓ ' if collected else ''}{sentence}"
                    if can_delete:
                        c_cap, c_del = st.columns([9, 1])
                        if c_cap.button(
                            label,
                            key=f"cap-{digest}-{sh}",
                            use_container_width=True,
                        ):
                            clicked_words.append(sentence)
                        if c_del.button(
                            "×",
                            key=f"del-{digest}-{sh}",
                            use_container_width=True,
                            help="删除这条文案（仅这张图）",
                        ):
                            clicked_deletes.append((path, sentence))
                    elif st.button(
                        label, key=f"cap-{digest}-{sh}", use_container_width=True
                    ):
                        clicked_words.append(sentence)

        picked_css = (
            f".st-key-{tile_key}::after {{ content: '✓'; position: absolute; top: 4px;"
            f" right: 6px; z-index: 6; font-size: 1.1rem; color: #000;"
            f" background: #e8e8e8; width: 22px; height: 22px; line-height: 22px;"
            f" text-align: center; }}"
            f".st-key-{tile_key} [data-testid='stImage'] {{ outline: 2px solid #e8e8e8;"
            f" outline-offset: -2px; }}"
            if picked
            else ""
        )

        style.append(
            f".st-key-{tile_key} {{ position: relative; }}"
            f".st-key-{button_key} {{ position: absolute; top: 0; left: 0; z-index: 5;"
            f" width: 100%; height: {thumb_h}px; }}"
            f".st-key-{button_key} > div, .st-key-{button_key} [data-testid^='stButton']"
            f" {{ width: 100% !important; height: {thumb_h}px !important; }}"
            f".st-key-{button_key} button {{ width: 100% !important; height: {thumb_h}px !important;"
            f" min-height: {thumb_h}px !important; opacity: 0; cursor: pointer; }}"
            + picked_css
        )

    st.markdown(f"<style>{''.join(style)}</style>", unsafe_allow_html=True)
    return clicked_images, clicked_words, clicked_deletes


# ---------------------------------------------------------------- 侧边栏
with st.sidebar:
    st.subheader("检索与挑选")

    query = st.text_input(
        "模糊搜索:", key="search_text", on_change=on_type_query
    )

    dimension = st.radio(
        "分类维度",
        list(DIMENSIONS),
        index=list(DIMENSIONS).index(DEFAULT_DIMENSION),
        key="dimension",
    )
    sort_by = DIMENSION_SORT[dimension]
    descending = (
        st.radio("排序方向", ["升序", "降序"], key="order", horizontal=True) == "降序"
    )

    groups = build_groups(text_list, text_to_filepath, dimension, sort_by, descending)
    group = st.selectbox(
        f"分组（{len(groups)} 组）", list(groups), key=f"group_{dimension}"
    )
    st.caption(
        f"{dimension} · {'按' + sort_by if sort_by != dimension else ''}"
        f"{'降序' if descending else '升序'} · {len(groups[group])} 条"
    )
    st.caption("**左键**搜索 · **点图或图下文案**收藏图片 · **右键图片/文案**编辑文案")

    pill_key = f"pills_{dimension}_{group}"
    with st.container(height=320, border=True):
        st.pills(
            "文案",
            groups[group],
            selection_mode="single",
            key=pill_key,
            on_change=pick_word,
            args=(pill_key,),
            label_visibility="collapsed",
        )

    st.caption(f"已收录图片 {len(read_lines(IMAGES_FILE))} 张")

    # 右键桥：不可见，只负责把父页面右键的文案回传


# ---------------------------------------------------------------- 主区
st.title("全自动VV表情包fetch bot")

VIEWS = ("搜索结果", "图片墙", "已收集")
views_col, size_col = st.columns([3, 1], vertical_alignment="center")

with views_col:
    picked_view = st.pills(
        "视图",
        VIEWS,
        selection_mode="single",
        key="view_pick",
        default=st.session_state.get("view", VIEWS[0]),
        label_visibility="collapsed",
    )
    if picked_view:
        st.session_state["view"] = picked_view
view = st.session_state.get("view", VIEWS[0])

with size_col:
    hover_preview = st.toggle(
        "悬停预览", value=True, key="hover_preview",
        help="鼠标在缩略图上停留 400ms 后全屏预览",
    )
    thumb_h = st.slider(
        "缩略图大小", 90, 320, 150, step=10, key="thumb_size",
        label_visibility="collapsed",
        help="缩略图高度（px），列数自动适配；影响搜索结果 / 图片墙 / 已收集",
    )
per_row = max(2, min(8, round(1200 / (thumb_h * 1.6))))

st.markdown(
    f"<style>[data-testid='stImage'] img {{ height: {thumb_h}px !important; }}</style>",
    unsafe_allow_html=True,
)

# 右键桥 + 悬停预览浮层（enabled 跟随上方开关）
right_pick = rightclick(
    enabled=hover_preview, key="rightclick", default=None
)
if right_pick and isinstance(right_pick, dict):
    if right_pick.get("ts") != st.session_state.get("rightclick_ts"):
        st.session_state["rightclick_ts"] = right_pick.get("ts")
        if right_pick.get("digest"):
            st.session_state["edit_image"] = right_pick.get("digest")
            st.session_state.pop(f"note_edit_{right_pick.get('digest')}", None)
            if right_pick.get("caption"):
                st.session_state["edit_prefill"] = right_pick["caption"]
            st.rerun()

picked_images = read_lines(IMAGES_FILE)
picked_images_set = set(picked_images)

# 右键图片 -> 编辑该图的自定义文案
edit_digest = st.session_state.get("edit_image")
if edit_digest:
    edit_path = DIGEST_PATHS.get(edit_digest)
    notes = read_notes()
    with st.container(border=True):
        if not edit_path:
            st.caption("这张图不在当前视图里了，请重新右键。")
            if st.button("关闭"):
                st.session_state.pop("edit_image", None)
                st.rerun()
        else:
            st.caption(f"编辑文案 · {os.path.basename(edit_path)}")
            prefill = notes.get(edit_path)
            if prefill is None:
                prefill = st.session_state.get("edit_prefill", "")
            left, right = st.columns([5, 1])
            new_text = left.text_area(
                "自定义文案",
                value=prefill,
                key=f"note_edit_{edit_digest}",
                height=80,
                placeholder="写点什么，留空保存 = 删除自定义文案",
                label_visibility="collapsed",
            )
            if right.button("保存", use_container_width=True):
                if new_text.strip():
                    notes[edit_path] = new_text.strip()
                else:
                    notes.pop(edit_path, None)
                write_notes(notes)
                st.session_state.pop("edit_image", None)
                st.session_state.pop("edit_prefill", None)
                st.rerun()
            if right.button("取消", use_container_width=True):
                st.session_state.pop("edit_image", None)
                st.session_state.pop("edit_prefill", None)
                st.rerun()

if view == "搜索结果":
    if not query:
        st.caption("左侧输入搜索词，或点侧边栏里的文案。")
    else:
        exact = bool(query) and st.session_state.get("exact_query") == query
        images = fetch_images(query, exact=exact)
        mode = "精确" if exact else "模糊"
        st.subheader(f"「{query}」· {mode}匹配 · {len(images)} 张")
        if images:
            clicked_images, clicked_words, clicked_deletes = render_images(
                images, "search", picked_images_set, thumb_h, per_row
            )
            if clicked_deletes:
                for img, sentence in clicked_deletes:
                    delete_caption(img, sentence)
                st.rerun()
            if clicked_images or clicked_words:
                toggle_images(clicked_images)
                for word in clicked_words:
                    toggle_word_images(word)
                st.rerun()
        else:
            st.caption("没搜到...")

elif view == "图片墙":
    wall = group_images(groups[group])
    st.subheader(f"图片墙 · {group} · {len(wall)} 张")
    st.caption("点图＝收藏/取消该图 · 点图下文案＝收藏/取消该句对应的整组图片")
    if wall:
        LIMIT = 60
        if len(wall) > LIMIT:
            st.caption(f"（仅显示前 {LIMIT} 张，选更小的分组或直接用搜索看其余）")
        clicked_images, clicked_words, clicked_deletes = render_images(
            wall[:LIMIT], "wall", picked_images_set, thumb_h, per_row
        )
        if clicked_deletes:
            for img, sentence in clicked_deletes:
                delete_caption(img, sentence)
            st.rerun()
        if clicked_images or clicked_words:
            toggle_images(clicked_images)
            for word in clicked_words:
                toggle_word_images(word)
            st.rerun()

else:  # 已收集
    st.subheader(f"已收集 · 图片 {len(picked_images)} 张")

    if picked_images:
        st.caption(f"写入 {IMAGES_FILE} · 点图取消收录 · 点图下文案切换该句的整组图片")
        clicked_images, clicked_words, clicked_deletes = render_images(
            picked_images, "picked", picked_images_set, thumb_h, per_row
        )
        if clicked_deletes:
            for img, sentence in clicked_deletes:
                delete_caption(img, sentence)
            st.rerun()
        if clicked_images or clicked_words:
            toggle_images(clicked_images)
            for word in clicked_words:
                toggle_word_images(word)
            st.rerun()
    else:
        st.caption(f"还没有收录图片（{IMAGES_FILE} 为空）")

    notes = read_notes()
    if notes:
        with st.expander(f"自定义文案 · {len(notes)} 条 → {NOTES_FILE}"):
            st.json(notes)

    if picked_images:
        if st.button("清空图片清单"):
            write_lines(IMAGES_FILE, [])
            st.rerun()
