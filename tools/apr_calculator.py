#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收益模型反算器 —— 把一个项目宣称的收益率，换算成它必须满足的现实条件。

核心逻辑：任何承诺收益率 R 的项目，若没有真实经营产生现金流，
则每年必须从新资金里拿出 R 倍存量资金来兑付。这个缺口就是庞氏缺口。

用法：
    python apr_calculator.py --daily 1.8
    python apr_calculator.py --daily 1.8 --cycle 7 --principal 10000
    python apr_calculator.py --monthly 30 --principal 50000
    python apr_calculator.py --daily 0.5 --members 1000 --avg 10000
    python apr_calculator.py --daily 1.8 --json

参数：
    --daily      日化收益率（百分数，1.8 表示 1.8%）
    --monthly    月化收益率（百分数）
    --annual     年化收益率（百分数）
    --cycle      静态周期天数（多少天回本，用于交叉验证）
    --principal  单笔投资额（元）
    --members    当前会员数（用于缺口测算）
    --avg        人均投资额（元，默认等于 principal）
    --json       以 JSON 输出

退出码：0 正常 · 2 参数错误
"""
from __future__ import annotations

import argparse
import json
import sys

# 司法保护上限：一年期 LPR 的 4 倍。2024 年后 LPR 约 3.1%~3.45%，取 3.45% × 4 ≈ 13.8%
LPR = 0.0345
LEGAL_CAP_ANNUAL = LPR * 4


def to_daily(daily=None, monthly=None, annual=None) -> float:
    if daily is not None:
        return daily / 100.0
    if monthly is not None:
        return (1 + monthly / 100.0) ** (1 / 30.0) - 1
    if annual is not None:
        return (1 + annual / 100.0) ** (1 / 365.0) - 1
    raise ValueError("必须提供 --daily / --monthly / --annual 之一")


def analyze(d: float, cycle=None, principal=None, members=None, avg=None) -> dict:
    simple_annual = d * 365
    compound_annual = (1 + d) ** 365 - 1
    payback_days = 1 / d if d > 0 else float("inf")

    r: dict = {
        "daily_rate": d,
        "daily_pct": d * 100,
        "simple_annual": simple_annual,
        "compound_annual": compound_annual,
        "payback_days": payback_days,
        "legal_cap_annual": LEGAL_CAP_ANNUAL,
        "multiple_of_legal_cap": compound_annual / LEGAL_CAP_ANNUAL if LEGAL_CAP_ANNUAL else None,
        "verdicts": [],
    }

    # —— 判定 ——
    v = r["verdicts"]
    if d >= 0.01:
        v.append(("critical", "日化 ≥ 1%%：年化约 %.0f 倍，任何实体经营都无法支撑，"
                              "属典型庞氏收益率" % (compound_annual + 1)))
    elif d >= 0.003:
        v.append(("critical", "日化 ≥ 0.3%%：年化约 %.1f 倍，远超司法保护上限（%.1f%%）"
                              % (compound_annual + 1, LEGAL_CAP_ANNUAL * 100)))
    elif d >= 0.001:
        v.append(("high", "日化 ≥ 0.1%%：年化 %.1f%%，已超出民间借贷司法保护上限（%.1f%%）"
                          % (compound_annual * 100, LEGAL_CAP_ANNUAL * 100)))
    else:
        v.append(("low", "日化 %.3f%%：年化 %.1f%%，处于常规理财区间，"
                         "需进一步核查收益来源" % (d * 100, compound_annual * 100)))

    if cycle:
        implied = 100.0 / cycle  # 按周期折算的日化
        gap = abs(implied - d * 100)
        r["cycle_check"] = {
            "declared_cycle_days": cycle,
            "implied_daily_pct": implied,
            "actual_daily_pct": d * 100,
            "deviation_pct": gap,
            "consistent": gap <= max(0.05, implied * 0.15),
        }
        if not r["cycle_check"]["consistent"]:
            v.append(("warn", "宣称「%d 天回本」与实际日化 %.2f%% 不自洽"
                              "（按周期应为日化 %.2f%%）——制度说明本身存在矛盾"
                              % (cycle, d * 100, implied)))

    # —— 单笔测算 ——
    if principal:
        r["per_principal"] = {
            "amount": principal,
            "daily_profit": principal * d,
            "monthly_profit": principal * ((1 + d) ** 30 - 1),
            "annual_profit": principal * compound_annual,
            "payback_days": payback_days,
        }
        v.append(("info", "投 %.0f 元：日收益 %.2f 元，%d 天回本，一年后账面 %.0f 元"
                          % (principal, principal * d, round(payback_days),
                             principal * (1 + compound_annual))))

    # —— 缺口测算 ——
    if members and (avg or principal):
        per = avg or principal
        pool = members * per
        annual_payout = pool * compound_annual
        r["ponzi_gap"] = {
            "members": members,
            "avg_ticket": per,
            "capital_pool": pool,
            "annual_payout_needed": annual_payout,
            "new_members_needed_per_year": annual_payout / per,
            "new_members_needed_per_day": annual_payout / per / 365,
        }
        g = r["ponzi_gap"]
        v.append(("critical",
                  "现有 %d 人、人均 %.0f 元（资金池 %.0f 元）：一年需兑付 %.0f 元，"
                  "在没有真实经营收入的前提下，等于每天必须新增 %.0f 个"
                  "人均 %.0f 元的新会员才能不崩。这是纯数学，没有例外。"
                  % (members, per, pool, annual_payout,
                     g["new_members_needed_per_day"], per)))

    return r


def render(r: dict) -> str:
    L = []
    a = L.append
    a("=" * 66)
    a(" 收益模型反算")
    a("=" * 66)
    a("")
    a("  日化收益率          %.4f%%" % (r["daily_pct"]))
    a("  单利年化            %.2f%%" % (r["simple_annual"] * 100))
    a("  复利年化            %s" % ("%.0f 倍" % (r["compound_annual"] + 1)
                                     if r["compound_annual"] > 10
                                     else "%.1f%%" % (r["compound_annual"] * 100)))
    a("  静态回本周期        %d 天" % round(r["payback_days"]))
    a("  司法保护上限(年化)  %.1f%%（一年期 LPR %.2f%% × 4）"
      % (r["legal_cap_annual"] * 100, LPR * 100))
    if r.get("multiple_of_legal_cap"):
        a("  超出上限倍数        %.1f 倍" % r["multiple_of_legal_cap"])
    a("")

    if "cycle_check" in r:
        c = r["cycle_check"]
        a("-" * 66)
        a(" 周期自洽性检查")
        a("-" * 66)
        a("  宣称周期 %d 天  →  隐含日化 %.3f%%" % (c["declared_cycle_days"],
                                                   c["implied_daily_pct"]))
        a("  实际日化         →  %.3f%%" % c["actual_daily_pct"])
        a("  结论             →  %s" % ("自洽" if c["consistent"]
                                          else "⚠ 不自洽（偏差 %.3f 个百分点）"
                                          % c["deviation_pct"]))
        a("")

    if "per_principal" in r:
        p = r["per_principal"]
        a("-" * 66)
        a(" 单笔测算")
        a("-" * 66)
        a("  本金            %.2f 元" % p["amount"])
        a("  日收益          %.2f 元" % p["daily_profit"])
        a("  月收益          %.2f 元" % p["monthly_profit"])
        a("  年账面          %.2f 元" % (p["amount"] + p["annual_profit"]))
        a("")

    if "ponzi_gap" in r:
        g = r["ponzi_gap"]
        a("-" * 66)
        a(" 庞氏缺口测算")
        a("-" * 66)
        a("  当前会员数      %d 人" % g["members"])
        a("  人均投资额      %.2f 元" % g["avg_ticket"])
        a("  资金池          %.0f 元" % g["capital_pool"])
        a("  年需兑付        %.0f 元" % g["annual_payout_needed"])
        a("  需新增会员      %.0f 人 / 年（%.0f 人 / 天）"
          % (g["new_members_needed_per_year"], g["new_members_needed_per_day"]))
        a("")

    a("=" * 66)
    a(" 判定")
    a("=" * 66)
    tag = {"critical": "🔴", "high": "🟠", "warn": "⚠ ", "low": "🟢", "info": "  "}
    for level, msg in r["verdicts"]:
        a("%s %s" % (tag.get(level, "  "), msg))
        a("")
    a("注：以上为数学测算，不构成法律定性。收益率本身不违法，")
    a("    违法与否取决于收益来源与计酬方式，需结合制度结构综合判断。")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="收益模型反算器")
    ap.add_argument("--daily", type=float, help="日化收益率（%%）")
    ap.add_argument("--monthly", type=float, help="月化收益率（%%）")
    ap.add_argument("--annual", type=float, help="年化收益率（%%）")
    ap.add_argument("--cycle", type=int, help="静态周期天数")
    ap.add_argument("--principal", type=float, help="单笔投资额（元）")
    ap.add_argument("--members", type=int, help="当前会员数")
    ap.add_argument("--avg", type=float, help="人均投资额（元）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    try:
        d = to_daily(args.daily, args.monthly, args.annual)
    except ValueError as e:
        print("参数错误：%s" % e, file=sys.stderr)
        return 2

    if d <= 0:
        print("参数错误：收益率必须为正数", file=sys.stderr)
        return 2

    r = analyze(d, args.cycle, args.principal, args.members, args.avg)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(render(r))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
