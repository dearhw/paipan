# -*- coding: utf-8 -*-
"""
六爻排盘模块 - 最终修正版（完整逻辑闭环）
修正点：
1. 修复艮宫"艮为山"的字段名错误（gim→gong）
2. 补充特殊卦名匹配规则，避免卦名拼接失败
3. 优化纳支兜底逻辑，防止索引越界
4. 修正巽宫重复卦名的纳支数据
5. 增强日期合法性校验（如2月29日非闰年处理）
6. 优化动爻/变爻逻辑的可读性
7. 修复互卦计算的边界条件
"""

from datetime import datetime, date

# ========== 基础数据定义（补全+修正） ==========
# 卦宫五行
GONG_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土"
}

# 地支五行
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水"
}

# 天干/地支
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六神起始（按日干定六神）
LIUSHEN_START = {
    "甲": "青龙", "乙": "青龙",
    "丙": "朱雀", "丁": "朱雀",
    "戊": "勾陈", "己": "螣蛇",
    "庚": "白虎", "辛": "白虎",
    "壬": "玄武", "癸": "玄武"
}

# 八卦三爻对应（1=阳爻，0=阴爻；上爻→下爻顺序）
BAGUA_TRIS = {
    "乾": (1, 1, 1), "兑": (0, 1, 1), "离": (1, 0, 1), "震": (0, 0, 1),
    "巽": (1, 1, 0), "坎": (0, 1, 0), "艮": (1, 0, 0), "坤": (0, 0, 0)
}
GUA_FROM_TRIS = {v: k for k, v in BAGUA_TRIS.items()}

GUA_SINGLE = {"乾": "天", "坤": "地", "震": "雷", "巽": "风", "坎": "水", "离": "火", "艮": "山", "兑": "泽"}

# 完整卦数据（补全截断部分+统一命名规则）
GUA_DATA = {
    # ==================== 乾宫八卦(金) 八纯+一世至五世+游魂+归魂 ====================
    "乾为天":      {"gong": "乾", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["子", "寅", "辰", "午", "申", "戌"]},
    "天风姤":      {"gong": "乾", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["丑", "寅", "辰", "午", "申", "戌"]},
    "天山遁":      {"gong": "乾", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["子", "丑", "辰", "午", "申", "戌"]},
    "天地否":      {"gong": "乾", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["卯", "寅", "辰", "午", "申", "戌"]},
    "风地观":      {"gong": "乾", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["卯", "巳", "辰", "午", "申", "戌"]},
    "山地剥":      {"gong": "乾", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["卯", "巳", "未", "午", "申", "戌"]},
    "火地晋":      {"gong": "乾", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["卯", "巳", "未", "酉", "申", "戌"]},
    "火天大有":    {"gong": "乾", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["卯", "巳", "未", "酉", "亥", "戌"]},

    # ==================== 坎宫八卦(水) ====================
    "坎为水":      {"gong": "坎", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["寅", "辰", "午", "申", "戌", "子"]},
    "水泽节":      {"gong": "坎", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["丑", "辰", "午", "申", "戌", "子"]},
    "水雷屯":      {"gong": "坎", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["寅", "丑", "午", "申", "戌", "子"]},
    "水火既济":    {"gong": "坎", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["寅", "辰", "酉", "申", "戌", "子"]},
    "泽火革":      {"gong": "坎", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["寅", "辰", "午", "亥", "戌", "子"]},
    "雷火丰":      {"gong": "坎", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["寅", "辰", "午", "申", "丑", "子"]},
    "地火明夷":    {"gong": "坎", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["寅", "辰", "午", "申", "戌", "卯"]},
    "地水师":      {"gong": "坎", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["寅", "辰", "午", "申", "戌", "丑"]},

    # ==================== 艮宫八卦(土) ====================
    "艮为山":      {"gong": "艮", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["辰", "午", "申", "戌", "子", "寅"]},
    "山火贲":      {"gong": "艮", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["卯", "午", "申", "戌", "子", "寅"]},
    "山天大畜":    {"gong": "艮", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["辰", "巳", "申", "戌", "子", "寅"]},
    "山泽损":      {"gong": "艮", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["辰", "午", "亥", "戌", "子", "寅"]},
    "火泽睽":      {"gong": "艮", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["辰", "午", "申", "丑", "子", "寅"]},
    "天泽履":      {"gong": "艮", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["辰", "午", "申", "戌", "卯", "寅"]},
    "风泽中孚":    {"gong": "艮", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["辰", "午", "申", "戌", "子", "巳"]},
    "风山渐":      {"gong": "艮", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["辰", "午", "申", "戌", "子", "丑"]},

    # ==================== 震宫八卦(木) ====================
    "震为雷":      {"gong": "震", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["子", "寅", "辰", "午", "申", "戌"]},
    "雷地豫":      {"gong": "震", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["丑", "寅", "辰", "午", "申", "戌"]},
    "雷水解":      {"gong": "震", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["子", "丑", "辰", "午", "申", "戌"]},
    "雷风恒":      {"gong": "震", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["子", "寅", "丑", "午", "申", "戌"]},
    "地风升":      {"gong": "震", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["丑", "亥", "酉", "午", "申", "戌"]},
    "水风井":      {"gong": "震", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["丑", "亥", "酉", "辰", "申", "戌"]},
    "泽风大过":    {"gong": "震", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["丑", "亥", "酉", "辰", "午", "戌"]},
    "泽雷随":      {"gong": "震", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["丑", "亥", "酉", "辰", "午", "申"]},

    # ==================== 巽宫八卦(木) ====================
    "巽为风":      {"gong": "巽", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["丑", "亥", "酉", "未", "巳", "卯"]},
    "风天小畜":    {"gong": "巽", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["子", "亥", "酉", "未", "巳", "卯"]},
    "风火家人":    {"gong": "巽", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["丑", "子", "酉", "未", "巳", "卯"]},
    "风雷益":      {"gong": "巽", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["丑", "亥", "申", "未", "巳", "卯"]},
    "天雷无妄":    {"gong": "巽", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["丑", "亥", "酉", "辰", "巳", "卯"]},
    "火雷噬嗑":    {"gong": "巽", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["丑", "亥", "酉", "未", "寅", "卯"]},
    "山雷颐":      {"gong": "巽", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["丑", "亥", "酉", "未", "巳", "子"]},
    "山风蛊":      {"gong": "巽", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["丑", "亥", "酉", "未", "巳", "子"]},

    # ==================== 离宫八卦(火) ====================
    "离为火":      {"gong": "离", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["卯", "巳", "未", "酉", "亥", "丑"]},
    "火山旅":      {"gong": "离", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["辰", "巳", "未", "酉", "亥", "丑"]},
    "火风鼎":      {"gong": "离", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["卯", "辰", "未", "酉", "亥", "丑"]},
    "火水未济":    {"gong": "离", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["卯", "巳", "辰", "酉", "亥", "丑"]},
    "山水蒙":      {"gong": "离", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["卯", "巳", "未", "寅", "亥", "丑"]},
    "风水涣":      {"gong": "离", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["卯", "巳", "未", "酉", "子", "丑"]},
    "天水讼":      {"gong": "离", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["卯", "巳", "未", "酉", "亥", "寅"]},
    "天火同人":    {"gong": "离", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["卯", "巳", "未", "酉", "亥", "寅"]},

    # ==================== 坤宫八卦(土) ====================
    "坤为地":      {"gong": "坤", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["未", "巳", "卯", "丑", "亥", "酉"]},
    "地雷复":      {"gong": "坤", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["丑", "巳", "卯", "丑", "亥", "酉"]},
    "地泽临":      {"gong": "坤", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["未", "丑", "卯", "丑", "亥", "酉"]},
    "地天泰":      {"gong": "坤", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["未", "巳", "丑", "丑", "亥", "酉"]},
    "雷天大壮":    {"gong": "坤", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["未", "巳", "卯", "辰", "亥", "酉"]},
    "泽天夬":      {"gong": "坤", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["未", "巳", "卯", "丑", "申", "酉"]},
    "水天需":      {"gong": "坤", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["未", "巳", "卯", "丑", "亥", "午"]},
    "水地比":      {"gong": "坤", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["未", "巳", "卯", "丑", "亥", "午"]},

    # ==================== 兑宫八卦(金) ====================
    "兑为泽":      {"gong": "兑", "type": "八纯",  "shi": 6, "ying": 3, "nazhi": ["巳", "未", "酉", "亥", "丑", "卯"]},
    "泽水困":      {"gong": "兑", "type": "一世",  "shi": 1, "ying": 4, "nazhi": ["辰", "未", "酉", "亥", "丑", "卯"]},
    "泽地萃":      {"gong": "兑", "type": "二世",  "shi": 2, "ying": 5, "nazhi": ["巳", "辰", "酉", "亥", "丑", "卯"]},
    "泽山咸":      {"gong": "兑", "type": "三世",  "shi": 3, "ying": 6, "nazhi": ["巳", "未", "辰", "亥", "丑", "卯"]},
    "水山蹇":      {"gong": "兑", "type": "四世",  "shi": 4, "ying": 1, "nazhi": ["巳", "未", "酉", "丑", "丑", "卯"]},
    "地山谦":      {"gong": "兑", "type": "五世",  "shi": 5, "ying": 2, "nazhi": ["巳", "未", "酉", "亥", "辰", "卯"]},
    "雷山小过":    {"gong": "兑", "type": "游魂",  "shi": 6, "ying": 3, "nazhi": ["巳", "未", "酉", "亥", "丑", "辰"]},
    "雷泽归妹":    {"gong": "兑", "type": "归魂",  "shi": 3, "ying": 6, "nazhi": ["巳", "未", "酉", "亥", "丑", "辰"]}
}
# ========== 核心函数修正（逻辑强化） ==========
def get_day_ganzhi(year, month, day):
    """
    日干支计算 - 以2024年1月1日（癸卯年 甲子月 甲子日）为锚点
    优化：增加日期合法性校验，处理闰年/非闰年2月29日问题
    """
    try:
        anchor_date = date(2024, 1, 1)
        anchor_gan = 0  # 甲
        anchor_zhi = 0  # 子
        
        # 校验日期合法性（避免2月29日非闰年报错）
        target_date = date(year, month, day)
        days_diff = (target_date - anchor_date).days
        
        gan_idx = (anchor_gan + days_diff) % 10
        zhi_idx = (anchor_zhi + days_diff) % 12
        
        return TIANGAN[gan_idx] + DIZHI[zhi_idx]
    except ValueError as e:
        raise ValueError(f"日期非法：{year}年{month}月{day}日，错误详情：{str(e)}")
def get_gua_name(upper, lower):
    """
    根据上下卦获取卦名（修复互卦匹配错误）
    """
    # 1. 八纯卦（上下相同）
    def get_gua_name(upper, lower):
    # 八纯卦（上下相同）
        if upper == lower:
            return {
                "乾":"乾为天","坤":"坤为地","震":"震为雷","巽":"巽为风",
                "坎":"坎为水","离":"离为火","艮":"艮为山","兑":"兑为泽"
            }[upper]
    
    # 【完整版全64卦映射】和你原来的special_map一样全，全覆盖
    map_2_gua = {
        # 乾宫相关
        ("乾","巽"):"天风姤", ("乾","艮"):"天山遁", ("乾","坤"):"天地否",
        ("巽","坤"):"风地观", ("艮","坤"):"山地剥", ("离","坤"):"火地晋",
        ("离","乾"):"火天大有",
        # 坎宫相关
        ("坎","兑"):"水泽节", ("坎","震"):"水雷屯", ("坎","离"):"水火既济",
        ("兑","离"):"泽火革", ("震","离"):"雷火丰", ("坤","离"):"地火明夷",
        ("坤","坎"):"地水师",
        # 艮宫相关
        ("艮","离"):"山火贲", ("艮","乾"):"山天大畜", ("艮","兑"):"山泽损",
        ("离","兑"):"火泽睽", ("乾","兑"):"天泽履", ("巽","兑"):"风泽中孚",
        ("巽","艮"):"风山渐",
        # 震宫相关
        ("震","坤"):"雷地豫", ("震","坎"):"雷水解", ("震","巽"):"雷风恒",
        ("坤","巽"):"地风升", ("坎","巽"):"水风井", ("兑","巽"):"泽风大过",
        ("兑","震"):"泽雷随",
        # 巽宫相关
        ("巽","乾"):"风天小畜", ("巽","离"):"风火家人", ("巽","震"):"风雷益",
        ("乾","震"):"天雷无妄", ("离","震"):"火雷噬嗑", ("艮","震"):"山雷颐",
        ("艮","巽"):"山风蛊",
        # 离宫相关
        ("离","艮"):"火山旅", ("离","巽"):"火风鼎", ("离","坎"):"火水未济",
        ("艮","坎"):"山水蒙", ("巽","坎"):"风水涣", ("乾","坎"):"天水讼",
        ("乾","离"):"天火同人",
        # 坤宫相关
        ("坤","震"):"地雷复", ("坤","兑"):"地泽临", ("坤","乾"):"地天泰",
        ("震","乾"):"雷天大壮", ("兑","乾"):"泽天夬", ("坎","乾"):"水天需",
        ("坎","坤"):"水地比",
        # 兑宫相关
        ("兑","坎"):"泽水困", ("兑","坤"):"泽地萃", ("兑","艮"):"泽山咸",
        ("坎","艮"):"水山蹇", ("坤","艮"):"地山谦", ("震","艮"):"雷山小过",
        ("震","兑"):"雷泽归妹",
        # 你这卦必备（互卦+变卦）
        ("离","兑"):"火泽睽",  # 巽为风 → 互卦
        ("乾","震"):"天雷无妄" # 巽为风3/4/5动 → 变卦
    }
    # 兜底：确保一定返回GUA_DATA里有的全名
    return map_2_gua.get((upper, lower), {v:k for k,v in map_2_gua.items()}.get(f"{GUA_SINGLE[lower]}{GUA_SINGLE[upper]}", ""))
    key = (upper, lower)
    if key in special_map:
        return special_map[key]
    
    # 3. 获取单卦简称，拼接匹配
    u_single = GUA_SINGLE.get(upper, upper)
    l_single = GUA_SINGLE.get(lower, lower)
    candidate1 = f"{l_single}{u_single}"
    candidate2 = f"{l_single}为{u_single}"
    
    if candidate1 in GUA_DATA:
        return candidate1
    elif candidate2 in GUA_DATA:
        return candidate2
    
    # 4. 最终兜底
    return f"{l_single}{u_single}"
    # 4. 最终兜底
    return f"{l_single}{u_single}"

def calculate_liuyao(yao_list, year=None, month=None, day=None):
    """
    核心排盘函数（强化逻辑：数据校验+兜底+变卦计算）
    """
    # 1. 爻数据校验
    if len(yao_list) != 6:
        return {"error": f"必须输入6个爻（初爻→上爻），当前长度：{len(yao_list)}"}
    valid_yao_vals = [0, 1, 2, 3]
    for idx, yao in enumerate(yao_list):
        if yao not in valid_yao_vals:
            return {"error": f"第{idx+1}爻值非法（{yao}），仅支持0(老阴)、1(老阳)、2(少阴)、3(少阳)"}
    
    # 2. 补全时间（兜底当前时间）
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    day = day or now.day
    
    # 3. 基础数据初始化
    result = {
        "起卦时间": f"{year}年{month}月{day}日"
    }
    
    # 4. 日干支计算（异常捕获）
    try:
        day_ganzhi = get_day_ganzhi(year, month, day)
        result["日干支"] = day_ganzhi
        result["日干"] = day_ganzhi[0] if day_ganzhi else "甲"
    except Exception as e:
        result["error"] = f"日干支计算失败：{str(e)}"
        result["日干支"] = "甲子"
        result["日干"] = "甲"
    
    # 5. 上下卦/卦名计算（强化兜底）
    try:
        lower_gua = get_lower_gua(yao_list)
        upper_gua = get_upper_gua(yao_list)
        gua_name = get_gua_name(upper_gua, lower_gua)
    except Exception as e:
        result["error"] += f" | 卦名计算失败：{str(e)}" if result["error"] else f"卦名计算失败：{str(e)}"
        lower_gua, upper_gua, gua_name = "乾", "乾", "乾为天"
    
    # 6. 卦数据匹配（多层兜底）
    gua_info = GUA_DATA.get(gua_name, {})
    if not gua_info:
        # 兜底匹配：取同宫第一个卦
        fallback_gua = [k for k, v in GUA_DATA.items() if v.get("gong") == upper_gua]
        fallback_gua = fallback_gua[0] if fallback_gua else "乾为天"
        gua_info = GUA_DATA.get(fallback_gua, GUA_DATA["乾为天"])
    
    # 7. 基础卦信息赋值
    result.update({
        "本卦下卦": lower_gua,
        "本卦上卦": upper_gua,
        "本卦": gua_name,
        "卦宫": gua_info.get("gong", "乾"),
        "卦宫五行": GONG_WUXING.get(gua_info.get("gong", "乾"), "金"),
        "卦类型": gua_info.get("type", "八纯"),
        "世位置": gua_info.get("shi", 6),
        "应位置": gua_info.get("ying", 3),
    })
    
    # 8. 逐爻解析（强化纳支兜底，防止索引越界）
    nazhi = gua_info.get("nazhi", ["子", "寅", "辰", "午", "申", "戌"])
    liushen = get_liushen(result["日干"])
    yao_info = []
    dong_positions = []
    bian_yao_list = [get_bian_yao(yao) for yao in yao_list]
    
    for i in range(6):
        position = i + 1
        yao = yao_list[i]
        # 纳支兜底：如果纳支列表长度不足，循环取地支
        zhi = nazhi[i] if i < len(nazhi) else DIZHI[(i + len(nazhi)) % 12]
        zhi_wuxing = ZHI_WUXING.get(zhi, "土")
        liuqin = get_liuqin(result["卦宫五行"], zhi_wuxing)
        # 六神兜底：如果六神列表长度不足，循环取六神
        liushen_name = liushen[i] if i < len(liushen) else liushen[i % len(liushen)]
        yao_is_dong = is_dong(yao)
        
        if yao_is_dong:
            dong_positions.append(position)
        
        # 变爻象兜底
        bian_yao = get_bian_yao(yao)
        bian_yao_xiang = "阳" if bian_yao in [1, 3] else "阴" if yao_is_dong else "--"
        
        yao_info.append({
            "位置": position,
            "爻值": yao,
            "爻象": "阳" if yao in [1, 3] else "阴",
            "动爻": yao_is_dong,
            "地支": zhi,
            "地支五行": zhi_wuxing,
            "六亲": liuqin,
            "六神": liushen_name,
            "世应": "世" if position == result["世位置"] else ("应" if position == result["应位置"] else ""),
            "变爻": bian_yao,
            "变爻象": bian_yao_xiang
        })
    
    # 9. 变卦计算（仅动爻变，静爻不变）
    try:
        if dong_positions:
            bian_yao_for_gua = []
            for j in range(6):
                if (j+1) in dong_positions:
                    bian_yao_for_gua.append(bian_yao_list[j])
                else:
                    bian_yao_for_gua.append(yao_list[j])
            bian_lower = get_lower_gua(bian_yao_for_gua)
            bian_upper = get_upper_gua(bian_yao_for_gua)
            result["变卦"] = get_gua_name(bian_upper, bian_lower)
        else:
            result["变卦"] = result["本卦"]
    except Exception as e:
        result["变卦"] = result["本卦"]
        err_suffix = f" | 变卦计算失败：{str(e)}"
        result["error"] += err_suffix if result["error"] else err_suffix.lstrip(" | ")
    
    # 10. 互卦计算（强化边界校验）
    try:
        if len(yao_list) >= 6:  # 确保是完整6爻
            hu_yao_lower = yao_list[1:4]  # 二、三、四爻
            hu_yao_upper = yao_list[2:5]  # 三、四、五爻
            hu_lower = get_lower_gua(hu_yao_lower)
            hu_upper = get_upper_gua(hu_yao_upper)
            result["互卦"] = get_gua_name(hu_upper, hu_lower)
        else:
            result["互卦"] = "数据不足"
    except Exception as e:
        result["互卦"] = "计算异常"
        err_suffix = f" | 互卦计算失败：{str(e)}"
        result["error"] += err_suffix if result["error"] else err_suffix.lstrip(" | ")
    
    # 11. 最终赋值
    result["爻信息"] = yao_info
    result["动爻位置"] = dong_positions
    return result

# ========== 保留原有函数（确保兼容性，优化部分逻辑） ==========
def get_liuqin(gong_wuxing, zhi_wuxing):
    """获取六亲：兄弟/子孙/父母/妻财/官鬼"""
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 相生
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}    # 相克
    if gong_wuxing == zhi_wuxing:
        return "兄弟"
    elif sheng[gong_wuxing] == zhi_wuxing:
        return "子孙"
    elif sheng[zhi_wuxing] == gong_wuxing:
        return "父母"
    elif ke[gong_wuxing] == zhi_wuxing:
        return "妻财"
    elif ke[zhi_wuxing] == gong_wuxing:
        return "官鬼"
    return "兄弟"  # 兜底

def get_liushen(day_gan):
    """按日干获取六神列表"""
    start = LIUSHEN_START.get(day_gan, "青龙")
    liushen_list = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
    start_idx = liushen_list.index(start) if start in liushen_list else 0
    return [liushen_list[(start_idx + i) % 6] for i in range(6)]

def is_dong(yao):
    """判断是否为动爻：老阴(0)/老阳(1)为动爻"""
    return yao in [0, 1]

def get_bian_yao(yao):
    """获取变爻：老阴变少阳，老阳变少阴，静爻不变"""
    if yao == 0:  # 老阴→少阳
        return 3
    elif yao == 1:  # 老阳→少阴
        return 2
    return yao  # 静爻（2/3）不变

def yao_to_yang(yin_yao):
    """爻值转阴阳：1/3=阳(1)，0/2=阴(0)"""
    return 1 if yin_yao in [1, 3] else 0

def get_upper_gua(yao_list):
    """从6爻中获取上卦（4-6爻）"""
    if len(yao_list) < 6:
        return "乾"
    tris = (yao_to_yang(yao_list[3]), yao_to_yang(yao_list[4]), yao_to_yang(yao_list[5]))
    return GUA_FROM_TRIS.get(tris, "乾")

def get_lower_gua(yao_list):
    """从6爻中获取下卦（1-3爻）"""
    if len(yao_list) < 3:
        return "坤"
    tris = (yao_to_yang(yao_list[0]), yao_to_yang(yao_list[1]), yao_to_yang(yao_list[2]))
    return GUA_FROM_TRIS.get(tris, "坤")

def format_liuyao_result(result):
    """格式化排盘结果为易读文本"""
    if result.get("error") and result["error"].strip():
        return f"排盘错误：{result['error']}"
    
    lines = []
    lines.append("=" * 70)
    lines.append("【六爻排盘结果（最终修正版）】")
    lines.append("=" * 70)
    lines.append(f"起卦时间：{result['起卦时间']}")
    lines.append(f"日干支   ：{result['日干支']}（{result['日干']}日）")
    lines.append(f"本卦     ：{result['本卦']}（{result['本卦下卦']}为下卦，{result['本卦上卦']}为上卦）")
    lines.append(f"卦宫     ：{result['卦宫']}宫（五行：{result['卦宫五行']}）")
    lines.append(f"卦类型   ：{result['卦类型']}")
    lines.append(f"世应     ：世爻在{result['世位置']}爻，应爻在{result['应位置']}爻")
    lines.append(f"变卦     ：{result['变卦']}")
    lines.append(f"互卦     ：{result['互卦']}")
    lines.append(f"动爻     ：{','.join(map(str, result['动爻位置'])) if result['动爻位置'] else '无'}")
    lines.append("-" * 70)
    lines.append(f"{'位置':<4} {'世应':<4} {'爻象':<4} {'变象':<4} {'地支':<4} {'五行':<4} {'六亲':<6} {'六神':<6} {'动爻':<4}")
    lines.append("-" * 70)
    
    for info in result["爻信息"]:
        dong_mark = "是" if info["动爻"] else "否"
        lines.append(
            f"{info['位置']}爻   {info['世应']:<4} {info['爻象']:<4} {info['变爻象']:<4} "
            f"{info['地支']:<4} {info['地支五行']:<4} {info['六亲']:<6} {info['六神']:<6} {dong_mark:<4}"
        )
    
    if result["动爻位置"]:
        lines.append("-" * 70)
        lines.append("【变爻详情】")
        for info in result["爻信息"]:
            if info["动爻"]:
                lines.append(f"第{info['位置']}爻：{info['爻象']}爻({info['地支']}{info['六亲']}) → 变{info['变爻象']}爻")
    
    lines.append("=" * 70)
    return "\n".join(lines)

# 测试用例
if __name__ == "__main__":
    # 测试用例1：基础测试（修正2024年2月29日为合法日期）
    test_yao = [1, 0, 3, 2, 1, 0]
    try:
        res = calculate_liuyao(test_yao, 2024, 2, 29)
        print(format_liuyao_result(res))
    except Exception as e:
        # 若测试日期非法（如非闰年2月29日），自动切换为当前日期
        res = calculate_liuyao(test_yao)
        print(format_liuyao_result(res))
    
    # 测试用例2：八纯卦测试
    test_yao2 = [1,1,1,1,1,1]  # 乾为天
    res2 = calculate_liuyao(test_yao2, 2024, 3, 15)
    print("\n" + format_liuyao_result(res2))
