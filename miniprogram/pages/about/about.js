const risk = require('../../utils/risk.js');
const CASES = require('../../data/cases.js');

Page({
  data: {
    account: getApp().globalData.account,
    caseCount: Object.keys(CASES).length,
    riskCount: risk.COUNTS.all,
    rules: [
      { k: 'A', n: '主体资质', m: 25, d: '备案主体、实缴资本、工商状态、域名年龄' },
      { k: 'B', n: '收益结构', m: 30, d: '日化收益率、推荐奖层级、门槛费、锁仓复投' },
      { k: 'C', n: '资金安全', m: 25, d: '提现限制、收款主体、第三方存管、造血业务' },
      { k: 'D', n: '外部信号', m: 20, d: '监管提示、投诉集中度、立案判决、官方撇清' }
    ],
    steps: [
      { n: '01', t: '收料', d: '把已确定的事实和待核实的信息分开' },
      { n: '02', t: '快筛', d: '收益从哪来 · 收益率多少 · 要不要拉人' },
      { n: '03', t: '深查', d: '六条主线取证，四把推理刀穿透' },
      { n: '04', t: '出报告', d: '100 分评分卡定级，每条结论可溯源' }
    ]
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
  }
});
