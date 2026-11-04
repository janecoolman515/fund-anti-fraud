const CASES = require('../../data/cases.js');

/* 名单数据约 300KB，延迟到首次使用时加载，避免首屏解析卡顿 */
let _risk = null;
function getRisk() {
  if (!_risk) _risk = require('../../utils/risk.js');
  return _risk;
}

/* 案例索引：名称 + 全部别名，用于命中判断 */
const CASE_INDEX = Object.keys(CASES).map(function (k) {
  const c = CASES[k];
  return { key: k, names: [c.name].concat(c.aliases || []) };
});

function findCase(kw) {
  const q = (kw || '').replace(/\s/g, '').toLowerCase();
  if (!q) return null;
  let partial = null;
  for (let i = 0; i < CASE_INDEX.length; i++) {
    const it = CASE_INDEX[i];
    for (let j = 0; j < it.names.length; j++) {
      const n = (it.names[j] || '').replace(/\s/g, '').toLowerCase();
      if (!n) continue;
      if (n === q) return it.key;
      if (!partial && (n.indexOf(q) >= 0 || q.indexOf(n) >= 0)) partial = it.key;
    }
  }
  return partial;
}

const CASE_LIST = Object.keys(CASES).map(function (k) {
  const c = CASES[k];
  return {
    key: k,
    name: c.name,
    type: c.type || '',
    scale: c.scale || '',
    badge: c.badge || '已判决'
  };
});

Page({
  data: {
    keyword: '',
    account: getApp().globalData.account,
    hot: ['善心汇', '民族资产解冻', '云数贸', '1040阳光工程', '金涌投资'],
    cases: CASE_LIST,
    caseHit: null,
    riskHit: null,
    notFound: '',
    totalRisk: 0,
    caseCount: CASE_LIST.length
  },

  onLoad() {
    const self = this;
    setTimeout(function () {
      try {
        self.setData({ totalRisk: getRisk().COUNTS.all });
      } catch (e) {}
    }, 30);
  },

  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  onSearch() {
    this.search(this.data.keyword);
  },

  onHot(e) {
    const k = e.currentTarget.dataset.k;
    this.setData({ keyword: k });
    this.search(k);
  },

  onGoCheck() {
    wx.switchTab({ url: '/pages/check/check' });
  },

  onGoLibrary() {
    wx.switchTab({ url: '/pages/library/library' });
  },

  onCopyName() {
    wx.setClipboardData({
      data: this.data.account.name,
      success: () => wx.showToast({ title: '公众号名称已复制', icon: 'none' })
    });
  },

  onCopyWx() {
    wx.setClipboardData({
      data: this.data.account.wechat,
      success: () => wx.showToast({ title: '微信号已复制', icon: 'none' })
    });
  },

  search(kw) {
    kw = (kw || '').trim();
    if (!kw) {
      wx.showToast({ title: '请输入项目名称', icon: 'none' });
      return;
    }

    const ck = findCase(kw);
    const rk = getRisk().find(kw);

    if (!ck && !rk) {
      this.setData({ caseHit: null, riskHit: null, notFound: kw });
      wx.pageScrollTo({ scrollTop: 0, duration: 200 });
      return;
    }

    let caseHit = null;
    if (ck) {
      const c = CASES[ck];
      caseHit = {
        name: c.name,
        badge: c.badge || '已判决',
        type: c.type || '',
        crime: c.crime || '',
        principal: c.principal || '',
        sentence: c.sentence || '',
        court: c.court || '',
        judged: c.judged || '',
        scale: c.scale || '',
        pattern: c.pattern || '',
        features: c.features || [],
        lesson: c.lesson || '',
        extra: c.extra || '',
        sources: c.sources || [],
        aliases: (c.aliases || []).join(' / ')
      };
    }

    let riskHit = null;
    if (rk) {
      riskHit = {
        n: rk.n,
        t: rk.t,
        s: rk.s,
        d: rk.d,
        src: rk.src,
        st: rk.st,
        stText: getRisk().ST_TEXT[rk.st]
      };
    }

    this.setData({ caseHit: caseHit, riskHit: riskHit, notFound: '' });
    wx.pageScrollTo({ scrollTop: 0, duration: 200 });
  }
});
