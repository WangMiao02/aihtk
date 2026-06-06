export const BDATA = {
  agentName: '栖云助手',
  hotelName: '栖云·青芝坞小院',

  dailyReport: {
    date: '6月1日（昨日）',
    occupancy: '87%',
    revenue: '¥2,840',
    roomNights: 3,
    revpar: '¥568',
    rating: '4.8',
    newReviews: 2,
    sampleCount: 12,
    competitorAvg: '82折',
    merchantCurrent: '92折',
    gap: '10%',
  },

  competitorInsight: {
    sampleCount: 12,
    radiusKm: 3,
    basis: '非节假日·近7日',
    competitorAvg: '82折',
    merchantCurrent: '92折',
    gap: '10%',
    currentPrice: 568,
    suggestedDiscount: '88折',
    suggestedPrice: 500,
    estimatedWeeklyGain: '+¥340',
  },

  fullHouseSwitch: {
    roomType: '湖景大床房（A201）',
    status: '今日预订已满',
    suggestion: '建议下架停止接单，避免超卖',
  },

  review: {
    guestName: '张先生',
    rating: 2,
    roomNumber: 'A201',
    roomType: '湖景大床房',
    date: '6月2日',
    issueType: '硬件问题（空调不制冷）',
    content: '空调完全不制冷，大热天根本睡不着，住了一晚，很失望',
    draftReply: '张先生您好，非常抱歉入住体验不佳。我们已第一时间安排维修团队今日检修空调。感谢您的反馈，期待您再次到访栖云小院。',
  },

  maintenanceSwitch: {
    roomNumber: 'A201',
    roomType: '湖景大床房',
    issue: '空调不制冷',
    source: '房客差评（6月2日）',
  },

  maintenance: {
    roomNumber: 'A201',
    roomType: '湖景大床房',
    issue: '空调不制冷',
    source: '房客差评（6月2日）',
    technician: '李师傅',
    scheduledTime: '今日 14:00–16:00',
  },

  roomRelist: {
    roomNumber: 'A201',
    roomType: '湖景大床房',
    technicianNote: '李师傅已完成空调维修，制冷恢复正常',
    suggestion: '建议立即恢复上架，重新接单',
  },

  campaign: {
    name: '避暑季特惠',
    platform: '美团民宿',
    period: '6月15日–8月31日',
    benefit: '流量加权 +30%',
    subsidyRate: '平台补贴15%',
    deadline: '6月8日 23:59',
    requirement: '折扣率 ≤88折',
  },

  dailyReportAfter: {
    date: '6月9日（一周后）',
    occupancy: '94%',
    revenue: '¥3,180',
    roomNights: 3,
    revpar: '¥499',
    rating: '4.9',
    a201Status: '维修完成 · 已恢复上架',
    campaignStatus: '避暑季报名成功 ✓',
  },
}

export const INITIAL_B_SNAPSHOT = {
  occupancy: '—',
  revenue: '—',
  discount: '—',
  operationStatus: '运营正常 ✓',
}

export const INITIAL_B_TIMELINE = [
  { title: '等待启动', desc: '演示将自动开始', dot: '', time: '—' },
]
