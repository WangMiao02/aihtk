import { useState, useCallback } from 'react'
import './App.css'
import { RightPanel } from './components/RightPanel'
import BDemo from './demos/BDemo'
import CDemo from './demos/CDemo'
import { BDATA, INITIAL_B_SNAPSHOT, INITIAL_B_TIMELINE } from './data/bDemoData'
import { INITIAL_C_SNAPSHOT, INITIAL_C_TIMELINE } from './data/cDemoData'
import { nowTime } from './utils'

export default function App() {
  const [activeTab, setActiveTab] = useState('B')

  // Keys — increment only on explicit "重新开始", not on tab switch
  const [bResetKey, setBResetKey] = useState(0)
  const [cResetKey, setCResetKey] = useState(0)

  // Snapshot and timeline state — persists across tab switches
  const [bSnapshot, setBSnapshot] = useState({ ...INITIAL_B_SNAPSHOT })
  const [cSnapshot, setCSnapshot] = useState({ ...INITIAL_C_SNAPSHOT })
  const [bTimeline, setBTimeline] = useState([...INITIAL_B_TIMELINE])
  const [cTimeline, setCTimeline] = useState([...INITIAL_C_TIMELINE])

  // Tab switch — preserve progress, just toggle visibility
  const handleTabSwitch = tab => setActiveTab(tab)

  // Explicit reset — remounts the active demo and resets its data
  const handleReset = () => {
    if (activeTab === 'B') {
      setBResetKey(k => k + 1)
      setBSnapshot({ ...INITIAL_B_SNAPSHOT })
      setBTimeline([...INITIAL_B_TIMELINE])
    } else {
      setCResetKey(k => k + 1)
      setCSnapshot({ ...INITIAL_C_SNAPSHOT })
      setCTimeline([...INITIAL_C_TIMELINE])
    }
  }

  const handleBSnapshotUpdate = useCallback(update => setBSnapshot(prev => ({ ...prev, ...update })), [])
  const handleCSnapshotUpdate = useCallback(update => setCSnapshot(prev => ({ ...prev, ...update })), [])

  const handleBTimelineAdd = useCallback((title, desc, dot) => {
    setBTimeline(prev => [{ title, desc, dot, time: nowTime() }, ...prev.filter(item => item.title !== '等待启动')])
  }, [])
  const handleCTimelineAdd = useCallback((title, desc, dot) => {
    setCTimeline(prev => [{ title, desc, dot, time: nowTime() }, ...prev.filter(item => item.title !== '等待操作')])
  }, [])

  const agentName  = activeTab === 'B' ? BDATA.agentName : '旅行助手'
  const avatarChar = activeTab === 'B' ? '栖' : 'A'
  const tabSubtitle = activeTab === 'B' ? '栖云·青芝坞小院 — 商家端演示' : '旅行助手 — 用户端演示'

  return (
    <div className="app-root">
      {/* Tab bar */}
      <div className="tab-bar">
        <div className="tab-pill">
          <button className={`tab-btn${activeTab === 'B' ? ' active' : ''}`} onClick={() => handleTabSwitch('B')}>
            B端 · 商家助手
          </button>
          <button className={`tab-btn${activeTab === 'C' ? ' active' : ''}`} onClick={() => handleTabSwitch('C')}>
            C端 · 用户助手
          </button>
        </div>
        <span className="tab-title">{tabSubtitle}</span>
        <button className="reset-btn" onClick={handleReset} title="重新开始当前演示">
          ↺ 重新开始
        </button>
      </div>

      <div className="body-cols">
        {/* Chat column */}
        <main className="col-chat">
          {/* Header — always visible, content reflects active tab */}
          <div className="chat-hd">
            <div className="av">{avatarChar}</div>
            <div>
              <div className="chat-hd-name">{agentName}</div>
              <div className="chat-hd-status">● 在线</div>
            </div>
          </div>

          {/* Both demos always mounted; visibility toggled via display:none in each demo */}
          <BDemo
            key={bResetKey}
            isActive={activeTab === 'B'}
            onSnapshotUpdate={handleBSnapshotUpdate}
            onTimelineAdd={handleBTimelineAdd}
          />
          <CDemo
            key={cResetKey}
            isActive={activeTab === 'C'}
            onSnapshotUpdate={handleCSnapshotUpdate}
            onTimelineAdd={handleCTimelineAdd}
          />
        </main>

        {/* Right panel */}
        <RightPanel
          tab={activeTab}
          snapshot={activeTab === 'B' ? bSnapshot : cSnapshot}
          timeline={activeTab === 'B' ? bTimeline : cTimeline}
        />
      </div>
    </div>
  )
}
