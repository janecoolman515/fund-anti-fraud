const engine = require('../../utils/engine.js');

/* 各字段的选项： [值, 显示文本] */
const OPTS = {
  icp: [['unknown', '不清楚'], ['individual', '个人 / 个体户'], ['company', '企业'], ['none', '无备案']],
  match: [['unknown', '不清楚'], ['yes', '一致'], ['no', '不一致']],
  status: [['unknown', '不清楚'], ['normal', '正常'], ['abnormal', '经营异常 / 注销']],
  lock: [['unknown', '不清楚'], ['yes', '有'], ['no', '没有']],
  wd: [['unknown', '不清楚'], ['yes', '受限（限额/排队/高手续费）'], ['no', '正常']],
  payee: [['unknown', '不清楚'], ['personal', '个人账户'], ['company', '对公账户']],
  cust: [['unknown', '不清楚'], ['yes', '有'], ['no', '没有']],
  biz: [['unknown', '不清楚'], ['real', '有，能对上账'], ['weak', '有，但对不上账'], ['none', '没有']],
  legal: [['unknown', '不清楚'], ['yes', '有'], ['no', '没有']]
};

function buildSelect(key) {
  const list = OPTS[key];
  return {
    idx: 0,
    val: list[0][0],
    label: list[0][1],
    labels: list.map(function (x) { return x[1]; }),
    values: list.map(function (x) { return x[0]; })
  };
}

Page({
  data: {
    form: {},
    nums: {
      paid: '', domain: '', daily: '', level: '', fee: '', complaint: ''
    },
    checks: { cap: false, reg: false, deny: false },
    result: null,
    resultReady: false
  },

  onLoad() {
    const form = {};
    Object.keys(OPTS).forEach(function (k) { form[k] = buildSelect(k); });
    this.setData({ form: form });
  },

  onPick(e) {
    const key = e.currentTarget.dataset.key;
    const idx = Number(e.detail.value);
    const f = this.data.form[key];
    this.setData({
      ['form.' + key]: {
        idx: idx,
        val: f.values[idx],
        label: f.labels[idx],
        labels: f.labels,
        values: f.values
      }
    });
  },

  onNum(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ ['nums.' + key]: e.detail.value });
  },

  onCheck(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ ['checks.' + key]: e.detail.value.length > 0 });
  },

  onCalc() {
    const f = this.data.form;
    const n = this.data.nums;
    const c = this.data.checks;

    const num = function (v) {
      if (v === '' || v === null || v === undefined) return null;
      const x = parseFloat(v);
      return isNaN(x) ? null : x;
    };

    const facts = {
      icp: f.icp.val === 'unknown' ? null : f.icp.val,
      match: f.match.val === 'unknown' ? null : f.match.val,
      paid: num(n.paid),
      status: f.status.val === 'unknown' ? null : f.status.val,
      domain: num(n.domain),
      daily: num(n.daily),
      level: num(n.level),
      fee: num(n.fee),
      lock: f.lock.val === 'unknown' ? null : f.lock.val,
      cap: c.cap,
      wd: f.wd.val === 'unknown' ? null : f.wd.val,
      payee: f.payee.val === 'unknown' ? null : f.payee.val,
      cust: f.cust.val === 'unknown' ? null : f.cust.val,
      biz: f.biz.val === 'unknown' ? null : f.biz.val,
      complaint: num(n.complaint),
      legal: f.legal.val === 'unknown' ? null : f.legal.val,
      reg: c.reg,
      deny: c.deny
    };

    const r = engine.calcScore(facts);
    const g = engine.grade(r.total, r.coverage);

    const dims = Object.keys(r.dims).map(function (k) {
      return {
        k: k,
        n: engine.DIM_NAME[k],
        v: r.dims[k],
        m: engine.DIM_MAX[k],
        pct: Math.round(r.dims[k] / engine.DIM_MAX[k] * 100)
      };
    });

    this.setData({
      resultReady: true,
      result: {
        total: r.total,
        grade: g,
        dims: dims,
        hits: r.hits,
        gaps: r.gaps,
        verified: engine.RULES.length - r.gaps.length,
        totalRules: engine.RULES.length
      }
    });
  },

  onReset() {
    const form = {};
    Object.keys(OPTS).forEach(function (k) { form[k] = buildSelect(k); });
    this.setData({
      form: form,
      nums: { paid: '', domain: '', daily: '', level: '', fee: '', complaint: '' },
      checks: { cap: false, reg: false, deny: false },
      result: null,
      resultReady: false
    });
  }
});
