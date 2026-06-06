import { useState, useRef, useEffect, useCallback } from 'react'
import { nowTime } from '../utils'
import { ChatBubble, TypingIndicator, SkillTrace, ThinkingChain, COLOR } from '../components/SharedUI'
import {
  DailyReportCard, PromoAdvisorCard, FullHouseSwitchCard,
  ReviewAlertBubble, ReviewReplyCard, MaintenanceSwitchCard,
  MaintenanceCard, RoomRelistCard, CampaignCard,
} from '../components/BCards'
import { useAgentSocket } from '../hooks/useAgentSocket'
import { BDATA } from '../data/bDemoData'

function renderBCard(type, payload, key) {
  switch (type) {
    case 'DailyReportCard':
      return <DailyReportCard key={key} payload={payload} disabled={true} />
    case 'PromoAdvisorCard':
      return <PromoAdvisorCard key={key} payload={payload} />
    case 'FullHouseSwitchCard':
      return <FullHouseSwitchCard key={key} payload={payload} />
    case 'ReviewAlertBubble':
      return <ReviewAlertBubble key={key} payload={payload} />
    case 'ReviewReplyCard':
      return <ReviewReplyCard key={key} payload={payload} disabled={true} />
    case 'MaintenanceSwitchCard':
      return <MaintenanceSwitchCard key={key} payload={payload} />
    case 'MaintenanceCard':
      return <MaintenanceCard key={key} payload={payload} />
    case 'RoomRelistCard':
      return <RoomRelistCard key={key} payload={payload} disabled={true} />
    case 'CampaignCard':
      return <CampaignCard key={key} payload={payload} disabled={true} />
    default:
      return null
  }
}

export default function BDemo({ isActive, onSnapshotUpdate, onTimelineAdd }) {
  const [messages,      setMessages]      = useState([])
  const [isTyping,      setIsTyping]      = useState(false)
  const [trace,         setTrace]         = useState(null)
  const [activeOptions, setActiveOptions] = useState(null)
  const [inputValue,    setInputValue]    = useState('')
  const chatBodyRef = useRef(null)
  const msgIdRef    = useRef(0)

  const soul = 'homestay'
  const { connected, error, on, sendText, selectOption } = useAgentSocket('B', soul)

  const nextId = () => `msg_${++msgIdRef.current}`
  const addMsg = useCallback((msg) => {
    setMessages(prev => [...prev, { ...msg, id: nextId() }])
  }, [])

  const scrollBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (chatBodyRef.current)
        chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    })
  }, [])
  useEffect(() => { scrollBottom() }, [messages, isTyping, activeOptions, scrollBottom])
  useEffect(() => { if (isActive) scrollBottom() }, [isActive, scrollBottom])

  useEffect(() => {
    const unsubs = [
      on('thinking', ({ lines, duration }) => {
        addMsg({ type: 'ThinkingChain', lines, duration: duration || 1500 })
      }),
      on('skill_trace', ({ skill, action, status }) => {
        setTrace({ skill, action, status })
        if (status === 'done') setTimeout(() => setTrace(null), 2000)
      }),
      on('agent_text', ({ text }) => {
        setIsTyping(true)
        setTimeout(() => {
          setIsTyping(false)
          addMsg({ type: 'text', who: 'agent', text, time: nowTime() })
        }, 600)
      }),
      on('skill_card', ({ card, payload }) => {
        addMsg({ type: 'card', card, payload })
      }),
      on('options', ({ items }) => {
        setActiveOptions(items)
      }),
      on('phase_change', ({ to }) => {
        if (to === 'settled' || to === 'idle') setActiveOptions(null)
      }),
      on('snapshot_update', ({ data }) => onSnapshotUpdate?.(data)),
      on('timeline_add', ({ title, desc, dot }) => onTimelineAdd?.(title, desc, dot)),
    ]
    return () => unsubs.forEach(fn => fn?.())
  }, [on, addMsg, onSnapshotUpdate, onTimelineAdd])

  const handleOptionClick = (key, label) => {
    setActiveOptions(null)
    addMsg({ type: 'text', who: 'user', text: label, time: nowTime() })
    selectOption(key)
  }

  const handleSend = () => {
    const text = inputValue.trim()
    if (!text) return
    setInputValue('')
    addMsg({ type: 'text', who: 'user', text, time: nowTime() })
    sendText(text)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <>
      <div style={{
        padding: '4px 12px', fontSize: 10, color: COLOR.blue,
        background: COLOR.bluePale, borderBottom: `0.5px solid ${COLOR.border}`,
        display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          background: connected ? COLOR.green : '#ccc', display: 'inline-block',
        }} />
        {connected
          ? 'Hub Director 已连接 · Qwen3.5-27B · 民宿商家链路'
          : (error || '连接中…')}
      </div>

      {trace && (
        <div className="skill-trace" style={{ flexShrink: 0 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: COLOR.green, flexShrink: 0 }} />
          <span style={{ fontFamily: 'monospace', fontSize: 10, color: COLOR.blue, fontWeight: 500 }}>
            {trace.skill} · {trace.action}
          </span>
        </div>
      )}

      <div ref={chatBodyRef} className="chat-body" style={{
        flex: 1, overflowY: 'auto', padding: '12px 14px',
        display: 'flex', flexDirection: 'column', gap: 8,
      }}>
        {messages.map((msg) => {
          if (msg.type === 'text')
            return <ChatBubble key={msg.id} who={msg.who} text={msg.text} time={msg.time} />
          if (msg.type === 'ThinkingChain')
            return <ThinkingChain key={msg.id} lines={msg.lines} duration={msg.duration} />
          if (msg.type === 'card')
            return renderBCard(msg.card, msg.payload, msg.id)
          return null
        })}
        {isTyping && <TypingIndicator />}
      </div>

      {activeOptions && (
        <div style={{
          display: 'flex', gap: 8, padding: '8px 14px', flexWrap: 'wrap',
          borderTop: `0.5px solid ${COLOR.border}`, flexShrink: 0,
        }}>
          {activeOptions.map(({ key, label }) => (
            <button key={key} onClick={() => handleOptionClick(key, label)} style={{
              padding: '7px 16px', borderRadius: 20,
              border: `0.5px solid ${COLOR.panelBg}`,
              background: COLOR.white, color: COLOR.blue,
              fontSize: 13, cursor: 'pointer', fontWeight: 500,
            }}>
              {label}
            </button>
          ))}
        </div>
      )}

      <div style={{
        display: 'flex', gap: 8, padding: '8px 14px', flexShrink: 0,
        borderTop: `0.5px solid ${COLOR.border}`, background: COLOR.white,
      }}>
        <input
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? '说点什么…（试试"帮我处理差评"或"查看调价建议"）' : '等待连接…'}
          disabled={!connected}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 20,
            border: `0.5px solid ${COLOR.border}`, fontSize: 13,
            outline: 'none', background: COLOR.bluePale,
          }}
        />
        <button onClick={handleSend} disabled={!connected || !inputValue.trim()} style={{
          padding: '8px 16px', borderRadius: 20,
          background: connected ? COLOR.panelBg : '#ccc',
          color: COLOR.white, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 500,
        }}>
          发送
        </button>
      </div>
    </>
  )
}
