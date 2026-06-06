/**
 * useAgentSocket — WebSocket hook
 * 连接后端 FastAPI WebSocket: ws://localhost:8000/ws/{demo}/{soul}
 *
 * 使用方式：
 *   const { connected, send, on } = useAgentSocket('C', 'pet_owner')
 *   on('agent_text', ({ text }) => addMessage(...))
 *   send({ event: 'user_message', text: '帮我订下周去上海的票' })
 */

import { useEffect, useRef, useState, useCallback } from 'react'

const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'

export function useAgentSocket(demo, soul) {
  const wsRef      = useRef(null)
  const handlersRef = useRef({})
  const [connected, setConnected] = useState(false)
  const [error,     setError]     = useState(null)

  /** 注册事件处理器，返回取消注册函数 */
  const on = useCallback((eventName, handler) => {
    handlersRef.current[eventName] = handler
    return () => { delete handlersRef.current[eventName] }
  }, [])

  /** 发送消息到后端 */
  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  /** 选择选项 */
  const selectOption = useCallback((key) => {
    send({ event: 'option_select', key, demo, soul })
  }, [send, demo, soul])

  /** 发送文本消息 */
  const sendText = useCallback((text) => {
    send({ event: 'user_message', text, demo, soul })
  }, [send, demo, soul])

  useEffect(() => {
    const url = `${WS_BASE}/ws/${demo}/${soul}`
    const ws  = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setError(null)
    }

    ws.onclose = () => {
      setConnected(false)
    }

    ws.onerror = () => {
      setError('无法连接到 Agent 后端（localhost:8000）')
      setConnected(false)
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        const handler = handlersRef.current[data.event]
        if (handler) handler(data)
        // 通配符处理器
        const wildcard = handlersRef.current['*']
        if (wildcard) wildcard(data)
      } catch (err) {
        console.warn('[useAgentSocket] parse error', err)
      }
    }

    return () => {
      ws.close()
    }
  }, [demo, soul])

  return { connected, error, send, on, sendText, selectOption }
}
