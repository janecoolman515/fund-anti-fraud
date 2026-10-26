#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告生成器 —— 把一份案件 JSON 渲染成可直接发布的 Markdown 风险报告。

依赖同目录的 scheme_audit.py（规则引擎）与 apr_calculator.py（收益反算），
三者都是标准库实现，无需安装任何第三方包。

用法：
    python report_builder.py examples/sample-case.json
    python report_builder.py examples/sample-case.json -o REPORT.md
    python report_builder.py examples/sample-case.json --title "【风险审查】星辰国际"

退出码：0 = 成功 · 2 = 输入错误
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from apr_calculator import analyze as apr_analyze  # noqa: E402
from scheme_audit import audit as run_audit  # noqa: E402

# ─────────────────────────────────────────────────────────────
# 阶段 → 结局推演 / 行动建议
# ─────────────────────────────────────────────────────────────

STAGES = {
    "pre_launch": {
        "label": "尚未参与",
        "outlook": "该项目尚未崩盘或尚未被广泛曝光，处于吸金扩张期。"
                   "此阶段的特征是收益按时到账、社群氛围热烈、拉人有奖——"
                   "**这些都不是安全的证据，恰恰是庞氏结构运转正常的表征**。",
        "advice": [
            "不参与。任何收益率超过司法保护上限且收益与拉人挂钩的项目，"
            "其最终结果只有「什么时候崩」，没有「会不会崩」。",
            "如果身边有人已经在推，把本报告的证据表转给他，不要只转结论。",
        ],
    },
    "normal": {
        "label": "提现尚正常",
        "outlook": "目前仍能正常提现，属于资金链尚能维持的阶段。"
                   "按同类项目的规律，这个窗口通常不会太长——一旦新增资金"
                   "跟不上承诺兑付，就会进入限额阶段。",
        "advice": [
            "**立即全额提现**，不要有「再赚一轮就走」的想法。绝大多数亏损都发生在这个念头之后。",
            "提现到账后不要再复投，也不要接受「推荐新人可加速提现」之类的条件。",
            "保存好充值记录、提现记录、制度页截图、群公告，以备后续需要。",
        ],
    },
    "withdrawal_slow": {
        "label": "提现变慢 / 限额",
        "outlook": "提现出现限额、排队、手续费畸高或改成积分代金券，"
                   "是资金链收紧的直接信号。下一步大概率会演化为"
                   "「补缴保证金解冻」或「升级会员等级才能提现」。",
        "advice": [
            "**停止一切追加投入**，包括所谓的「解冻金」「保证金」「税费」「认证费」。"
            "这些是二次收割，不是解锁条件。",
            "保留全部证据：转账凭证、聊天记录、制度截图、群公告、APP 页面录屏。",
            "向属地公安机关经侦部门报案，同时可在国家反诈中心 APP 提交线索。",
            "联合其他受害者统一报案，避免各自零散报案导致并案困难。",
        ],
    },
    "deposit_required": {
        "label": "要求再充值才能提现",
        "outlook": "这是二次收割的典型手法：以「账户异常」「需缴税」「需验资」为由，"
                   "要求受害人再打款才能解锁原有余额。**打进去的钱不会解锁任何东西**。",
        "advice": [
            "**一分钱都不要再打。** 这是本方法论里最确定的一条结论。",
            "立刻固定证据并报案，不要再与客服协商——协商只会拖延你报案的时间。",
            "警惕「维权代理」「追损团队」：以追回损失为名收取前期费用的，绝大多数是二次诈骗。",
        ],
    },
    "vanished": {
        "label": "群解散 / 客服失联",
        "outlook": "项目方已进入跑路阶段。按套路链，接下来可能出现的动作是："
                   "短暂「重启」安抚、换名换皮开新盘、或者直接销号消失。"
                   "**跑路不是终点，是换皮的起点**。",
        "advice": [
            "立即报案，并向公安提供你掌握的全部转账流水与聊天记录。",
            "**警惕换皮新盘**：同一批人换个名字、换个 APP 重新开张，"
            "早期甚至会允许老会员「平移资产」以重建信任。不要参与。",
            "保留原始证据，不要因为群解散就删除聊天记录。",
        ],
    },
    "new_shell": {
        "label": "已换皮新盘",
        "outlook": "原项目已停摆，同一操盘方以新名称、新制度重新起盘，"
                   "常见手法是承诺老会员可「资产平移」或「优先兑付」，"
                   "本质是让老受害者变成新盘的推广者。",
        "advice": [
            "**新盘同样不能碰**，且不要因为「平移资产」而再次投入现金。",
            "新盘的出现本身就是原盘崩盘的证据，可用于补充报案材料。",
            "把新旧两个项目的制度页、域名、收款账户做对照，作为同一操盘方的线索提交。",
        ],
    },
}

DEFAULT_STAGE = "pre_launch"


def _fmt_money(x) -> str:
    try:
        return "{:,.0f}".format(float(x))
    except (TypeError, ValueError):
        return str(x)


def build(case: dict, title: str | None = None) -> str:
    p = case.get("project", {})
    res = run_audit(case)
    facts = case.get("facts", {})
    stage_key = case.get("stage", DEFAULT_STAGE)
    stage = STAGES.get(stage_key, STAGES[DEFAULT_STAGE])

    name = p.get("name") or "未命名项目"
    L: list[str] = []
    a = L.append

    a("# %s" % (title or "【风险审查】%s" % name))
    a("")
    a("> **评级**：%s ｜ **得分**：%d / 100 ｜ **信息完整度**：%d%%"
      % (res["label"], res["score"], round(res["coverage"] * 100)))
    a(">")
    a("> **审查人**：%s ｜ **审查日期**：%s ｜ **当前阶段**：%s"
      % (p.get("auditor") or "—",
         p.get("audit_date") or dt.date.today().isoformat(),
         stage["label"]))
    a("")

    # ── 基本信息 ──
    a("## 一、项目基本信息")
    a("")
    a("| 项 | 内容 |")
    a("|---|---|")
    a("| 项目名称 | %s |" % name)
    if p.get("aliases"):
        a("| 别名 / 曾用名 | %s |" % "、".join(p["aliases"]))
    a("| 宣称类型 | %s |" % (p.get("claimed_type") or "—"))
    a("| 宣称收益 | %s |" % (p.get("claimed_yield") or "—"))
    if p.get("url"):
        a("| 官网 / APP | `%s` |" % p["url"])
    if p.get("start_date"):
        a("| 起盘时间 | %s |" % p["start_date"])
    if p.get("channel"):
        a("| 推广渠道 | %s |" % p["channel"])
    a("")

    # ── 结论 ──
    a("## 二、结论")
    a("")
    hit_names = [h["name"] for h in res["hits"]]
    if res["level"] == "critical":
        concl = ("该项目的收益结构、拉人计酬设计与提现限制，"
                 "在结构上与已被司法机关处理的同类案件高度一致；"
                 "其宣称的实力背书在公开工商与备案信息中找不到对应主体。"
                 "**核心问题不是「它会不会出问题」，而是「出问题后钱在哪里」**——"
                 "目前没有答案。")
    elif res["level"] == "high":
        concl = ("该项目存在多项无法相互解释的异常，"
                 "尤其在收益来源与资金去向两个环节缺乏可核查的支撑。"
                 "在补充核实之前，不建议投入任何资金。")
    elif res["level"] == "medium":
        concl = ("该项目部分环节存在异常，但现有信息不足以形成完整判断。"
                 "建议补齐本报告第七节列出的信息缺口后再评估。")
    else:
        concl = ("在本次核查范围内，未发现该项目的明显违规特征。"
                 "**这只说明「没查到」，不说明「没问题」**——"
                 "未覆盖的环节见第七节信息缺口。")

    a(concl)
    a("")
    if hit_names:
        a("命中的关键特征：**%s**。" % "、".join(hit_names[:6]))
        a("")

    # ── 证据表 ──
    ev = case.get("evidence", [])
    a("## 三、证据表")
    a("")
    if ev:
        a("| # | 核查项 | 查到的事实 | 说明什么 | 来源 | 日期 |")
        a("|---|---|---|---|---|---|")
        for i, e in enumerate(ev, 1):
            a("| %d | %s | %s | %s | %s | %s |"
              % (i, e.get("item", "—"), e.get("fact", "—"),
                 e.get("implication", "—"), e.get("source", "—"),
                 e.get("date", "—")))
        a("")
        a("> 证据表的每一行都可以独立复核。「说明什么」一栏是基于事实的推断，"
          "与「查到的事实」严格分开——**这是本报告能被采信的前提**。")
    else:
        a("*尚未录入证据条目。请在案件 JSON 的 `evidence` 字段中补充。*")
    a("")

    # ── 维度得分 ──
    a("## 四、风险维度评分")
    a("")
    a("| 维度 | 得分 | 满分 | 主要问题 |")
    a("|---|---|---|---|")
    for k, d in res["dimensions"].items():
        issues = [h["name"] for h in res["hits"] if h["dim"] == k]
        a("| %s %s | %d | %d | %s |"
          % (k, d["name"], d["score"], d["max"],
             "、".join(issues) if issues else "—"))
    a("")
    a("**合计 %d / 100 → %s**" % (res["score"], res["label"]))
    a("")
    a("> %s" % res["meaning"])
    a("")

    # ── 收益反算 ──
    y = facts.get("yield", {})
    if y.get("daily_rate") or y.get("monthly_rate"):
        a("## 五、收益模型反算")
        a("")
        try:
            daily = y.get("daily_rate")
            monthly = y.get("monthly_rate")
            if daily:
                d = daily / 100.0
            elif monthly:
                d = (1 + monthly / 100.0) ** (1 / 30.0) - 1
            else:
                d = None
            if not d:
                raise ValueError("收益数据不完整")
            r = apr_analyze(d, cycle=y.get("cycle_days"))
            comp = r["compound_annual"]
            a("| 指标 | 数值 |")
            a("|---|---|")
            a("| 日化收益率 | %.2f%% |" % (r["daily_pct"]))
            a("| 单利年化 | %.2f%% |" % (r["simple_annual"] * 100))
            a("| 复利年化 | %s |"
              % ("%.0f 倍" % (comp + 1) if comp > 10
                 else "%.1f%%" % (comp * 100)))
            a("| 静态回本 | %d 天 |" % round(r["payback_days"]))
            a("| 民间借贷司法保护上限 | %.1f%%（一年期 LPR %.2f%% × 4） |"
              % (r["legal_cap_annual"] * 100, 3.45))
            if r.get("multiple_of_legal_cap"):
                a("| 超出上限倍数 | %.1f 倍 |" % r["multiple_of_legal_cap"])
            a("")
            a("**这条测算的意义**：不是「收益高所以是骗局」——高收益本身不违法。"
              "而是「这个收益率在物理上必须由新资金来兑付」。"
              "当它没有真实经营收入时，这个缺口只能由后来者填，"
              "而后来者终有耗尽的一天。")
            a("")
            cc = r.get("cycle_check")
            if cc and not cc["consistent"]:
                a("⚠️ 另外，项目宣称的「%d 天回本」与实际日化 %.2f%% 并不自洽"
                  "（按周期折算应为日化 %.2f%%），制度说明本身存在内部矛盾。"
                  % (cc["declared_cycle_days"], cc["actual_daily_pct"],
                     cc["implied_daily_pct"]))
                a("")
        except Exception:  # noqa: BLE001
            a("*收益数据不完整，无法反算。*")
            a("")

    # ── 结局推演 ──
    a("## 六、结局推演")
    a("")
    a("**当前阶段：%s**" % stage["label"])
    a("")
    a(stage["outlook"])
    a("")
    a("同类项目的典型走向（按时间顺序）：")
    a("")
    a("```")
    a("维稳 → 拖延提现 → 改代金券/积分 → 重启 → 换币换皮")
    a("→ 停盘「系统维护」→ 关网跑路 → 开新盘再割")
    a("```")
    a("")
    a("## 七、行动建议")
    a("")
    for i, adv in enumerate(stage["advice"], 1):
        a("%d. %s" % (i, adv))
    a("")

    # ── 缺口 ──
    a("## 八、未能核实项")
    a("")
    if res["gaps"]:
        a("以下项目在公开渠道未取得有效信息，**未计入评分**。"
          "这不是「没问题」，而是「还不知道」：")
        a("")
        for g in res["gaps"]:
            a("- [ ] **%s** —— %s" % (g["name"], g["basis"]))
    else:
        a("*本次核查覆盖了全部检查项。*")
    a("")

    # ── 免责 ──
    a("## 免责声明")
    a("")
    a("本报告基于公开渠道信息与用户提供的材料整理，仅作**风险提示**之用，"
      "不构成法律意见、投资建议或对任何主体的事实认定。"
      "报告中「查到的事实」均可溯源至公开来源，"
      "「说明什么」为基于事实的推断，与事实本身严格区分。"
      "项目性质的最终认定权在司法机关。")
    a("")
    a("如本报告内容与事实有出入，欢迎指出并提供证据，将及时更正。")
    a("")
    a("---")
    a("")
    a("*本报告由 [fund-anti-fraud](https://github.com/janecoolman515/fund-anti-fraud) 生成*")

    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="风险报告生成器")
    ap.add_argument("case", help="案件 JSON 文件")
    ap.add_argument("-o", "--output", help="输出 Markdown 路径（默认打印到终端）")
    ap.add_argument("--title", help="自定义报告标题")
    args = ap.parse_args()

    path = pathlib.Path(args.case)
    if not path.exists():
        print("找不到案件文件：%s" % path, file=sys.stderr)
        return 2
    try:
        case = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print("JSON 格式错误：%s（第 %d 行）" % (e.msg, e.lineno), file=sys.stderr)
        return 2

    md = build(case, args.title)
    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print("已生成：%s（%d 字）" % (out, len(md)))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
