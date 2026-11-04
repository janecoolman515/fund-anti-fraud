const risk = require('../../utils/risk.js');

Page({
  data: {
    kw: '',
    st: 'all',
    mode: '',
    list: [],
    total: 0,
    hasMore: false,
    loading: false,
    modes: risk.MODES,
    counts: risk.COUNTS
  },

  onLoad() {
    this.reload();
  },

  onInput(e) {
    this.setData({ kw: e.detail.value });
    const self = this;
    if (this._timer) clearTimeout(this._timer);
    this._timer = setTimeout(function () { self.reload(); }, 250);
  },

  onStatus(e) {
    this.setData({ st: e.currentTarget.dataset.st });
    this.reload();
  },

  onMode(e) {
    const m = e.currentTarget.dataset.mode;
    this.setData({ mode: this.data.mode === m ? '' : m });
    this.reload();
  },

  reload() {
    const r = risk.query({
      kw: this.data.kw,
      st: this.data.st,
      mode: this.data.mode,
      offset: 0,
      size: 60
    });
    this.setData({ list: r.list, total: r.total, hasMore: r.hasMore });
  },

  onMore() {
    if (!this.data.hasMore || this.data.loading) return;
    this.setData({ loading: true });
    const r = risk.query({
      kw: this.data.kw,
      st: this.data.st,
      mode: this.data.mode,
      offset: this.data.list.length,
      size: 60
    });
    this.setData({
      list: this.data.list.concat(r.list),
      total: r.total,
      hasMore: r.hasMore,
      loading: false
    });
  },

  onTap(e) {
    const r = this.data.list[e.currentTarget.dataset.i];
    if (!r) return;
    let c = '类型：' + r.t + '\n状态：' + r.s;
    if (r.d) c += '\n说明：' + r.d;
    if (r.src) c += '\n来源：' + r.src;
    c += '\n\n本条来自公开报道汇总，未经司法机关认定，可能存在重名。';
    wx.showModal({
      title: r.n,
      content: c,
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
