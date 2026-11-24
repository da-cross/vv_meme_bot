# coding: utf-8
"""「全部文案」浏览用的分类与排序。

每个维度都是纯函数：给定一条文案（及对应图片数）返回一个或多个分组名，
组内统一按「文本首字 → 长度 → 文本」排序。加新维度只需往 DIMENSIONS 里塞一项。
"""
from collections import OrderedDict

from pypinyin import lazy_pinyin

# ---------------------------------------------------------------- 话题（多标签）
# 一条文案可同时命中多个标签；都不命中则归入「未归类」
TOPIC_RULES = (
    ("台湾 · 两岸", ("台湾", "金门", "两岸", "台独", "大选")),
    ("香港", ("香港",)),
    ("美国 · 中美", ("美国", "中美", "美利坚", "特朗普", "拜登", "白宫", "华盛顿", "纽约")),
    (
        "西方 · 制度",
        (
            "西方", "民主", "制度", "普世", "自由", "人权", "种族", "资本", "选票",
            "政治正确", "双标", "双重标准", "殖民", "虚伪", "傲慢", "偏见", "干涉",
        ),
    ),
    (
        "经济 · 民生",
        (
            "经济", "金融", "崩溃", "贸易", "增长", "债务", "股市", "房价", "百姓",
            "民生", "脱贫", "小康", "现代化", "就业", "收入", "生活",
        ),
    ),
    ("疫情 · 公共", ("疫情", "封控", "呼吸机", "病毒", "健康", "安全")),
    (
        "军事 · 国际",
        ("军事", "战争", "战乱", "冲突", "危机", "峰会", "主权", "领土", "屠杀",
         "红海", "中东", "中俄", "东盟", "一带一路", "命运共同体"),
    ),
    (
        "言论 · 媒体",
        ("言论", "媒体", "新闻", "报道", "舆论", "发声", "采访", "话语", "真相",
         "说谎", "撒谎", "欺骗", "偷窃"),
    ),
    ("教育 · 青年", ("教育", "学生", "青年", "一代", "大学", "吃苦", "年轻", "成长")),
    (
        "国家 · 民族",
        ("中国", "中华", "民族", "祖国", "崛起", "复兴", "文明", "道路", "模式",
         "人民", "统一", "新疆", "党"),
    ),
    (
        "自信 · 心态",
        (
            "自信", "心态", "怕", "谦虚", "笑话", "震撼", "可笑", "荒谬", "愚昧",
            "无知", "脑残", "心虚", "底线", "道德", "实力", "优势", "面子", "骄傲",
            "精彩", "光荣", "自豪", "挫折", "感动", "乐观", "淡定", "自卑",
        ),
    ),
    (
        "对抗 · 交锋",
        ("斗争", "对抗", "反击", "警告", "惩罚", "制裁", "打压", "侵犯", "挑衅",
         "痛击", "羞辱", "道歉", "赔礼", "赔偿", "耳光", "巴掌"),
    ),
    (
        "评价 · 输赢",
        ("赢", "输", "竞争", "排名", "第一", "佩服", "优秀", "专业", "水准",
         "厉害", "了不起", "成功", "失败", "错误", "教训"),
    ),
)
OTHER_TOPIC = "未归类"

# ---------------------------------------------------------------- 字数
LENGTH_BUCKETS = (
    ("短句 · 1-6 字", 1, 6),
    ("中句 · 7-12 字", 7, 12),
    ("长句 · 13-20 字", 13, 20),
    ("长段 · 20 字以上", 21, 10**6),
)

# ---------------------------------------------------------------- 热度
POPULARITY_BUCKETS = (
    ("常见 · 1 张", 1, 1),
    ("次常见 · 2-3 张", 2, 3),
    ("少见 · 4 张以上", 4, 10**6),
)

NO_INITIAL = "#"


def first_pinyin(text: str) -> str:
    """文本首字的拼音；首字不是汉字时返回空串。"""
    head = text[:1]
    if not ("\u4e00" <= head <= "\u9fff"):
        return ""
    parts = lazy_pinyin(head)
    return parts[0] if parts else ""


def _in_buckets(n: int, buckets):
    for label, low, high in buckets:
        if low <= n <= high:
            return label
    return buckets[-1][0]


def topic_labels(text: str, n_images: int):
    labels = [label for label, keywords in TOPIC_RULES if any(k in text for k in keywords)]
    return labels or [OTHER_TOPIC]


def length_label(text: str, n_images: int):
    return _in_buckets(len(text), LENGTH_BUCKETS)


def initial_label(text: str, n_images: int):
    py = first_pinyin(text)
    return py[0].upper() if py else NO_INITIAL


def popularity_label(text: str, n_images: int):
    return _in_buckets(n_images, POPULARITY_BUCKETS)


# 维度名 -> (分组函数, 分组顺序)；顺序为 None 时按分组名排序
DIMENSIONS = OrderedDict(
    (
        ("首字", (initial_label, None)),
        ("话题", (topic_labels, [label for label, _ in TOPIC_RULES] + [OTHER_TOPIC])),
        ("字数", (length_label, [label for label, _, _ in LENGTH_BUCKETS])),
        ("热度", (popularity_label, [label for label, _, _ in POPULARITY_BUCKETS])),
    )
)

ALL_GROUP = "全部"


def sort_key(text: str):
    """排序：文本首字（拼音）→ 长度 → 文本本身。"""
    py = first_pinyin(text)
    return (py[:1] or "~", py, len(text), text)


def build_groups(texts, text_to_filepath, dimension: str, with_all: bool = True):
    """返回 OrderedDict{分组名: [文案...]}，组内已按 sort_key 排序。"""
    group_fn, order = DIMENSIONS[dimension]

    buckets = {}
    for text in texts:
        labels = group_fn(text, len(text_to_filepath.get(text, ())))
        if isinstance(labels, str):
            labels = (labels,)
        for label in labels:
            buckets.setdefault(label, []).append(text)

    if order is not None:
        labels = [label for label in order if label in buckets]
    else:
        labels = sorted(buckets, key=lambda label: (label == NO_INITIAL, label))

    groups = OrderedDict((label, sorted(buckets[label], key=sort_key)) for label in labels)
    if with_all:
        groups = OrderedDict([(ALL_GROUP, sorted(texts, key=sort_key)), *groups.items()])
    return groups
