import { AgentCard, HotelCard, COLOR } from './SharedUI'
import { C_HOTELS, C_ROOMS } from '../data/cDemoData'

export function HotelListCard({ onPickHotel, chosenHotel, step }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxWidth: '90%', alignSelf: 'flex-start', animation: 'slideIn .3s ease' }}>
      {C_HOTELS.map(hotel => (
        <HotelCard
          key={hotel.name}
          hotel={hotel}
          onSelect={() => onPickHotel(hotel)}
          disabled={step !== 1 || (chosenHotel && chosenHotel.name !== hotel.name)}
        />
      ))}
    </div>
  )
}

export function RoomSelectionCard({ hotel, onPickRoom, disabled }) {
  return (
    <AgentCard
      tag="选择房型"
      title={hotel.name}
      subtitle="📅 6月2日 · 1晚入住"
      rows={[
        { label: '大床房（含早）',  value: C_ROOMS[0].price, color: COLOR.blue },
        { label: '双床房（不含早）', value: C_ROOMS[1].price },
        { label: '免费取消',        value: '今日24:00前',    color: COLOR.greenDark },
      ]}
      buttons={C_ROOMS.map(room => ({
        text:     room.label.includes('大床') ? `大床房 ${room.price}` : `双床房 ${room.price}`,
        variant:  room.label.includes('大床') ? 'pri' : 'sec',
        disabled,
        onClick:  () => onPickRoom(room, hotel),
      }))}
    />
  )
}

export function BookingSuccessCard({ hotel, room }) {
  return (
    <AgentCard
      tag="预订成功" tagColor="green"
      title={hotel.name}
      rows={[
        { label: '房型',   value: room.label },
        { label: '入住',   value: '6月2日 14:00后' },
        { label: '退房',   value: '6月3日 12:00前' },
        { label: '总金额', value: room.price, color: COLOR.blue },
      ]}
      buttons={[{ text: '订单已确认', variant: 'suc', disabled: true }]}
    />
  )
}

export function RideCard({ hotel, onCallCar, onSkipCar, disabled }) {
  return (
    <AgentCard
      tag="打车联动" tagColor="amber" borderColor={COLOR.amber}
      title="要打车去酒店吗？"
      subtitle={`📍 距${hotel.name}约12.3km`}
      rows={[
        { label: '快车', value: '¥38–45 · 等待约3分钟' },
        { label: '优享', value: '¥52–60 · 等待约5分钟' },
      ]}
      buttons={[
        { text: '一键叫车', onClick: onCallCar, disabled },
        { text: '不用了',   variant: 'sec', onClick: onSkipCar, disabled },
      ]}
    />
  )
}

export function CarSuccessCard() {
  return (
    <AgentCard
      tag="叫车成功" tagColor="green"
      title="司机正在赶来"
      rows={[
        { label: '车牌',     value: '沪A · 88235' },
        { label: '车型',     value: '大众帕萨特（白）' },
        { label: '预计等待', value: '约3分钟', color: COLOR.greenDark },
        { label: '预估费用', value: '¥41',     color: COLOR.blue },
      ]}
      buttons={[{ text: '✓ 全部搞定！', variant: 'suc', disabled: true }]}
    />
  )
}
