App({
  globalData: {
    version: '1.0.0',
    account: {
      name: '金融防骗预警',
      wechat: 'janecoolman01'
    }
  },

  onLaunch() {
    // 记录一次启动，仅本地存储，不上传任何数据
    try {
      const n = wx.getStorageSync('launch_count') || 0;
      wx.setStorageSync('launch_count', n + 1);
    } catch (e) {
      // 忽略存储异常
    }
  }
});
