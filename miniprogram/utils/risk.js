/**
 * 高风险名单数据层
 * 数据来自网站 risk-list.js（2068 条，公开报道汇总）
 * 负责：归一化、状态判定、模式分类、检索、筛选、分页
 */
const RAW = require('../data/risk.js');

/* 模式分类规则（与网站 library.html 完全一致） */
const MODE_RULES = [
  { name: '民族资产解冻', re: /民族资产|国家项目|假冒官方|假冒机关|假冒机构|假冒慈善|政策热点|虚假福利/ },
  { name: '假冒套牌', re: /假冒|套牌|山寨|仿冒/ },
  { name: '互助寄售', re: /互助|寄售|抢单|抢拍|竞拍|拆分/ },
  { name: '跟单交易', re: /跟单|外汇|期货|股票|量化|带单|贵金属|对赌/ },
  { name: '虚拟币公链', re: /虚拟币|公链|DeFi|空气币|代币|钱包|质押|挖矿|算力|矿机|链游|数藏/ },
  { name: '消费返利', re: /消费返利|返利|商城|社交电商|新零售|积分|短剧|影视|直播|短视频/ },
  { name: 'P2P理财', re: /P2P|理财|集资|私募|解债|保险/ },
  { name: '传销拉人', re: /传销|直销|保健品|康养|养老/ }
];

/* 状态判定（与网站一致） */
const BOOM_RE = /已崩|已跑|已立案|已判|已抓|已爆|已死|已凉|已出事|已关网|已失败|崩盘|跑路|已破案|已定性|已处罚|已报警|崩盘中|已公诉|官方点名|已判刑/;
const WARN_RE = /高危|预警|即将|在运作|疑似|未知/;

const ST_TEXT = { boom: '已暴雷', warn: '预警', other: '其他' };
const ST_RANK = { boom: 0, warn: 1, other: 2 };

function modeOf(r) {
  const s = (r.t || '') + ' ' + (r.d || '');
  for (let i = 0; i < MODE_RULES.length; i++) {
    if (MODE_RULES[i].re.test(s)) return MODE_RULES[i].name;
  }
  return '其他资金盘';
}

function statusOf(r) {
  const s = r.s || '';
  if (BOOM_RE.test(s)) return 'boom';
  if (WARN_RE.test(s)) return 'warn';
  return 'other';
}

/* 归一化：只在模块加载时做一次 */
const LIST = RAW.map(function (r, i) {
  const st = statusOf(r);
  return {
    id: i,
    n: r.n || '未命名',
    t: r.t || '未分类',
    s: r.s || '未知',
    d: r.d || '',
    src: r.src || '',
    mode: modeOf(r),
    st: st,
    stText: ST_TEXT[st],
    key: (r.n || '').replace(/\s/g, '').toLowerCase()
  };
}).sort(function (a, b) {
  if (ST_RANK[a.st] !== ST_RANK[b.st]) return ST_RANK[a.st] - ST_RANK[b.st];
  return a.n < b.n ? -1 : (a.n > b.n ? 1 : 0);
});

/* 统计 */
const COUNTS = { all: LIST.length, boom: 0, warn: 0, other: 0 };
const MODE_MAP = {};
LIST.forEach(function (r) {
  COUNTS[r.st]++;
  MODE_MAP[r.mode] = (MODE_MAP[r.mode] || 0) + 1;
});
const MODES = Object.keys(MODE_MAP).map(function (m) {
  return { name: m, count: MODE_MAP[m] };
}).sort(function (a, b) { return b.count - a.count; });

/**
 * 检索 + 筛选 + 分页
 * @param {Object} o { kw, st, mode, offset, size }
 */
function query(o) {
  o = o || {};
  const kw = (o.kw || '').trim().toLowerCase();
  const st = o.st || 'all';
  const mode = o.mode || '';
  const offset = o.offset || 0;
  const size = o.size || 60;

  const out = [];
  let total = 0;
  for (let i = 0; i < LIST.length; i++) {
    const r = LIST[i];
    if (st !== 'all' && r.st !== st) continue;
    if (mode && r.mode !== mode) continue;
    if (kw) {
      const hay = (r.key + ' ' + r.t + ' ' + r.d + ' ' + r.s).toLowerCase();
      if (hay.indexOf(kw) < 0) continue;
    }
    total++;
    if (total > offset && out.length < size) out.push(r);
  }
  return { list: out, total: total, hasMore: offset + out.length < total };
}

/** 按名称精确/包含匹配（查询页用） */
function find(kw) {
  const k = (kw || '').trim().replace(/\s/g, '').toLowerCase();
  if (!k) return null;
  let partial = null;
  for (let i = 0; i < LIST.length; i++) {
    const r = LIST[i];
    if (r.key === k) return r;
    if (!partial && r.key && (r.key.indexOf(k) >= 0 || k.indexOf(r.key) >= 0)) partial = r;
  }
  return partial;
}

module.exports = {
  LIST: LIST,
  MODES: MODES,
  COUNTS: COUNTS,
  ST_TEXT: ST_TEXT,
  query: query,
  find: find
};
