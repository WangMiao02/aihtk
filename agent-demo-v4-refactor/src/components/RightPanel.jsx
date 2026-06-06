import { TimelineNode } from './SharedUI'

export function RightPanel({ tab, snapshot, timeline }) {
  const bItems = [
    { label: '入住率',   value: snapshot.occupancy        || '—' },
    { label: '营收',     value: snapshot.revenue          || '—' },
    { label: '折扣率',   value: snapshot.discount         || '—' },
    { label: '经营状态', value: snapshot.operationStatus  || '运营正常 ✓' },
  ]

  const cItems = [
    { label: '入住日期', value: snapshot.date  || '—' },
    { label: '房型',     value: snapshot.room  || '—' },
    { label: '总金额',   value: snapshot.total || '—' },
    { label: '打车',     value: snapshot.car   || '—' },
  ]

  const items = tab === 'B' ? bItems : cItems
  const label = tab === 'B' ? '⊞ 经营快照' : '⊞ 行程快照'

  return (
    <aside className="col-right">
      <div className="panel-hd">
        <span className="panel-hd-label">{label}</span>
      </div>

      <div className="snap-grid">
        {items.map(({ label: l, value }) => (
          <div key={l} className="snap-card">
            <div className="snap-label">{l}</div>
            <div className="snap-val">{value}</div>
          </div>
        ))}
      </div>

      <div className="tl-wrap">
        <div className="tl-section-label">事件时间线</div>
        {timeline.map((item, i) => (
          <div key={i} className="tl-item">
            <TimelineNode type={item.dot} />
            <div>
              <div className="tl-ttl">{item.title}</div>
              <div className="tl-desc">{item.desc}</div>
              <div className="tl-time">{item.time}</div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
