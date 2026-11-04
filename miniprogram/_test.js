const e = require('./utils/engine.js');

function mk(o) {
  return Object.assign({
    icp: null, match: null, paid: null, status: null, domain: null,
    daily: null, level: null, fee: null, lock: null, cap: false,
    guaranteed: null, wd: null, payee: null, cust: null, biz: null,
    manip: null, complaint: null, legal: null, reg: false, deny: false
  }, o);
}

function t(name, f) {
  const r = e.calcScore(f);
  const g = e.grade(r.total, r.coverage);
  console.log(
    name.padEnd(18),
    String(r.total).padStart(3),
    g.text.padEnd(10),
    '命中' + r.hits.length,
    r.comboPonzi ? '★组合' : '',
    r.extremeYield ? '★极端' : ''
  );
}

console.log('=== 小程序引擎测试 ===\n');

t('全填高风险', mk({
  icp: 'individual', match: 'no', paid: 0, status: 'abnormal', domain: 4,
  daily: 1.8, level: 3, fee: 998, lock: 'yes', wd: 'yes',
  payee: 'personal', cust: 'no', biz: 'weak', complaint: 47,
  guaranteed: 'yes', manip: 'yes'
}));

t('仅结构无收益率', mk({
  level: 3, fee: 10800, biz: 'none', legal: 'yes'
}));

t('日化100%', mk({ daily: 100 }));

t('只有项目名', mk({}));

t('合规项目', mk({
  icp: 'company', match: 'yes', paid: 200, status: 'normal', domain: 48,
  daily: 0.03, level: 1, cap: true, fee: 0, lock: 'no', guaranteed: 'no',
  wd: 'no', payee: 'company', cust: 'yes', biz: 'real', manip: 'no',
  complaint: 2, legal: 'no'
}));

console.log('\n规则总数:', e.RULES.length);
console.log('示例项目:', e.KEYS.join(', '));
