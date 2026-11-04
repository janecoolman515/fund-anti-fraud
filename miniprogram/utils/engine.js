/**
 * 风险审查引擎 —— 18 条规则 + 示例数据
 *
 * 设计原则：
 *   1. 只对「已确认的事实」计分，未知项不计分但记入信息缺口
 *   2. 已核实项过少时不出评级，避免把「没查到」误判为「没问题」
 *   3. 不做法律定性，只做特征描述
 */

const DIM_MAX = { A: 25, B: 30, C: 25, D: 20 };
const DIM_NAME = { A: '主体资质', B: '收益结构', C: '资金安全', D: '外部信号' };

/**
 * 规则表：[编号, 维度, 分值, 名称, 判定函数]
 * 判定函数返回 true=命中 / false=未命中 / null=信息不足
 */
const RULES = [
  ['A1', 'A', 8, '备案主体非企业', f => f.icp === null ? null : (f.icp === 'individual' || f.icp === 'none')],
  ['A2', 'A', 4, '备案与宣传主体不符', f => f.match === null ? null : f.match === 'no'],
  ['A3', 'A', 5, '实缴资本极低', f => f.paid === null ? null : (f.paid <= 10)],
  ['A4', 'A', 6, '工商状态异常', f => f.status === null ? null : f.status === 'abnormal'],
  ['A5', 'A', 6, '域名注册不足一年', f => f.domain === null ? null : (f.domain < 12)],

  ['B1', 'B', 12, '日化收益率 ≥ 1%', f => f.daily === null ? null : (f.daily >= 1)],
  ['B2', 'B', 6, '日化 0.1%~1%', f => f.daily === null ? null : (f.daily >= 0.1 && f.daily < 1)],
  ['B3', 'B', 8, '推荐奖层级且无封顶', f => f.level === null ? null : (f.level >= 1 && !f.cap)],
  ['B4', 'B', 5, '存在入门门槛费', f => f.fee === null ? null : (f.fee > 0)],
  ['B5', 'B', 5, '锁仓或强制复投', f => f.lock === null ? null : f.lock === 'yes'],
  ['B6', 'B', 6, '承诺保本/固定回报/回购', f => f.guaranteed === null ? null : f.guaranteed === 'yes'],
  ['B7', 'B', 8, '日化收益率 ≥ 10%（极端）', f => f.daily === null ? null : (f.daily >= 10)],

  ['C1', 'C', 10, '提现受限', f => f.wd === null ? null : f.wd === 'yes'],
  ['C2', 'C', 6, '收款方为个人', f => f.payee === null ? null : f.payee === 'personal'],
  ['C3', 'C', 5, '无第三方存管', f => f.cust === null ? null : f.cust === 'no'],
  ['C4', 'C', 4, '无真实造血业务', f => f.biz === null ? null : (f.biz === 'none' || f.biz === 'weak')],
  ['C5', 'C', 6, '价格可被平台操控', f => f.manip === null ? null : f.manip === 'yes'],

  ['D1', 'D', 8, '监管已发风险提示', f => f.reg ? true : null],
  ['D2', 'D', 6, '投诉集中', f => f.complaint === null ? null : (f.complaint >= 10)],
  ['D3', 'D', 6, '已有立案或判决', f => f.legal === null ? null : f.legal === 'yes'],
  ['D4', 'D', 4, '官方已撇清关系', f => f.deny ? true : null]
];

/**
 * 计算风险分
 * @param {Object} f 事实对象
 * @returns {Object} { dims, total, hits, gaps, coverage }
 */
function calcScore(f) {
  const dims = { A: 0, B: 0, C: 0, D: 0 };
  const hits = [];
  const gaps = [];

  RULES.forEach(function (rule) {
    const id = rule[0], dim = rule[1], w = rule[2], name = rule[3], test = rule[4];
    let r = null;
    try { r = test(f); } catch (e) { r = null; }

    if (r === null) {
      gaps.push({ id: id, name: name });
    } else if (r) {
      dims[dim] += w;
      hits.push({ id: id, dim: dim, w: w, name: name });
    }
  });

  // 维度封顶，避免单项堆分导致总分失真
  Object.keys(dims).forEach(function (k) {
    dims[k] = Math.min(dims[k], DIM_MAX[k]);
  });

  const total0 = dims.A + dims.B + dims.C + dims.D;
  const coverage = (RULES.length - gaps.length) / RULES.length;

  /* 组合判定：传销结构（《禁止传销条例》第七条第（二）（三）项）
     入门费 + 团队计酬本身就是法定特征，不需要再等收益率 */
  const ids = {};
  hits.forEach(function (h) { ids[h.id] = true; });
  const comboPonzi = !!(ids.B3 && ids.B4);
  const extremeYield = !!ids.B7;

  let total = total0;
  if (comboPonzi) total = Math.max(total, 82);
  if (extremeYield) total = Math.max(total, 80);

  return {
    dims: dims,
    total: total,
    hits: hits.sort(function (a, b) { return b.w - a.w; }),
    gaps: gaps,
    coverage: coverage,
    comboPonzi: comboPonzi,
    extremeYield: extremeYield
  };
}

/**
 * 按分数与覆盖度给出评级
 * @returns {Object} { level, text, color, note }
 */
function grade(total, coverage) {
  // 顺序：分数顶格时不该被「覆盖率不足」压成信息不足
  if (total >= 80) {
    return { level: 'critical', text: '极高风险', color: '#D9433F',
      note: '命中多项核心违规特征，与已知资金盘结构高度一致' };
  }
  if (coverage < 0.3) {
    return {
      level: 'unknown',
      text: '信息不足',
      color: '#6E88A6',
      note: '已核实项太少，无法形成有效评级'
    };
  }
  if (total >= 60) {
    return { level: 'high', text: '高风险', color: '#E07B39',
      note: '存在多项无法解释的异常，强烈建议不参与' };
  }
  if (total >= 40) {
    return { level: 'medium', text: '中风险', color: '#C9A227',
      note: '部分异常或信息不足，需补充核查后再判断' };
  }
  return { level: 'low', text: '暂未发现明显违规', color: '#2E9E5B',
    note: '本次自查范围内未发现，不代表安全或合法' };
}

/* ══════════════════════════════════════════════
   示例数据（项目名称与信息均为虚构）
   ══════════════════════════════════════════════ */
const DB = {
  '星辰国际': {
    name: '星辰国际',
    tag: '示例·虚构',
    aliases: '星辰财富 / Star Capital',
    type: '跨境电商 + 理财',
    claim: '日化 1.8%，7 天一轮',
    score: 86,
    grade: { level: 'critical', text: '极高风险', color: '#D9433F',
      note: '命中多项核心违规特征，与已知资金盘结构高度一致' },
    dims: [
      { k: 'A', n: '主体资质', v: 25, m: 25, tags: '个人备案 / 实缴为零 / 工商异常' },
      { k: 'B', n: '收益结构', v: 30, m: 30, tags: '日化1.8% / 三级无封顶 / 门槛费' },
      { k: 'C', n: '资金安全', v: 25, m: 25, tags: '提现限额 / 个人收款 / 无存管' },
      { k: 'D', n: '外部信号', v: 6, m: 20, tags: '投诉 47 条集中爆发' }
    ],
    ev: [
      { i: 'ICP 备案主体', f: '备案主体为个人，与宣称集团无关联', w: '宣称的集团背景在备案层面无对应主体', s: '工信部备案系统' },
      { i: '工商登记', f: '注册资本 1000 万，实缴 0 元；2026-09 列入经营异常', w: '资本实力无实缴支撑，已出现监管异常', s: '国家企业信用信息公示系统' },
      { i: '域名注册', f: '注册于 2026-06，到期 2027-01（剩余 75 天）', w: '注册仅 4 个月，到期不足 3 个月', s: 'WHOIS 查询' },
      { i: '收益制度', f: '日化 1.8%，直推 3 代 8/5/3%，无封顶', w: '年化约 673 倍，收益与拉人层级挂钩', s: 'APP 制度页截图' },
      { i: '收款方式', f: '充值页为个人收款码', w: '资金未进对公账户，无第三方存管', s: '充值页截图' },
      { i: '用户投诉', f: '黑猫投诉 47 条，集中在 2026-09 后', w: '提现不到账、要求补缴解冻金', s: '黑猫投诉平台' }
    ],
    stage: 2,
    advice: [
      { b: '尚未参与', t: '不参与。日化 1.8% 且收益与拉人挂钩，只有「什么时候崩」。' },
      { b: '能提现', t: '立即全额提现，不要有「再赚一轮」的念头。' },
      { b: '提现变慢', t: '停止追加，保留转账与聊天记录，向属地公安经侦报案。' },
      { b: '要求再充值', t: '一分钱都不要打。所谓「解冻金」是二次收割。' }
    ]
  },

  '云矿宝': {
    name: '云矿宝',
    tag: '示例·虚构',
    aliases: '云矿宝科技 / CloudMiner',
    type: '云算力挖矿',
    claim: '日化 0.45%，180 天固定收益',
    score: 72,
    grade: { level: 'high', text: '高风险', color: '#E07B39',
      note: '存在多项无法解释的异常，强烈建议不参与' },
    dims: [
      { k: 'A', n: '主体资质', v: 16, m: 25, tags: '域名 8 个月 / 实缴偏低' },
      { k: 'B', n: '收益结构', v: 24, m: 30, tags: '日化0.45% / 锁仓180天 / 无封顶' },
      { k: 'C', n: '资金安全', v: 19, m: 25, tags: '提现排队 / 无存管 / 算力无凭据' },
      { k: 'D', n: '外部信号', v: 13, m: 20, tags: '投诉 21 条 / 无监管提示' }
    ],
    ev: [
      { i: '工商登记', f: '注册资本 500 万，实缴 38 万；参保 2 人', w: '与「专业矿场团队」不匹配', s: '国家企业信用信息公示系统' },
      { i: '收益制度', f: '日化 0.45%，180 天固定收益，到期返本', w: '年化约 4.1 倍，承诺固定回报', s: 'APP 制度页截图' },
      { i: '算力凭证', f: '无矿场地址、电费单、算力分配凭据', w: '收益来源不可核', s: '客服沟通记录' },
      { i: '提现规则', f: 'T+7 到账，单日限额 2000，超出需排队', w: '资金流出被主动控制', s: 'APP 提现页截图' }
    ],
    stage: 1,
    advice: [
      { b: '尚未参与', t: '不参与。承诺固定日收益且算力不可验，收益不可核。' },
      { b: '能提现', t: '先提现再判断。能提出来的钱才是你的钱。' },
      { b: '已锁仓', t: '保留协议、转账记录、收益截图，关注工商变更。' },
      { b: '提现排队', t: '停止追加，准备报案材料。' }
    ]
  },

  '数藏星河': {
    name: '数藏星河',
    tag: '示例·虚构',
    aliases: '星河数藏',
    type: '数字藏品平台',
    claim: '首发 30 天溢价回购，邀请返 5%',
    score: 51,
    grade: { level: 'medium', text: '中风险', color: '#C9A227',
      note: '部分异常或信息不足，需补充核查后再判断' },
    dims: [
      { k: 'A', n: '主体资质', v: 11, m: 25, tags: '企业备案 / 实缴待核' },
      { k: 'B', n: '收益结构', v: 22, m: 30, tags: '承诺回购 / 邀请返佣' },
      { k: 'C', n: '资金安全', v: 10, m: 25, tags: '提现待核 / 无存管信息' },
      { k: 'D', n: '外部信号', v: 8, m: 20, tags: '信息不足' }
    ],
    ev: [
      { i: '平台模式', f: '平台自营账号在二级市场挂单收自家藏品', w: '存在自买自卖抬价嫌疑', s: '二级市场截图' },
      { i: '回购承诺', f: '宣称「首发 30 天溢价 15% 回购」', w: '固定溢价回购属变相还本付息承诺', s: '活动海报' },
      { i: '邀请机制', f: '邀请新用户购买返 5% 现金', w: '收益与拉新直接挂钩', s: 'APP 邀请页截图' },
      { i: '备案信息', f: '备案主体为企业，含数字内容服务', w: '形式上合规，需核实交易场所资质', s: '工信部备案系统' }
    ],
    stage: 0,
    advice: [
      { b: '尚未参与', t: '先补核查：交易场所资质、回购资金来源。' },
      { b: '已参与', t: '不追加。自买自卖 + 固定回购同时出现，价格大概率被操控。' },
      { b: '补充材料', t: '提供用户协议与回购条款原文，可提升核查完整度。' },
      { b: '信息缺口', t: '资金存管、实缴资本、实际控制人未核实。' }
    ]
  },

  '惠民优选': {
    name: '惠民优选',
    tag: '示例·虚构',
    aliases: '惠民优选商城',
    type: '社区团购 + 消费返利',
    claim: '消费满 500 返 20%，推荐返 3%',
    score: 28,
    grade: { level: 'low', text: '暂未发现明显违规', color: '#2E9E5B',
      note: '本次核查范围内未发现，不代表安全或合法' },
    dims: [
      { k: 'A', n: '主体资质', v: 8, m: 25, tags: '企业备案 / 实缴 200 万' },
      { k: 'B', n: '收益结构', v: 10, m: 30, tags: '返利比例低 / 一级返佣' },
      { k: 'C', n: '资金安全', v: 7, m: 25, tags: '对公收款 / 提现正常' },
      { k: 'D', n: '外部信号', v: 3, m: 20, tags: '投诉 2 条 / 无监管提示' }
    ],
    ev: [
      { i: '工商登记', f: '注册资本 300 万，实缴 200 万；参保 26 人', w: '有真实团队，资本与业务匹配', s: '国家企业信用信息公示系统' },
      { i: '收益结构', f: '消费返 20%，推荐一级返 3%，无多层级', w: '返利来自商品毛利，无入门费', s: '平台规则页' },
      { i: '收款方式', f: '对公账户收款，可开发票', w: '资金进企业账户，可追溯', s: '下单页截图' },
      { i: '造血能力', f: '有实体仓配，商品价格与市场持平', w: '存在可对账的真实收入', s: '实地核查 + 比价' }
    ],
    stage: 0,
    advice: [
      { b: '本次结论', t: '未发现资金盘或传销特征，返利模式可持续性仍需观察。' },
      { b: '仍需注意', t: '若引入多层级分销，性质会改变，需持续跟踪。' },
      { b: '信息缺口', t: '资金存管方式、返利资金来源明细未公开。' },
      { b: '提醒', t: '绿色评级只代表「本次未发现」，不等于合法。' }
    ]
  }
};

const CHAIN = ['维稳', '拖延提现', '改积分', '重启', '换皮', '停盘', '跑路', '开新盘'];

module.exports = {
  DIM_MAX: DIM_MAX,
  DIM_NAME: DIM_NAME,
  RULES: RULES,
  calcScore: calcScore,
  grade: grade,
  DB: DB,
  CHAIN: CHAIN,
  KEYS: Object.keys(DB)
};
