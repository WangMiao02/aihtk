import { nowTime } from '../utils'

export const CDATA = {
  tripInfo: {
    trainNo:    'G1',
    departure:  '07:00',
    arrival:    '11:30',
    from:       '北京南',
    to:         '上海虹桥',
    seatType:   '二等座靠窗',
    price:      '¥553',
    date:       '周三 6月4日',
  },

  petBoardingInfo: {
    petName:   '豆豆',
    storeName: '喵星人之家',
    boardType: '散养位',
    days:      2,
    price:     '¥300',
  },

  hotelInfo: {
    hotelName:     '全季虹桥店',
    pricePerNight: '¥389',
    roomType:      '标准大床房',
    checkIn:       '6月4日',
    checkOut:      '6月6日',
    nights:        2,
  },

  hairSalonInfo: {
    storeName: 'MOMENT SALON',
    stylist:   'Tony 老师',
    time:      '周三 15:00',
    service:   '剪+洗',
    price:     '¥128',
  },

  tripSummary: [
    { label: '🚄 高铁',     value: 'G1·07:00 北京南→虹桥' },
    { label: '🐱 豆豆寄养', value: '喵星人之家·2天 ¥300' },
    { label: '🏨 酒店',     value: '全季虹桥·2晚 ¥778' },
    { label: '✂️ 理发',     value: 'MOMENT SALON·周三15:00 ¥128' },
    { label: '⏰ 明早闹钟', value: '06:00 · 叫车6:10到楼下' },
  ],

  arrivalRide: {
    from:     '上海虹桥站',
    to:       '全季虹桥店',
    distance: '3.2km',
    time:     '约12分钟',
    price:    '约¥18',
  },

  lunchRecommend: {
    restaurants: [
      { name: '渝是乎', rating: '4.8', price: '¥38/人', distance: '280米', recommended: true },
      { name: '老盛昌', rating: '4.7', price: '¥22/人', distance: '450米', recommended: false },
    ],
    coupon: '满25减5（已自动匹配）',
  },

  hairReminder: {
    storeName: 'MOMENT SALON',
    time:      '15:00',
    address:   '武康路101号',
  },

  cityExplore: {
    routes: [
      { name: '武康路', distance: '步行15分钟', highlight: '梧桐街道·网红打卡', petFriendly: true },
      { name: '外滩',   distance: '打车10分钟', highlight: '黄浦江夜景·地标建筑', petFriendly: false },
    ],
  },

  dayOneBudget: {
    expenses: [
      { label: '高铁·G1',         amount: '¥553', type: '差旅' },
      { label: '打车·虹桥到酒店',  amount: '¥18',  type: '差旅' },
      { label: '午餐·渝是乎',      amount: '¥33',  type: '个人' },
      { label: '理发·MOMENT',     amount: '¥128', type: '个人' },
    ],
    bizTotal:      '¥571',
    personalTotal: '¥161',
    total:         '¥732',
  },

  expenseClassify: {
    bizItems:      ['高铁·G1  ¥553', '打车·虹桥到酒店  ¥18'],
    personalItems: ['午餐·渝是乎  ¥33', '理发·MOMENT  ¥128'],
    bizTotal:      '¥571',
    personalTotal: '¥161',
  },
}

export const INITIAL_C_SNAPSHOT = { date: '—', room: '—', total: '—', car: '—' }

export const INITIAL_C_TIMELINE = [
  { title: '等待操作', desc: '演示尚未开始', dot: '', time: nowTime() },
]
