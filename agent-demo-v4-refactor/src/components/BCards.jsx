import { AgentCard, Tag, CardButton, COLOR } from './SharedUI'
import { BDATA } from '../data/bDemoData'

export function DailyReportCard({ payload, onViewPromotion, disabled }) {
  return (
    <AgentCard
      tag="晨间日报"
      title={`${BDATA.hotelName} · ${payload.date}`}
      rows={[
        { label: '入住率',  value: payload.occupancy,                                      color: COLOR.greenDark },
        { label: '营收',    value: payload.revenue,                                        color: COLOR.blue },
        { label: '间夜数',  value: `${payload.roomNights} 间` },
        { label: 'RevPAR', value: payload.revpar },
        { label: '评分',    value: `${payload.rating} ⭐（${payload.newReviews}条新评价）` },
      ]}
      buttons={[{ text: '查看调价建议 →', onClick: onViewPromotion, disabled }]}
    >
      <div style={{
        background: COLOR.amberPale, border: `0.5px solid ${COLOR.amber}`,
        borderRadius: 6, padding: '6px 8px', marginTop: 5, marginBottom: 2,
      }}>
        <div style={{ fontSize: 10, fontWeight: 500, color: COLOR.amberDark, marginBottom: 2 }}>⚡ 竞品动态</div>
        <div style={{ fontSize: 11, color: COLOR.textMid }}>
          周边{payload.sampleCount}家均折扣 <b>{payload.competitorAvg}</b>，您当前 <b>{payload.merchantCurrent}</b>，差距 {payload.gap}
        </div>
      </div>
    </AgentCard>
  )
}

export function PromoAdvisorCard({ payload }) {
  return (
    <AgentCard
      tag="调价建议" tagColor="amber" borderColor={COLOR.amber}
      title="建议跟进周边折扣力度"
      subtitle={`${payload.sampleCount}家竞品 · ${payload.radiusKm}km内 · ${payload.basis}`}
      rows={[
        { label: '竞品均值',       value: payload.competitorAvg,       color: COLOR.greenDark },
        { label: '你当前',         value: payload.merchantCurrent,     color: COLOR.redDark },
        { label: '建议调整为',     value: payload.suggestedDiscount,   color: COLOR.blue },
        { label: '调整后均价',     value: `¥${payload.suggestedPrice}/间夜` },
        { label: '预计周营收变化', value: payload.estimatedWeeklyGain, color: COLOR.greenDark },
      ]}
    />
  )
}

export function FullHouseSwitchCard({ payload }) {
  return (
    <AgentCard
      tag="满房提醒" tagColor="amber" borderColor={COLOR.amber}
      title={`${payload.roomType} · ${payload.status}`}
      rows={[{ label: '建议操作', value: payload.suggestion }]}
      warning="若不下架，新订单仍可能进入导致超卖"
    />
  )
}

export function ReviewAlertBubble({ payload }) {
  return (
    <div style={{
      alignSelf: 'flex-start', maxWidth: '90%',
      background: COLOR.redPale, border: `1.5px solid ${COLOR.red}`,
      borderRadius: 10, padding: '8px 12px', animation: 'slideIn .3s ease',
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: COLOR.redDark, marginBottom: 3 }}>
        ⚠️ 新差评 · {payload.roomNumber} {payload.roomType}
      </div>
      <div style={{ fontSize: 11, color: COLOR.textMid }}>
        {payload.guestName} ★★☆☆☆ · "{payload.content.slice(0, 24)}…"
      </div>
      <div style={{ fontSize: 10, color: '#999', marginTop: 3 }}>{payload.date}</div>
    </div>
  )
}

export function ReviewReplyCard({ payload }) {
  return (
    <AgentCard
      tag="差评回复草稿" tagColor="red" borderColor={COLOR.red}
      title={`${payload.guestName} ★★☆☆☆ · ${payload.roomNumber}`}
      subtitle={`来源：房客差评（${payload.date}）`}
    >
      <div style={{ fontSize: 11, color: COLOR.textMid, lineHeight: 1.5, marginTop: 4, marginBottom: 2 }}>
        {payload.draftReply}
      </div>
    </AgentCard>
  )
}

export function MaintenanceSwitchCard({ payload }) {
  return (
    <AgentCard
      tag="建议临时下架" tagColor="amber" borderColor={COLOR.amber}
      title={`${payload.roomNumber} · ${payload.roomType}`}
      subtitle={`来源：${payload.source}`}
      rows={[
        { label: '故障',   value: payload.issue },
        { label: '影响',   value: '暂停接单·防止二次差评' },
      ]}
      warning="不下架可能被再次订出，加重差评风险"
    />
  )
}

export function MaintenanceCard({ payload }) {
  return (
    <AgentCard
      tag="维修工单"
      title={`${payload.roomNumber} · ${payload.issue}`}
      subtitle={`来源：${payload.source}`}
      rows={[
        { label: '故障类型', value: payload.issue },
        { label: '维修师傅', value: payload.technician },
        { label: '预约时间', value: payload.scheduledTime },
      ]}
    />
  )
}

// Act 2 checklist progress bar — always visible during act 2
export function Act2ChecklistBar({ tasks }) {
  const taskDefs = [
    { key: 'reviewReply', label: '差评回复' },
    { key: 'roomSwitch',  label: '维修下架' },
    { key: 'maintenance', label: '安排维修' },
  ]
  const allDone = taskDefs.every(td => tasks[td.key] !== null)

  return (
    <div style={{
      alignSelf: 'stretch', margin: '4px 0',
      background: 'rgba(255,255,255,0.75)', border: `0.5px solid ${COLOR.borderMd}`,
      borderRadius: 8, padding: '7px 12px',
      display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
    }}>
      <span style={{ fontSize: 10, color: COLOR.textHint, flexShrink: 0 }}>任务进度</span>
      {taskDefs.map(td => {
        const state = tasks[td.key]
        const done = state !== null
        return (
          <span key={td.key} style={{
            fontSize: 11, display: 'flex', alignItems: 'center', gap: 4,
            color: done ? COLOR.greenDark : COLOR.textMid,
          }}>
            <span style={{
              fontSize: 12,
              color: done ? COLOR.green : '#CBD5E1',
            }}>
              {done ? '✓' : '○'}
            </span>
            {td.label}
          </span>
        )
      })}
      {allDone && (
        <span style={{ marginLeft: 'auto', fontSize: 10, color: COLOR.blue }}>
          → 进入下一幕…
        </span>
      )}
    </div>
  )
}

export function RoomRelistCard({ payload }) {
  return (
    <AgentCard
      tag="维修完成 · 建议上架" tagColor="green" borderColor={COLOR.green}
      title={`${payload.roomNumber} · ${payload.roomType}`}
      subtitle={payload.technicianNote}
      rows={[
        { label: '维修结果', value: '空调恢复正常', color: COLOR.greenDark },
        { label: '建议操作', value: payload.suggestion },
      ]}
    />
  )
}

export function CampaignCard({ payload }) {
  return (
    <AgentCard
      tag="平台活动"
      title={payload.name}
      subtitle={`${payload.platform} · ${payload.period}`}
      rows={[
        { label: '流量奖励', value: payload.benefit,     color: COLOR.greenDark },
        { label: '平台补贴', value: payload.subsidyRate },
        { label: '参与要求', value: payload.requirement },
        { label: '报名截止', value: payload.deadline,    color: COLOR.redDark },
      ]}
    />
  )
}

export function TimeJumpDivider({ from, to }) {
  return (
    <div style={{
      alignSelf: 'center', fontSize: 11, color: COLOR.textMid,
      padding: '4px 16px', background: 'rgba(255,255,255,0.7)',
      borderRadius: 20, border: `0.5px solid ${COLOR.borderMd}`, margin: '4px 0',
    }}>
      ⏩ {from} → {to}
    </div>
  )
}

export function DailyReportAfterCard({ payload }) {
  return (
    <AgentCard
      tag="一周复盘" tagColor="green"
      title={`${BDATA.hotelName} · ${payload.date}`}
      rows={[
        { label: '入住率',   value: payload.occupancy,      color: COLOR.greenDark },
        { label: '营收',     value: payload.revenue,        color: COLOR.blue },
        { label: 'RevPAR',  value: payload.revpar },
        { label: 'A201状态', value: payload.a201Status,     color: COLOR.green },
        { label: '活动状态', value: payload.campaignStatus, color: COLOR.blue },
      ]}
      buttons={[{ text: '✓ 经营闭环完成', variant: 'suc', disabled: true }]}
    />
  )
}
