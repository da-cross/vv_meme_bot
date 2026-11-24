# coding: utf-8
"""OCR 文本清洗。

`txts/*.txt` 是逐图 OCR 的原始结果，里面除了表情包文案，还混有画面上的台标、
节目标识、播放器 UI，以及台标区域被反复识别出来的乱码。这里在「汇总成检索
索引」这一步把它们滤掉，原始 OCR 结果（txts/）保持不动。

规则覆盖不到、经人工逐行确认的碎片放在 MANUAL_JUNK 里。
"""
import difflib
import re

_CJK = re.compile(r"[\u4e00-\u9fff]")

# 画面固定出现的台标 / 节目标识 / 出镜人名，都不是表情包文案
WATERMARKS = (
    "东方卫视",
    "观视频",
    "观传媒",
    "这就是中国",
    "张维为",
    "复旦大学中国研究院",
    "DRAGON TV",
    "CHINA NOW",
    "GUAN MEDIA",
)

# 播放器 UI、时间戳、站内号、书名号之类
_UI_PATTERNS = tuple(
    re.compile(p)
    for p in (
        r"正在看",
        r"\d{1,2}:\d{2}\s*/\s*\d{1,2}:\d{2}",
        r"BV[0-9A-Za-z]{6,}",
        r"@\S+",
        r"[《》|]",
        r"卫视",
        r"观视",
    )
)

# 人工逐行复核确认的乱码（台标/角标区域的 OCR 碎片，读不出原意）
MANUAL_JUNK = frozenset(
    {
        "中中中馆",
        "中中国：组织走",
        "中“贱民紫价层",
        "中国：线",
        "乐百马视",
        "作A杯口W",
        "出正在租",
        "本口卫我",
        "东有杂粥",
        "汉就好日座",
        "油业七学中平的生",
        "特日名子画东长保",
        "现频工作室业",
        "车方口次",
        "古愚味没有底线",
        "品威珍",
        "品威缘",
        "心有缘",
        "工件堂",
        "时心节",
        "见步顶",
        "研究院",
        "世界观察",
        "万家乐",
        "我假也成為革命者的活",
    }
)

# 高置信度的 OCR 错别字（只收语义唯一确定的，存疑的一律不动）
TYPO_FIXES = (
    ("厉善", "厉害"),
    ("事卖", "事实"),
    ("成莎", "成就"),
    ("精菜", "精彩"),
    ("光菜", "光荣"),
    ("起菜", "起来"),
    ("自已", "自己"),
    ("竞然", "竟然"),
    ("恐伯", "恐怕"),
    ("河以", "可以"),
    ("皮击", "抨击"),
    ("凄修", "凄惨"),
    ("科药感", "科技感"),
    ("大迎", "大选"),
    ("害司", "害己"),
    ("鼓学", "鼓掌"),
    ("在平", "在乎"),
    ("至令", "至今"),
    ("革锅", "革命"),
    ("肉心", "内心"),
    ("这几平", "这几乎"),
    ("新廊", "新闻"),
    ("白私", "自私"),
    ("党韵", "党的"),
    ("延自韵脚", "砸自己的脚"),
    ("害馆", "害怕"),
    ("言诊", "言论"),
    ("一带路", "一带一路"),
)


def _cjk_count(text: str) -> int:
    return len(_CJK.findall(text))


def _logo_like(text: str, cutoff: float = 0.5) -> bool:
    """与任一已知台标/标识足够相似，就算台标变体。"""
    s = text.upper().replace(" ", "")
    for mark in WATERMARKS:
        m = mark.upper().replace(" ", "")
        if difflib.SequenceMatcher(None, s, m).ratio() >= cutoff:
            return True
    return False


def clean_text(line: str, min_cjk: int = 3):
    """返回清洗后的文案；不达标返回 None。

    min_cjk: 至少包含几个汉字。碎成 1-2 个字的行基本是台标残片。
    """
    text = line.strip()
    if not text or text in MANUAL_JUNK:
        return None

    if any(pattern.search(text) for pattern in _UI_PATTERNS):
        return None

    n_cjk = _cjk_count(text)
    if n_cjk == 0:
        # 纯英文/数字：只留像台词的句子（至少 3 个词），其余视为台标噪声
        return text if len(text.split()) >= 3 and not _logo_like(text) else None

    if n_cjk < min_cjk or _logo_like(text):
        return None

    for wrong, right in TYPO_FIXES:
        text = text.replace(wrong, right)
    return text
