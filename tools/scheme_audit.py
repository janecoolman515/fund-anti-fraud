#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""制度特征审查引擎 —— 把一份结构化案件事实，跑一遍规则库，输出风险分与命中特征。

设计原则：
  1. 零第三方依赖（只用标准库），输入是 JSON，任何语言都能生成。
  2. 只对「已核实的事实」计分。事实为 unknown / null 的项不计分，但记入「信息缺口」。
  3. 每条规则都对应一个可核查的客观事实，不做主观推测。
  4. 输出同时给分、给证据、给缺口 —— 让人能复核，而不是只看到一个数字。

用法：
    python scheme_audit.py examples/sample-case.json
    python scheme_audit.py examples/sample-case.json --json
    python scheme_audit.py examples/sample-case.json --explain

退出码：0 = 完成 · 2 = 输入错误
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

# ─────────────────────────────────────────────────────────────
# 规则库
# 每条：(id, 维度, 分值, 名称, 判定函数, 事实依据说明)
# 判定函数返回 True = 命中（危险）、False = 未命中、None = 信息不足
# ─────────────────────────────────────────────────────────────

DIMENSIONS = {
    "A": ("主体资质", 25),
    "B": ("收益结构", 30),
    "C": ("资金安全", 25),
    "D": ("外部信号", 20),
}


def _g(f: dict, *path, default=None):
    """安全取嵌套值。"""
    cur = f
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur if cur is not None else default


def r_icp_not_company(f):
    v = _g(f, "entity", "icp_entity_type")
    if v is None or v == "unknown":
        return None
    return v in ("individual", "sole_proprietor", "none")


def r_icp_mismatch(f):
    v = _g(f, "entity", "icp_entity_matches_claim")
    return None if v is None else (v is False)


def r_paid_in_capital(f):
    reg = _g(f, "entity", "registered_capital")
    paid = _g(f, "entity", "paid_in_capital")
    if reg is None or paid is None:
        return None
    if not reg:
        return None
    return (paid / reg) < 0.1 or paid <= 100000


def r_business_abnormal(f):
    v = _g(f, "entity", "business_status")
    if v is None or v == "unknown":
        return None
    return v in ("abnormal", "revoked", "cancelled", "unreachable")


def r_domain_young_or_expiring(f):
    age = _g(f, "entity", "domain_age_days")
    exp = _g(f, "entity", "domain_expires_days")
    if age is None and exp is None:
        return None
    if age is not None and age < 365:
        return True
    if exp is not None and exp < 180:
        return True
    return False


def r_high_yield(f):
    d = _g(f, "yield", "daily_rate")
    if d is None:
        m = _g(f, "yield", "monthly_rate")
        if m is None:
            return None
        d = (1 + m / 100.0) ** (1 / 30.0) * 100 - 100
    return d >= 1.0


def r_mid_yield(f):
    d = _g(f, "yield", "daily_rate")
    if d is None:
        return None
    return 0.1 <= d < 1.0


def r_referral(f):
    lv = _g(f, "scheme", "referral_levels")
    if lv is None:
        return None
    capped = _g(f, "scheme", "referral_capped", default=False)
    return lv >= 1 and not capped


def r_entry_fee(f):
    v = _g(f, "scheme", "entry_fee")
    if v is None:
        return None
    return v > 0


def r_lockup(f):
    v = _g(f, "scheme", "lockup")
    repurchase = _g(f, "scheme", "release_requires_repurchase", default=False)
    if v is None and repurchase is None:
        return None
    return bool(v) or bool(repurchase)


def r_withdrawal_limited(f):
    v = _g(f, "funds", "withdrawal_limited")
    return None if v is None else bool(v)


def r_personal_payee(f):
    v = _g(f, "funds", "payee_type")
    if v is None or v == "unknown":
        return None
    return v == "personal"


def r_no_custody(f):
    v = _g(f, "funds", "third_party_custody")
    return None if v is None else (v is False)


def r_no_real_business(f):
    v = _g(f, "funds", "real_business")
    if v is None or v == "unknown":
        return None
    return v in ("none", "weak")


def r_regulator(f):
    v = _g(f, "external", "regulator_warning")
    return None if v is None else bool(v)


def r_complaints(f):
    n = _g(f, "external", "complaints")
    if n is None:
        return None
    return n >= 10


def r_legal(f):
    n = _g(f, "external", "legal_cases")
    if n is None:
        return None
    return n > 0


def r_official_denial(f):
    v = _g(f, "external", "official_denial")
    return None if v is None else bool(v)


def r_guaranteed_return(f):
    """承诺保本 / 固定回报 / 到期回购 —— 变相还本付息。"""
    v = _g(f, "scheme", "guaranteed_return")
    return None if v is None else bool(v)


def r_extreme_yield(f):
    """日化 ≥ 10%：一年 1000 倍以上，属明显异常，单列一条。"""
    d = _g(f, "yield", "daily_rate")
    if d is None:
        return None
    return d >= 10.0


def r_price_manipulation(f):
    """价格可被平台操控：自买自卖抬价、后台改价、单边只涨不跌。

    数藏平台、山寨交易所的核心风险点 —— 价格不由市场形成，
    意味着账面浮盈无法兑现，随时可以被反向操作。
    """
    v = _g(f, "funds", "price_manipulable")
    return None if v is None else bool(v)


RULES = [
    # id,   维度, 分值, 名称, 判定, 依据
    ("A1", "A", 8, "备案主体非企业",
     r_icp_not_company, "ICP 备案主体为个人/个体户/无备案"),
    ("A2", "A", 4, "备案主体与宣称主体不一致",
     r_icp_mismatch, "备案主体名称与宣传中的集团/公司不对应"),
    ("A3", "A", 5, "注册资本未实缴或实缴极低",
     r_paid_in_capital, "实缴资本 < 注册资本的 10%，或 ≤ 10 万元"),
    ("A4", "A", 6, "工商状态异常",
     r_business_abnormal, "经营异常 / 注销 / 吊销 / 地址无法联系"),
    ("A5", "A", 6, "域名新注册或即将到期",
     r_domain_young_or_expiring, "域名注册 < 1 年，或到期 < 180 天"),

    ("B1", "B", 12, "日化收益率 ≥ 1%",
     r_high_yield, "日化 ≥ 1%（年化约 37 倍以上），无实体经营可支撑"),
    ("B2", "B", 6, "日化收益率 0.1%~1%",
     r_mid_yield, "日化 0.1%~1%，超出民间借贷司法保护上限"),
    ("B3", "B", 8, "存在推荐奖层级且无封顶",
     r_referral, "直推/间推/团队奖 ≥ 1 代且无封顶，属拉人计酬"),
    ("B4", "B", 5, "存在入门门槛费",
     r_entry_fee, "需缴纳激活费/会员费/购买指定产品才能参与"),
    ("B5", "B", 5, "锁仓或释放需复投",
     r_lockup, "本金锁仓，或解锁释放需再次购入"),
    ("B6", "B", 6, "承诺保本 / 固定回报 / 回购",
     r_guaranteed_return, "宣称保本、固定收益、到期溢价回购 —— 变相还本付息"),
    ("B7", "B", 8, "日化收益率 ≥ 10%（极端）",
     r_extreme_yield, "日化 ≥ 10%，一年 1000 倍以上，无任何实体经营可支撑"),

    ("C1", "C", 10, "提现受限",
     r_withdrawal_limited, "限额 / 排队 / 手续费畸高 / 改积分代金券"),
    ("C2", "C", 6, "收款方为个人账户",
     r_personal_payee, "充值收款码/收款账户为个人"),
    ("C3", "C", 5, "无第三方资金存管",
     r_no_custody, "资金直接进入平台自有账户，无银行/持牌机构存管"),
    ("C4", "C", 4, "无真实造血业务",
     r_no_real_business, "未发现可对上账的实体经营收入"),
    ("C5", "C", 6, "价格可被平台操控",
     r_price_manipulation, "自买自卖抬价 / 后台改价 / 单边只涨不跌 —— 账面浮盈无法兑现"),

    ("D1", "D", 8, "监管或官方已发风险提示",
     r_regulator, "金融监管局/互金协会/公安等已公开提示"),
    ("D2", "D", 6, "投诉集中且指向同一模式",
     r_complaints, "公开投诉 ≥ 10 条且内容指向提现/跑路"),
    ("D3", "D", 6, "已有立案或司法记录",
     r_legal, "公安立案 / 检察院起诉 / 法院判决 / 被执行"),
    ("D4", "D", 4, "官方已撇清关系",
     r_official_denial, "被冒名机构发布声明否认关联"),
]


# ─────────────────────────────────────────────────────────────
def load_case(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit("找不到案件文件：%s" % path)
    except json.JSONDecodeError as e:
        raise SystemExit("JSON 格式错误：%s（第 %d 行）" % (e.msg, e.lineno))


def audit(case: dict) -> dict:
    facts = case.get("facts", {})
    hits, missed, gaps = [], [], []

    dim_score = {k: 0 for k in DIMENSIONS}
    dim_max = {k: v[1] for k, v in DIMENSIONS.items()}

    for rid, dim, weight, name, fn, basis in RULES:
        try:
            res = fn(facts)
        except Exception:  # noqa: BLE001 —— 单条规则异常不影响整体
            res = None
        if res is None:
            gaps.append({"id": rid, "name": name, "basis": basis})
        elif res:
            hits.append({"id": rid, "dim": dim, "weight": weight,
                         "name": name, "basis": basis})
            dim_score[dim] += weight
        else:
            missed.append({"id": rid, "name": name})

    # 维度封顶，避免单项堆分导致总分失真
    for k in dim_score:
        dim_score[k] = min(dim_score[k], dim_max[k])

    total = sum(dim_score.values())

    # 信息缺口惩罚：核实项不足时不出评级，防止「没查到」被当成「没问题」
    total_rules = len(RULES)
    coverage = (total_rules - len(gaps)) / total_rules

    hit_ids = {h["id"] for h in hits}

    # ── 组合判定：庞氏结构三要素 ──
    # 依据《禁止传销条例》第七条第(二)(三)项 + 刑法 224 条之一的构成描述：
    #   拉人计酬 + 入门费 + 无真实造血 → 三者同时成立，已构成资金盘/传销结构，
    #   此时不应因「未公布收益率」而降低评级。
    COMBO = {"B3", "B4", "C4"}
    combo_ponzi = COMBO.issubset(hit_ids)
    if combo_ponzi:
        total = max(total, 82)

    # ── 极端收益率直接顶格 ──
    extreme = "B7" in hit_ids
    if extreme:
        total = max(total, 80)

    # ── 评级 ──
    # 顺序很重要：分数已经顶格时，不该被「覆盖率不足」压成信息不足。
    # 命中核心违规特征本身就是结论，不需要更多信息来确认。
    if total >= 80:
        level, label = "critical", "🔴 极高风险"
        meaning = "命中多项核心违规特征，与已知资金盘/传销结构高度一致"
    elif coverage < 0.35:
        level, label = "unknown", "⚪ 信息不足"
        meaning = ("已核实项不足 35%%（%d / %d），无法形成有效评级。"
                   "这不是「没问题」，是「还不知道」" % (total_rules - len(gaps), total_rules))
    elif total >= 60:
        level, label = "high", "🟠 高风险"
        meaning = "存在多项无法解释的异常，强烈建议不参与"
    elif total >= 40:
        level, label = "medium", "🟡 中风险"
        meaning = "部分异常或信息不足，需补充核查后再判断"
    else:
        level, label = "low", "🟢 暂未发现明显违规"
        meaning = "本次核查未发现明显违规特征，但不代表安全或合法"

    return {
        "project": case.get("project", {}),
        "score": total,
        "level": level,
        "label": label,
        "meaning": meaning,
        "dimensions": {k: {"name": DIMENSIONS[k][0], "score": dim_score[k],
                           "max": dim_max[k]} for k in DIMENSIONS},
        "hits": hits,
        "missed": missed,
        "gaps": gaps,
        "coverage": round(coverage, 3),
        "combo_ponzi": combo_ponzi,
        "extreme_yield": extreme,
    }


def render(res: dict) -> str:
    p = res["project"]
    L = []
    a = L.append
    a("=" * 68)
    a(" 制度特征审查报告")
    a("=" * 68)
    a("")
    a("  项目名称    %s" % (p.get("name") or "（未填写）"))
    if p.get("aliases"):
        a("  别名/曾用名 %s" % "、".join(p["aliases"]))
    a("  宣称类型    %s" % (p.get("claimed_type") or "未填写"))
    a("  宣称收益    %s" % (p.get("claimed_yield") or "未填写"))
    a("  信息完整度  %d%%（%d / %d 项可核实）"
      % (round(res["coverage"] * 100),
         len(RULES) - len(res["gaps"]), len(RULES)))
    a("")
    a("-" * 68)
    a("  %s      总分 %d / 100" % (res["label"], res["score"]))
    a("  %s" % res["meaning"])
    a("-" * 68)
    a("")

    a("【维度得分】")
    for k, d in res["dimensions"].items():
        bar_len = int(round(d["score"] / d["max"] * 20)) if d["max"] else 0
        bar = "█" * bar_len + "░" * (20 - bar_len)
        a("  %s %-6s %s %2d/%2d" % (k, d["name"], bar, d["score"], d["max"]))
    a("")

    if res["hits"]:
        a("【命中特征】")
        for h in sorted(res["hits"], key=lambda x: (-x["weight"], x["id"])):
            a("  +%-2d [%s] %s" % (h["weight"], h["id"], h["name"]))
            a("        依据：%s" % h["basis"])
        a("")

    if res["gaps"]:
        a("【信息缺口】（未计分，需补充核查）")
        for g in res["gaps"]:
            a("  ?    [%s] %s —— %s" % (g["id"], g["name"], g["basis"]))
        a("")

    if res["missed"]:
        a("【已排除】")
        a("  -    %s" % "、".join(m["name"] for m in res["missed"]))
        a("")

    a("=" * 68)
    a(" 说明：本报告基于输入的结构化事实做特征比对，仅供风险提示，")
    a("       不构成法律意见，也不对项目性质作法律定性。")
    a("       评级为「暂未发现明显违规」时，仅表示本次核查范围内未发现，")
    a("       不代表该项目安全或合法。")
    a("=" * 68)
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="制度特征审查引擎")
    ap.add_argument("case", help="案件 JSON 文件")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--explain", action="store_true", help="额外打印规则表")
    args = ap.parse_args()

    case = load_case(pathlib.Path(args.case))
    res = audit(case)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render(res))

    if args.explain:
        print("\n【规则表】")
        for rid, dim, w, name, _, basis in RULES:
            print("  %-3s %s %2d 分  %s" % (rid, dim, w, name))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
