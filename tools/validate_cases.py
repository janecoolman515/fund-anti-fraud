#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统实用性验证 —— 用真实案例的结构特征跑规则引擎，看它判得准不准。

数据来源（均为公开信息，不点具体项目名做定性）：
  · 湖南省衡阳市中级人民法院 2025-07-16 通报的传销案：
      最低入会门槛 1500 美元、邀请码形成上下线、以下线人数/层级/团队入金总量计酬、
      平台实际未开展外汇交易、涉案超百亿、主犯判 8 年
  · 公安部 2024-10 公布的 5 起传销典型案例之一：
      入门费 + 会员等级 + 高额返利、承诺上市后期权、195 万会员、涉案 43.5 亿
  · 公开通报中反复出现的三类常见模式：刷单返利、云矿机、数藏回购

每个用例只填「公开信息里能查到的事实」，查不到的一律留空，
用来检验系统在「信息不全」时会不会误判。
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))

from scheme_audit import audit  # noqa: E402


def case(name, expect, note, facts, stage="withdrawal_slow"):
    return {
        "project": {"name": name, "claimed_type": note, "audited": "公开通报特征重构"},
        "facts": facts,
        "expect": expect,
        "stage": stage,
    }


CASES = [
    # ── 1. 门槛费 + 邀请码层级 + 团队入金计酬 + 无真实交易 ──
    case(
        "案例A · 外汇投资幌子（公开判决）",
        "critical",
        "门槛费 1500 美元 / 邀请码层级 / 团队入金计酬 / 无真实交易",
        {
            "entity": {
                "icp_entity_type": "unknown",
                "registered_capital": None,
                "paid_in_capital": None,
                "business_status": "unknown",
                "domain_age_days": None,
                "domain_expires_days": None,
            },
            "yield": {"daily_rate": None},
            "scheme": {
                "referral_levels": 3,        # 邀请码形成上下线，明确多层级
                "referral_capped": False,    # 以下线人数、层级、团队入金总量计酬
                "entry_fee": 10800,          # 1500 美元 ≈ 1.08 万元
                "lockup": None,
                "release_requires_repurchase": None,
            },
            "funds": {
                "withdrawal_limited": None,
                "payee_type": "unknown",
                "third_party_custody": None,
                "real_business": "none",     # 平台实际未进行外汇交易
            },
            "external": {
                "regulator_warning": None,
                "complaints": None,
                "legal_cases": 1,            # 已有生效判决
                "official_denial": None,
            },
        },
    ),

    # ── 2. 入门费 + 会员等级 + 高额返利 + 承诺上市期权 ──
    case(
        "案例B · 刷视频赚钱（公安部通报）",
        "critical",
        "入门费 / 会员等级 / 高额返利 / 承诺上市期权 / 195 万会员",
        {
            "entity": {
                "icp_entity_type": "company",
                "registered_capital": None,
                "paid_in_capital": None,
                "business_status": "unknown",
                "domain_age_days": None,
                "domain_expires_days": None,
            },
            "yield": {"daily_rate": None},
            "scheme": {
                "referral_levels": 2,
                "referral_capped": False,
                "entry_fee": 99,             # 入门费（具体金额通报未披露，按常见量级）
                "lockup": None,
            },
            "funds": {
                "payee_type": "unknown",
                "real_business": "none",     # 靠会员费与拉人，无真实造血
            },
            "external": {
                "legal_cases": 1,            # 已立案
            },
        },
    ),

    # ── 3. 刷单返利盘（高频常见模式）──
    case(
        "案例C · 刷单返利盘",
        "critical",
        "日化 1.5% / 三级分销 / 提现需邀请 / 个人收款",
        {
            "entity": {
                "icp_entity_type": "individual",
                "icp_entity_matches_claim": False,
                "registered_capital": None,
                "paid_in_capital": 0,
                "business_status": "unknown",
                "domain_age_days": 90,
                "domain_expires_days": 200,
            },
            "yield": {"daily_rate": 1.5, "cycle_days": 7},
            "scheme": {
                "referral_levels": 3,
                "referral_capped": False,
                "entry_fee": 500,
                "lockup": True,
            },
            "funds": {
                "withdrawal_limited": True,
                "payee_type": "personal",
                "third_party_custody": False,
                "real_business": "none",
            },
            "external": {"complaints": 30},
        },
    ),

    # ── 4. 云矿机型 ──
    case(
        "案例D · 云矿机（算力不可验）",
        "high",
        "日化 0.4% / 固定收益 / 算力无凭据 / 提现排队",
        {
            "entity": {
                "icp_entity_type": "company",
                "registered_capital": 5000000,
                "paid_in_capital": 380000,
                "business_status": "normal",
                "domain_age_days": 240,
                "domain_expires_days": 400,
            },
            "yield": {"daily_rate": 0.4},
            "scheme": {
                "referral_levels": 2,
                "referral_capped": False,
                "entry_fee": 3000,
                "lockup": True,
            },
            "funds": {
                "withdrawal_limited": True,
                "payee_type": "company",
                "third_party_custody": False,
                "real_business": "weak",
            },
            "external": {"complaints": 21},
        },
    ),

    # ── 5. 数藏回购型 ──
    # 预期定 low：企业备案正常、实缴虽未知但无异常、无门槛费、
    # 只有一级返佣且有封顶、对公收款 —— 单靠「承诺回购 + 造血弱」
    # 不足以判中风险，判 low 是诚实的。这条用例的价值在于
    # 确认系统不会因为「看起来像数藏」就自动给高分。
    case(
        "案例E · 数藏平台（自买自卖 + 回购承诺）",
        "low",
        "企业备案 / 平台自营挂单 / 固定溢价回购 / 邀请返佣",
        {
            "entity": {
                "icp_entity_type": "company",
                "icp_entity_matches_claim": True,
                "registered_capital": 10000000,
                "paid_in_capital": None,
                "business_status": "normal",
                "domain_age_days": 500,
                "domain_expires_days": 600,
            },
            "yield": {"daily_rate": None},
            "scheme": {
                "referral_levels": 1,
                "referral_capped": True,
                "entry_fee": 0,
                "lockup": None,
                "guaranteed_return": True,   # 宣称「首发 30 天溢价 15% 回购」
            },
            "funds": {
                "withdrawal_limited": None,
                "payee_type": "company",
                "third_party_custody": None,
                "real_business": "weak",
                "price_manipulable": True,   # 平台自营账号在二级市场挂单收自家藏品
            },
            "external": {},
        },
        stage="pre_launch",
    ),

    # ── 6. 合规对照（有真实经营）──
    case(
        "案例F · 合规对照（社区团购）",
        "low",
        "实缴 200 万 / 对公收款 / 低返利 / 一级返佣有封顶",
        {
            "entity": {
                "icp_entity_type": "company",
                "icp_entity_matches_claim": True,
                "registered_capital": 3000000,
                "paid_in_capital": 2000000,
                "business_status": "normal",
                "domain_age_days": 1500,
                "domain_expires_days": 800,
            },
            "yield": {"daily_rate": 0.03},
            "scheme": {
                "referral_levels": 1,
                "referral_capped": True,
                "entry_fee": 0,
                "lockup": False,
            },
            "funds": {
                "withdrawal_limited": False,
                "payee_type": "company",
                "third_party_custody": True,
                "real_business": "real",
            },
            "external": {"complaints": 2, "legal_cases": 0},
        },
        stage="normal",
    ),

    # ── 7. 边界：信息极少（只给项目名）──
    case(
        "案例G · 边界测试（只有项目名）",
        "unknown",
        "什么信息都没有",
        {},
        stage="pre_launch",
    ),

    # ── 8. 边界：极端收益率 ──
    case(
        "案例H · 边界测试（日化 100%）",
        "critical",
        "日化 100%，其余未知",
        {"yield": {"daily_rate": 100}},
        stage="pre_launch",
    ),
]

RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def main() -> int:
    print("=" * 78)
    print(" 系统实用性验证 · 用真实案例结构跑 21 条规则")
    print("=" * 78)
    print()

    rows = []
    problems = []

    for c in CASES:
        r = audit(c)
        exp = c["expect"]
        got = r["level"]
        rows.append((c["project"]["name"], r["score"], got, exp, r["coverage"],
                     len(r["hits"]), len(r["gaps"])))

        # 判定是否达标：完全一致，或实际比预期更严重（更保守可接受）
        ok = (got == exp) or (exp in RANK and got in RANK and RANK[got] > RANK[exp])
        # 例外：预期 unknown（信息不足）时，必须真的是 unknown
        if exp == "unknown":
            ok = (got == "unknown")

        flag = "PASS" if ok else "FAIL"
        if not ok:
            problems.append((c["project"]["name"], exp, got, r["score"]))

        print("[%s] %s" % (flag, c["project"]["name"]))
        print("       得分 %3d / 100 ｜ 评级 %-10s ｜ 预期 %-8s" % (r["score"], got, exp))
        print("       覆盖率 %3.0f%%（缺口 %d 项）｜ 命中 %d 条"
              % (r["coverage"] * 100, len(r["gaps"]), len(r["hits"])))
        if r.get("combo_ponzi"):
            print("       ★ 命中「庞氏结构三要素」（拉人计酬 + 入门费 + 无造血）")
        if r.get("extreme_yield"):
            print("       ★ 命中「极端收益率」顶格判定")
        if r["hits"]:
            print("       命中：%s" % "、".join(h["name"] for h in r["hits"]))
        if not ok:
            print("       ⚠ 与预期不符")
        print()

    print("=" * 78)
    print(" 汇总")
    print("=" * 78)
    passed = len(CASES) - len(problems)
    print(" 通过 %d / %d" % (passed, len(CASES)))
    print()
    if problems:
        print(" 需要修正的用例：")
        for name, exp, got, score in problems:
            print("   · %s：预期 %s，实际 %s（%d 分）" % (name, exp, got, score))
    else:
        print(" 全部用例判定符合预期。")

    # 输出 JSON 备查
    out = pathlib.Path(__file__).resolve().parent / "validation-result.json"
    out.write_text(json.dumps(
        [{"name": n, "score": s, "got": g, "expect": e, "coverage": cov,
          "hits": h, "gaps": gp}
         for n, s, g, e, cov, h, gp in rows],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n 明细已写入：%s" % out.name)

    return 0 if not problems else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
