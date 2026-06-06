import { useState, useEffect, useRef } from 'react'
import { nowTime } from '../utils'

export const COLOR = {
  chatBg:     '#AEE2FF',
  panelBg:    '#4BB8FA',
  white:      '#FFFFFF',
  textDark:   '#1a1a1a',
  textMid:    '#555555',
  textHint:   '#888888',
  blue:       '#0369A1',
  blueLight:  '#E0F4FF',
  bluePale:   '#F0FAFF',
  border:     '#AEE2FF',
  borderMd:   '#7DD3F8',
  green:      '#10B981',
  greenPale:  '#ECFDF5',
  greenDark:  '#065F46',
  amber:      '#F59E0B',
  amberPale:  '#FFFBEB',
  amberDark:  '#B45309',
  red:        '#EF4444',
  redPale:    '#FEF2F2',
  redDark:    '#B91C1C',
}

export function Tag({ children, color = 'blue' }) {
  const styles = {
    blue:  { bg: COLOR.blueLight, text: COLOR.blue },
    green: { bg: COLOR.greenPale, text: COLOR.greenDark },
    amber: { bg: COLOR.amberPale, text: COLOR.amberDark },
    red:   { bg: COLOR.redPale,   text: COLOR.redDark },
  }
  const { bg, text } = styles[color] || styles.blue
  return (
    <span style={{
      fontSize: 10, fontWeight: 500, color: text, background: bg,
      padding: '2px 7px', borderRadius: 4, display: 'inline-block', marginBottom: 5,
    }}>
      {children}
    </span>
  )
}

export function CardButton({ text, variant = 'pri', onClick, disabled }) {
  const variantStyles = {
    pri: { background: COLOR.panelBg,   color: COLOR.white,     border: 'none' },
    sec: { background: COLOR.bluePale,  color: COLOR.textDark,  border: `0.5px solid ${COLOR.border}` },
    suc: { background: COLOR.greenPale, color: COLOR.greenDark, border: 'none' },
  }
  const style = variantStyles[variant] || variantStyles.pri
  return (
    <button
      onClick={disabled ? undefined : onClick}
      style={{
        flex: 1, padding: '6px 4px', fontSize: 11, fontWeight: 500,
        borderRadius: 6, cursor: disabled ? 'default' : 'pointer',
        textAlign: 'center', opacity: disabled ? 0.5 : 1,
        transition: 'opacity .15s', ...style,
      }}
    >
      {text}
    </button>
  )
}

export function AgentCard({ tag, tagColor, title, subtitle, rows, warning, children, buttons, borderColor }) {
  return (
    <div style={{
      background: COLOR.white,
      border: `0.5px solid ${borderColor || COLOR.border}`,
      borderRadius: 12, maxWidth: '92%', alignSelf: 'flex-start',
      overflow: 'hidden', animation: 'slideIn .3s ease',
    }}>
      <div style={{ padding: '9px 12px 8px', borderBottom: `0.5px solid #E0F4FF` }}>
        {tag && <Tag color={tagColor}>{tag}</Tag>}
        {title && <div style={{ fontSize: 13, fontWeight: 500, color: COLOR.textDark }}>{title}</div>}
        {subtitle && <div style={{ fontSize: 11, color: COLOR.textMid, marginTop: 2 }}>{subtitle}</div>}
      </div>
      {rows && (
        <div style={{ padding: '9px 12px' }}>
          {rows.map((row, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between',
              fontSize: 11, marginBottom: i === rows.length - 1 ? 0 : 4,
            }}>
              <span style={{ color: COLOR.textMid }}>{row.label}</span>
              <span style={{ fontWeight: 500, color: row.color || COLOR.textDark }}>{row.value}</span>
            </div>
          ))}
        </div>
      )}
      {children && <div style={{ padding: '0 12px 9px' }}>{children}</div>}
      {warning && (
        <div style={{
          margin: '0 12px 8px', fontSize: 11, color: COLOR.redDark,
          background: COLOR.redPale, padding: '5px 8px', borderRadius: 5,
        }}>
          ⚠️ {warning}
        </div>
      )}
      {buttons && (
        <div style={{ display: 'flex', gap: 5, padding: '8px 12px', borderTop: `0.5px solid #E0F4FF` }}>
          {buttons.map((btn, i) => <CardButton key={i} {...btn} />)}
        </div>
      )}
    </div>
  )
}

export function ChatBubble({ who, children, time }) {
  const isAgent = who === 'agent'
  return (
    <div style={{ alignSelf: isAgent ? 'flex-start' : 'flex-end', maxWidth: '85%', animation: 'slideIn .25s ease' }}>
      <div style={{
        fontSize: 12, lineHeight: 1.55, padding: '8px 12px', borderRadius: 14,
        borderBottomLeftRadius: isAgent ? 3 : 14,
        borderBottomRightRadius: isAgent ? 14 : 3,
        background: isAgent ? COLOR.white : COLOR.panelBg,
        color: isAgent ? COLOR.textDark : COLOR.white,
      }}>
        {children}
      </div>
      <div style={{
        fontSize: 10, color: '#5BAFD6', marginTop: 2, padding: '0 3px',
        textAlign: isAgent ? 'left' : 'right',
      }}>
        {time || nowTime()}
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div style={{
      alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 4,
      padding: '8px 12px', background: COLOR.white,
      borderRadius: 14, borderBottomLeftRadius: 3,
    }}>
      {[0, 0.15, 0.3].map((delay, i) => (
        <span key={i} style={{
          width: 5, height: 5, borderRadius: '50%', background: COLOR.border,
          display: 'inline-block', animation: `blink 1s ${delay}s infinite`,
        }} />
      ))}
    </div>
  )
}

export function SkillTrace({ trace }) {
  return (
    <div className="skill-trace">
      {trace ? (
        <>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', background: COLOR.green, flexShrink: 0,
          }} />
          <span style={{ fontFamily: 'monospace', fontSize: 10, color: COLOR.blue, fontWeight: 500 }}>
            {trace.skill}
          </span>
        </>
      ) : (
        <span style={{ fontSize: 11, color: '#aaa' }}>等待中…</span>
      )}
    </div>
  )
}

export function ThinkingChain({ lines, duration }) {
  const [phase, setPhase] = useState('running') // 'running' | 'done'
  const [lineIdx, setLineIdx] = useState(0)
  const [expanded, setExpanded] = useState(false)
  const elapsedRef = useRef(0)
  const startRef = useRef(Date.now())

  useEffect(() => {
    const interval = duration / lines.length
    const timers = lines.map((_, i) =>
      setTimeout(() => setLineIdx(i), i * interval)
    )
    const done = setTimeout(() => {
      elapsedRef.current = Math.round((Date.now() - startRef.current) / 1000)
      setPhase('done')
    }, duration)
    return () => { timers.forEach(clearTimeout); clearTimeout(done) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (phase === 'done') {
    return (
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          alignSelf: 'flex-start', maxWidth: '85%',
          fontSize: 11, color: COLOR.blue, cursor: 'pointer',
          background: COLOR.bluePale, border: `0.5px solid ${COLOR.border}`,
          borderRadius: 10, padding: '6px 10px',
          animation: 'slideIn .25s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ fontSize: 12 }}>🧠</span>
          <span style={{ fontWeight: 500 }}>
            已思考（用时 {elapsedRef.current} 秒）
          </span>
          <span style={{ color: COLOR.textHint, fontSize: 10 }}>{expanded ? '▲' : '▼'}</span>
        </div>
        {expanded && (
          <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {lines.map((line, i) => (
              <div key={i} style={{ color: COLOR.textMid, fontSize: 10, lineHeight: 1.5 }}>
                · {line}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{
      alignSelf: 'flex-start', maxWidth: '85%',
      fontSize: 11, color: COLOR.blue,
      background: COLOR.bluePale, border: `0.5px solid ${COLOR.border}`,
      borderRadius: 10, padding: '6px 10px',
      display: 'flex', alignItems: 'center', gap: 6,
      animation: 'slideIn .25s ease',
    }}>
      <span className="thinking-spin" style={{ fontSize: 12 }}>⟳</span>
      <span style={{ color: COLOR.textMid, fontSize: 10 }}>{lines[lineIdx]}</span>
    </div>
  )
}

export function TimelineNode({ type }) {
  const bgMap     = { dp: COLOR.white, dg: COLOR.green, da: COLOR.amber, red: COLOR.red, '': COLOR.panelBg }
  const borderMap = { dp: COLOR.white, dg: COLOR.green, da: COLOR.amber, red: COLOR.red, '': '#7DD3F8' }
  return (
    <div style={{
      width: 13, height: 13, borderRadius: '50%', flexShrink: 0, marginTop: 1,
      background: bgMap[type]     || COLOR.panelBg,
      border:     `2px solid ${borderMap[type] || '#7DD3F8'}`,
      transition: 'all .3s',
    }} />
  )
}

// Hoverable hotel card — defined here (not inside CDemo) to satisfy React hook rules
export function HotelCard({ hotel, onSelect, disabled }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      onClick={disabled ? undefined : onSelect}
      onMouseEnter={() => !disabled && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? COLOR.bluePale : COLOR.white,
        border: `0.5px solid ${hotel.recommended || hovered ? COLOR.panelBg : COLOR.border}`,
        borderRadius: 8, padding: '8px 10px',
        display: 'flex', alignItems: 'center', gap: 9,
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all .2s',
      }}
    >
      <div style={{
        width: 36, height: 36, borderRadius: 6, background: COLOR.blueLight,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18, flexShrink: 0,
      }}>🏨</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 500, color: COLOR.textDark }}>{hotel.name}</div>
        <div style={{ fontSize: 10, color: COLOR.textMid, marginTop: 1 }}>{hotel.meta}</div>
      </div>
      <div style={{ fontSize: 12, fontWeight: 500, color: COLOR.blue, textAlign: 'right', flexShrink: 0 }}>
        {hotel.price}
        {hotel.recommended && <div style={{ fontSize: 9, color: COLOR.blue }}>推荐</div>}
      </div>
    </div>
  )
}
