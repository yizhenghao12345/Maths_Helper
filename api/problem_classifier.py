import re


GEOMETRY_KEYWORDS = [
    "三角形",
    "圆",
    "正方形",
    "长方形",
    "平行四边形",
    "梯形",
    "等腰梯形",
    "菱形",
    "扇形",
    "面积",
    "周长",
    "角度",
    "对角线",
    "高",
    "底边",
    "上底",
    "下底",
    "弧",
    "半径",
    "直径",
    "边长",
]

EQUATION_KEYWORDS = [
    "方程",
    "解方程",
    "未知数",
    "一次方程",
    "二次方程",
    "二元一次",
]


def detect_problem_type(problem: str) -> str:
    text = (problem or "").replace(" ", "")

    geometry_score = sum(1 for keyword in GEOMETRY_KEYWORDS if keyword in text)
    equation_score = sum(1 for keyword in EQUATION_KEYWORDS if keyword in text)

    # 只有当出现明显“字母未知数 + 等式”结构时，才按方程题处理。
    has_equation_pattern = bool(
        re.search(r"[a-zA-Z]\s*(?:[+\-*/]\s*\d+|\d*\s*[a-zA-Z])?.*=", text)
        or re.search(r"=\s*[a-zA-Z]", text)
        or re.search(r"求\s*[a-zA-Z]", text)
    )

    if geometry_score > 0 and geometry_score >= equation_score:
        return "geometry"

    if equation_score > 0 or has_equation_pattern:
        return "equation"

    return "general"
