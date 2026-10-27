/**
 * 制度模式库 —— 从已判决案例里提炼的 14 类典型结构
 *
 * 为什么需要它：
 *   案例库解决「这个项目叫什么」，模式库解决「它属于哪一类」。
 *   用户往往只给一个名字或几句宣传话术，靠 21 条规则算分信息不够；
 *   但如果能先匹配到模式原型，就能给出方向性判断：
 *   「这像是刷单返利盘，这类盘平均存活 3-6 个月」。
 *
 * 数据来源：
 *   全部从 cases.js 里的已判决案例 + 公开判决认定的事实中提炼，
 *   不包含任何未判决项目的推测。
 */
window.PATTERNS = [

  {
    id: 'mutual',
    name: '互助盘 / 排队盘',
    aka: ['互助盘', '互助理财', '排队返利', 'MMM 类'],
    level: '极高',
    core: ['门槛费买入场资格', '排队匹配打款', '日化 1%–2%', '无真实标的'],
    keys: ['互助', '排队', '匹配', '打款', '互帮互助', '爱心', '善种子', '布施', '受助'],
    cycle: '3–12 个月',
    tell: '你打钱给别人，别人打钱给你，中间只有平台在抽水。没有借款人、没有标的、没有利息来源。',
    deadGiveaway: '「排队」和「匹配」这两个词一出现，基本可以定性。',
    cases: ['善心汇'],
    weight: { fee: 3, level: 2, daily: 3, biz: 3 }
  },

  {
    id: 'brush-order',
    name: '刷单返利盘',
    aka: ['刷单盘', '任务返佣', '垫付刷单'],
    level: '极高',
    core: ['日化 1%–2%', '短周期（7 天/一轮）', '三级以上分销', '前期小额返现建立信任'],
    keys: ['刷单', '任务', '垫付', '返佣', '接单', '佣金', '商家代付', '流水'],
    cycle: '1–6 个月',
    tell: '前几单真的返，让你尝到甜头；等你垫付金额变大，就以「任务未完成」「操作失误」为由冻结。',
    deadGiveaway: '「垫付」+「返佣」+ 短周期，三件套齐了就是刷单盘。',
    cases: [],
    weight: { daily: 4, level: 2, fee: 1, wd: 2 }
  },

  {
    id: 'grab-order',
    name: '抢单盘 / 抢拍盘',
    aka: ['抢单盘', '抢拍盘', '秒杀转卖'],
    level: '极高',
    core: ['抢购虚拟商品', '平台承诺溢价回购或转卖', '门槛费', '击鼓传花式向下传递'],
    keys: ['抢单', '抢拍', '秒杀', '抢购', '转卖', '溢价', '接盘', '商品流转'],
    cycle: '1–3 个月',
    tell: '你抢到的「商品」根本不会到手，只是个凭证。平台让你加价转卖给下一个人，最后一个人接盘。',
    deadGiveaway: '「抢到就赚」+「平台回收」= 击鼓传花。',
    cases: [],
    weight: { fee: 3, guaranteed: 3, biz: 3, level: 1 }
  },

  {
    id: 'cloud-mining',
    name: '云矿机 / 算力盘',
    aka: ['云挖矿', '算力合约', '矿机租赁'],
    level: '高',
    core: ['固定日收益', '算力无法验证', '本金锁仓', '收益可复投'],
    keys: ['矿机', '算力', '挖矿', '云算力', '哈希', '算力合约', '矿场', '电费'],
    cycle: '6–18 个月',
    tell: '真正的挖矿收益随币价和难度波动，不可能固定。承诺固定日收益，说明它卖的不是算力，是理财。',
    deadGiveaway: '拿不出矿场地址、电费单、算力分配凭据 —— 收益来源不可核。',
    cases: [],
    weight: { daily: 3, lock: 3, biz: 3, guaranteed: 2 }
  },

  {
    id: 'nft',
    name: '数藏平台 / NFT 盘',
    aka: ['数字藏品', 'NFT', '元宇宙藏品'],
    level: '中—高',
    core: ['平台自营账号自买自卖', '承诺溢价回购', '邀请返佣', '底层标的无价值'],
    keys: ['数字藏品', '藏品', '首发', '盲盒', '空投', '二级市场', '流转', '合成', '赋能'],
    cycle: '3–12 个月',
    tell: '价格不是市场形成的，是平台自己挂单抬起来的。你看到的浮盈，在它关掉交易那一刻就是 0。',
    deadGiveaway: '平台自营账号在二级市场收购自家藏品 —— 自买自卖。',
    cases: ['AI数藏集资诈骗'],
    weight: { manip: 4, guaranteed: 3, level: 1, biz: 2 }
  },

  {
    id: 'consume-rebate',
    name: '消费返利 / 全返盘',
    aka: ['消费全返', '消费返利', '购物返本'],
    level: '高',
    core: ['消费金额全额或高比例返还', '按日/按周期返还', '多层级分销', '线下门店包装'],
    keys: ['消费全返', '全返', '消费返利', '购物返', '返本', '积分', '消费商', '云返'],
    cycle: '1–3 年',
    tell: '商品利润撑不起全额返还，差额只能由后来者的消费补。本质是拿后人的钱返给前人。',
    deadGiveaway: '「消费多少返多少」—— 商业上不成立，除非它压根没打算靠卖货赚钱。',
    cases: ['云联惠', '云付通', '悦花越有'],
    weight: { daily: 1, level: 2, guaranteed: 2, biz: 3 }
  },

  {
    id: 'forex',
    name: '外汇 / 黄金 / 期货托管盘',
    aka: ['外汇托管', '黄金交易', '跟单盘'],
    level: '极高',
    core: ['门槛费（常以美元计）', '邀请码层级', '宣称专业操盘', '无真实交易记录'],
    keys: ['外汇', '黄金', '期货', '托管', '跟单', '操盘', '交易信号', 'MT4', 'MT5'],
    cycle: '1–2 年',
    tell: '判决书里最常见的一句认定：「平台实际未进行外汇交易，无法获得收益支持返利」。',
    deadGiveaway: '要它出金交所/银行的成交回单。出不来，就是没交易。',
    cases: ['海汇国际'],
    weight: { fee: 3, level: 3, biz: 3, daily: 1 }
  },

  {
    id: 'coin-ponzi',
    name: '虚拟币传销 / 存币生息',
    aka: ['存币生息', '搬砖套利', '边玩边赚', '通缩增值'],
    level: '极高',
    core: ['存币给固定收益', '拉人返佣多层', '所谓套利从未真实发生', '境外服务器'],
    keys: ['存币', '生息', '搬砖', '套利', '边玩边赚', '通缩', '销毁', '质押', '挖矿收益', '钱包'],
    cycle: '6–24 个月',
    tell: '币圈盘子的收益不来自交易，来自新会员充进来的币。层级越深，崩得越快。',
    deadGiveaway: '层级超过 10 层就足够进刑法；PlusToken 是 3293 层。',
    cases: ['PlusToken', '维卡币', '五行币'],
    weight: { level: 4, daily: 3, biz: 3, fee: 2 }
  },

  {
    id: 'pre-ipo',
    name: '原始股 / 期权盘',
    aka: ['原始股', '内部股', '期权激励', '上市分红'],
    level: '高',
    core: ['承诺上市', '卖「内部股」或期权', '拉人奖励', '公司无实际经营'],
    keys: ['原始股', '内部股', '期权', '上市', '股权', '分红', 'IPO', '新三板', '纳斯达克'],
    cycle: '1–3 年',
    tell: '真原始股轮不到微信群卖。能公开叫卖的「内部股」，要么没上市计划，要么公司本身是空壳。',
    deadGiveaway: '查它有没有股改、有没有券商辅导备案。没有就是空话。',
    cases: [],
    weight: { guaranteed: 3, level: 2, biz: 3, fee: 2 }
  },

  {
    id: 'ethnic-assets',
    name: '民族资产解冻 / 国家项目',
    aka: ['民族资产解冻', '国家扶贫项目', '中国梦平台'],
    level: '极高',
    core: ['伪造红头文件', '小额入门费', '承诺巨额回报', '针对中老年人'],
    keys: ['民族资产', '解冻', '国家项目', '扶贫', '中国梦', '红头文件', '守库老人', '李烈钧', '数字货币推广'],
    cycle: '数月至数年',
    tell: '这个骗局从 1970 年代就有了。凡是说「交几百块，解冻后分几百万」的，全是假的。',
    deadGiveaway: '国家项目不会通过微信群收会员费。这一条就能否掉全部。',
    cases: [],
    weight: { fee: 2, guaranteed: 3, biz: 3, level: 1 }
  },

  {
    id: 'elderly',
    name: '养老 / 收藏品骗局',
    aka: ['收藏品投资', '以房养老', '养老床位'],
    level: '高',
    core: ['高价卖廉价商品', '承诺代拍卖或回购', '情感攻势', '针对老年人'],
    keys: ['收藏', '字画', '纪念币', '玉器', '养老', '床位', '以房养老', '代拍卖', '升值空间'],
    cycle: '1–3 年',
    tell: '真藏品不需要承诺回购，假藏品才需要。凡是「买了我们帮你拍卖赚差价」的，都是套路。',
    deadGiveaway: '「投资有返利」+「到期代拍卖」，两个承诺同时出现就是骗局。',
    cases: ['收藏品字画诈骗'],
    weight: { guaranteed: 3, biz: 3, level: 1 }
  },

  {
    id: 'charity',
    name: '公益 / 慈善盘',
    aka: ['慈善互助', '爱心盘', '扶贫盘'],
    level: '极高',
    core: ['以公益为名', '门槛费', '层级返利', '把行善包装成投资'],
    keys: ['公益', '慈善', '爱心', '扶贫', '济困', '日行一善', '善款', '布施'],
    cycle: '6–18 个月',
    tell: '善心汇就是这么干的：以「扶贫济困、均富共生」为名，收 300 元「善种子」，598 万人受损。',
    deadGiveaway: '做公益要你交钱、还要你拉人 —— 这两条同时出现，就不是公益。',
    cases: ['善心汇'],
    weight: { fee: 3, level: 3, biz: 3 }
  },

  {
    id: 'fake-exchange',
    name: '假交易所 / 带单盘',
    aka: ['带单老师', '合约交易所', '黑平台'],
    level: '极高',
    core: ['后台可改价', '老师带单', '诱导加杠杆', '出金设障'],
    keys: ['带单', '老师', '喊单', '合约', '杠杆', '爆仓', '交易所', '出金', '滑点', '客损'],
    cycle: '数月',
    tell: '你的亏损就是平台的收入（客损模式）。它不需要你赢，它只需要你不断加仓。',
    deadGiveaway: '出金要交「税费」「保证金」—— 真交易所不会这么干。',
    cases: [],
    weight: { manip: 4, wd: 3, biz: 2 }
  },

  {
    id: 'fake-p2p',
    name: '假 P2P / 线下理财',
    aka: ['P2P', '线下理财', '财富公司'],
    level: '高',
    core: ['承诺年化 8%–20%', '虚构债权标的', '线下门店拉客', '资金池'],
    keys: ['理财', 'P2P', '出借', '债权', '年化', '保本保息', '财富管理', '资产管理', '门店'],
    cycle: '1–3 年',
    tell: '真 P2P 早已全行业清退。现在还在卖「P2P 理财」的，不是骗子就是违法。',
    deadGiveaway: '查它有没有金融牌照。没有牌照吸收公众资金，就是非法吸收公众存款。',
    cases: ['e租宝', '钱宝网', '善林金融', '团贷网', '阜兴系', '中晋系', '盛大金禧', '泛亚有色'],
    weight: { guaranteed: 3, biz: 3, daily: 1 }
  }
];

/* 别名反查 */
window.PATTERN_ALIAS = {};
window.PATTERNS.forEach(function (p) {
  window.PATTERN_ALIAS[p.name.toLowerCase()] = p.id;
  (p.aka || []).forEach(function (a) {
    window.PATTERN_ALIAS[a.toLowerCase()] = p.id;
  });
});

/**
 * 模式匹配 —— 靠关键词命中 + 结构化字段双重打分
 * @param {string} text 用户提交的原文
 * @param {object} facts 已解析的事实
 * @returns {Array} 按匹配度排序的模式列表（最多 3 个）
 */
window.matchPatterns = function (text, facts) {
  const t = (text || '').toLowerCase();
  const results = [];

  window.PATTERNS.forEach(function (p) {
    let score = 0;
    const hitKeys = [];

    // ① 关键词命中
    (p.keys || []).forEach(function (k) {
      if (t.indexOf(k.toLowerCase()) >= 0) {
        score += 2;
        hitKeys.push(k);
      }
    });

    // ② 结构化字段印证
    const w = p.weight || {};
    if (w.daily && facts.daily !== null && facts.daily !== undefined) score += w.daily;
    if (w.level && facts.level) score += w.level;
    if (w.fee && facts.fee) score += w.fee;
    if (w.lock && facts.lock === 'yes') score += w.lock;
    if (w.guaranteed && facts.guaranteed === 'yes') score += w.guaranteed;
    if (w.biz && (facts.biz === 'none' || facts.biz === 'weak')) score += w.biz;
    if (w.manip && facts.manip === 'yes') score += w.manip;
    if (w.wd && facts.wd === 'yes') score += w.wd;

    if (score >= 4) {
      results.push({
        id: p.id,
        name: p.name,
        aka: p.aka,
        level: p.level,
        score: score,
        hitKeys: hitKeys,
        core: p.core,
        cycle: p.cycle,
        tell: p.tell,
        deadGiveaway: p.deadGiveaway,
        cases: p.cases
      });
    }
  });

  return results.sort(function (a, b) { return b.score - a.score; }).slice(0, 3);
};
