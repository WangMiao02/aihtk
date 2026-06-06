import { useState, useRef, useEffect, useCallback } from 'react'
import { nowTime } from '../utils'
import {
  ChatBubble, TypingIndicator, SkillTrace,
  ThinkingChain, AgentCard, COLOR,
} from '../components/SharedUI'
import { useAgentSocket } from '../hooks/useAgentSocket'

function renderCard(type, payload, key) {
  switch (type) {
    case 'TripBooking':
      return (
        <AgentCard key={key} tag="行程预订" tagColor="blue"
          title={`${payload.trainNo}次 ${payload.date}`}
          subtitle={`${payload.from} → ${payload.to}`}
          rows={[
            { label: '出发', value: payload.departure },
            { label: '到达', value: payload.arrival },
            { label: '座位', value: payload.seatType },
            { label: '票价', value: payload.price, color: COLOR.blue },
          ]} />
      )
    case 'PetBoarding':
      return (
        <AgentCard key={key} tag="宠物寄养" tagColor="green"
          title={`${payload.storeName} · ${payload.boardType}`}
          subtitle={`${payload.petName} · ${payload.days}天`}
          rows={[{ label: '费用', value: payload.price, color: COLOR.blue }]} />
      )
    case 'HotelBooking':
      return (
        <AgentCard key={key} tag="酒店预订" tagColor="blue"
          title={payload.hotelName}
          subtitle={`${payload.checkIn} → ${payload.checkOut} · ${payload.nights}晚`}
          rows={[
            { label: '房型', value: payload.roomType },
            { label: '均价', value: payload.pricePerNight },
            { label: '总计', value: payload.total, color: COLOR.blue },
          ]} />
      )
    case 'RideBooking':
      return (
        <AgentCard key={key} tag="叫车预约" tagColor="amber"
          title="出行叫车"
          rows={[
            { label: '出发时间', value: payload.time || '' },
            { label: '预估费用', value: payload.price },
          ]} />
      )
    case 'LunchRecommend':
      return (
        <AgentCard key={key} tag="午餐推荐"
          title="附近推荐"
          rows={(payload.restaurants || []).map(r => ({
            label: r.name,
            value: `${r.price} · ${r.distance}`,
            color: r.recommended ? COLOR.greenDark : undefined,
          }))} />
      )
    case 'DayBudget':
      return (
        <AgentCard key={key} tag="今日账单" tagColor="blue"
          title={`总计 ${payload.total}`}
          rows={(payload.items || []).map(i => ({
            label: i.label, value: i.amount,
            color: i.type === '差旅' ? COLOR.blue : undefined,
          }))} />
      )
    case 'ExpenseClassify':
      return (
        <AgentCard key={key} tag="报销分类" tagColor="green"
          title={`差旅可报销 ${payload.bizTotal}`}
          rows={(payload.items || []).map(i => ({ label: i.label, value: i.amount }))} />
      )
    default:
      return (
        <AgentCard key={key} tag={type} title="处理完成"
          rows={Object.entries(payload || {}).slice(0, 4).map(([k, v]) => ({
            label: k, value: String(v),
          }))} />
      )
  }
}

export default function CDemo({ isActive, onSnapshotUpdate, onTimelineAdd }) {
  const [messages,      setMessages]      = useState([])
  const [isTyping,      setIsTyping]      = useState(false)
  const [trace,         setTrace]         = useState(null)
  const [activeOptions, setActiveOptions] = useState(null)
  const [inputValue,    setInputValue]    = useState('')
  const chatBodyRef = useRef(null)
  const msgIdRef    = useRef(0)

  const soul = 'pet_owner'
  const { connected, error, on, sendText, selectOption } = useAgentSocket('C', soul)

  const nextId  = () => `msg_${++msgIdRef.current}`
  const addMsg  = useCallback((msg) => {
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
      on('timeline_add',    ({ title, desc, dot }) => onTimelineAdd?.(title, desc, dot)),
      on('rl_recorded',     ({ reward, chain_depth }) => {
        console.log(`[RL] reward=${reward} chain_depth=${chain_depth}`)
      }),
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
          ? 'Agent Harness 已连接 · Qwen3.5-27B · Single→Multi-Agent'
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
            return renderCard(msg.card, msg.payload, msg.id)
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
          placeholder={connected ? '说点什么…（试试"帮我订下周去上海的票"）' : '等待连接…'}
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
