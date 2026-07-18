import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Activity, 
  Calendar, 
  History, 
  MessageSquare, 
  Flame, 
  AlertTriangle, 
  Settings, 
  PlusCircle, 
  CheckCircle, 
  XCircle, 
  Sparkles,
  ChevronRight,
  TrendingUp,
  Heart,
  RefreshCw
} from 'lucide-react';

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? "http://localhost:8000/api"
  : "/api";

// Helper to format date as YYYY-MM-DD
const getTodayString = () => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export default function App() {
  // Navigation & General state
  const [activeTab, setActiveTab] = useState('dashboard');
  const [habit, setHabit] = useState(null);
  const [logs, setLogs] = useState([]);
  const [nudge, setNudge] = useState('');
  const [analysis, setAnalysis] = useState('');
  const [loadingHabit, setLoadingHabit] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Onboarding Form State
  const [newHabitName, setNewHabitName] = useState('');
  const [newHabitDesc, setNewHabitDesc] = useState('');
  const [newHabitTriggers, setNewHabitTriggers] = useState('');
  const [newHabitMotiv, setNewHabitMotiv] = useState('');
  const [newHabitTarget, setNewHabitTarget] = useState('');
  const [submittingHabit, setSubmittingHabit] = useState(false);

  // Daily Log Form State
  const [logDate, setLogDate] = useState(getTodayString());
  const [logMetric, setLogMetric] = useState(0);
  const [logCraving, setLogCraving] = useState(5);
  const [logSlipUp, setLogSlipUp] = useState(false);
  const [logNotes, setLogNotes] = useState('');
  const [submittingLog, setSubmittingLog] = useState(false);

  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const chatBottomRef = useRef(null);

  // Load Initial Data
  useEffect(() => {
    fetchHabitData();
  }, []);

  // Fetch Habit, Logs, and Nudge
  const fetchHabitData = async () => {
    setLoadingHabit(true);
    setErrorMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/habit`);
      if (response.status === 200) {
        const data = await response.json();
        setHabit(data);
        // Fetch logs and nudge since habit exists
        await fetchLogs(data.id);
        fetchNudge();
      } else if (response.status === 404) {
        // No habit found, needs onboarding
        setHabit(null);
      } else {
        setErrorMessage("Server returned an error status while retrieving habit profile.");
      }
    } catch (err) {
      console.error(err);
      setErrorMessage("Could not connect to the backend server. Please verify the FastAPI server is running on http://localhost:8000");
    } finally {
      setLoadingHabit(false);
    }
  };

  const fetchLogs = async (habitId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  };

  const fetchNudge = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/nudge`);
      if (res.ok) {
        const data = await res.json();
        setNudge(data.nudge);
      }
    } catch (err) {
      console.error("Error fetching nudge:", err);
    }
  };

  const fetchAnalysis = async () => {
    setAnalysis('');
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/analysis`);
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data.analysis);
      } else {
        const errData = await res.json();
        setErrorMessage(errData.detail || "Failed to generate analysis.");
      }
    } catch (err) {
      setErrorMessage("Network error generating weekly assessment.");
    }
  };

  const fetchChatHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/history`);
      if (res.ok) {
        const data = await res.json();
        setChatMessages(data);
      }
    } catch (err) {
      console.error("Error fetching chat history:", err);
    }
  };

  // Scroll Chat to Bottom
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, activeTab]);

  // Load chat history when switching to chat tab
  useEffect(() => {
    if (activeTab === 'chat' && habit) {
      fetchChatHistory();
    } else if (activeTab === 'analysis' && habit) {
      fetchAnalysis();
    }
  }, [activeTab, habit]);

  // Action Handlers
  const handleOnboardHabit = async (e) => {
    e.preventDefault();
    if (!newHabitName.trim()) return;
    setSubmittingHabit(true);
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/habit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newHabitName,
          description: newHabitDesc,
          triggers: newHabitTriggers,
          motivation: newHabitMotiv,
          target_reduction: newHabitTarget
        })
      });
      if (res.ok) {
        const data = await res.json();
        setHabit(data);
        setActiveTab('dashboard');
        // Clean onboarding states
        setNewHabitName('');
        setNewHabitDesc('');
        setNewHabitTriggers('');
        setNewHabitMotiv('');
        setNewHabitTarget('');
        fetchNudge();
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Failed to save habit onboarding parameters.");
      }
    } catch (err) {
      setErrorMessage("Failed to send onboarding parameters to backend.");
    } finally {
      setSubmittingHabit(false);
    }
  };

  const handlePostLog = async (e) => {
    e.preventDefault();
    setSubmittingLog(true);
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: logDate,
          metric_value: Number(logMetric),
          craving_level: Number(logCraving),
          slip_up: logSlipUp,
          notes: logNotes
        })
      });
      if (res.ok) {
        await fetchLogs(habit.id);
        fetchNudge();
        // Reset log inputs except date
        setLogMetric(0);
        setLogCraving(5);
        setLogSlipUp(false);
        setLogNotes('');
        setActiveTab('dashboard');
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Validation or database write failed.");
      }
    } catch (err) {
      setErrorMessage("Network error submitting daily log check-in.");
    } finally {
      setSubmittingLog(false);
    }
  };

  const handleSendChat = async (messageText, isSos = false) => {
    if (!messageText.trim()) return;
    setSendingChat(true);
    setErrorMessage('');

    // Optimistically add user message to chat UI
    const optimisticUserMsg = {
      id: Date.now(),
      sender: 'user',
      message: messageText,
      timestamp: new Date().toISOString()
    };
    setChatMessages(prev => [...prev, optimisticUserMsg]);
    setChatInput('');

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          is_sos: isSos
        })
      });
      if (res.ok) {
        const botResponse = await res.json();
        setChatMessages(prev => [...prev, botResponse]);
      } else {
        const errData = await res.json();
        setErrorMessage(errData.detail || "Error receiving response from Aura.");
      }
    } catch (err) {
      setErrorMessage("Network error: Could not reach Aura AI Coach.");
    } finally {
      setSendingChat(false);
    }
  };

  const triggerSOS = () => {
    setActiveTab('chat');
    handleSendChat("EMERGENCY: I am experiencing an intense, overwhelming urge right now. Help me get through it.", true);
  };

  const handleResetData = async () => {
    if (!confirm("Are you sure you want to delete all streaks, logs, chat history, and habit settings? This starts the application fresh.")) {
      return;
    }
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/reset`, { method: 'POST' });
      if (res.ok) {
        setHabit(null);
        setLogs([]);
        setNudge('');
        setAnalysis('');
        setChatMessages([]);
        setActiveTab('dashboard');
      } else {
        setErrorMessage("Server failed to reset database tables.");
      }
    } catch (err) {
      setErrorMessage("Network error attempting application reset.");
    }
  };

  // Streak calculations
  const calculateStreak = () => {
    if (logs.length === 0) return 0;
    // Sort logs descending by date
    const sorted = [...logs].sort((a, b) => new Date(b.date) - new Date(a.date));
    
    let streak = 0;
    for (let log of sorted) {
      if (!log.slip_up) {
        streak++;
      } else {
        break;
      }
    }
    return streak;
  };

  // Render text helper for simple bold/markdown in chat bubbles
  const renderMarkdown = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, index) => {
      let content = line;
      if (content.startsWith('### ')) {
        return <h3 key={index} className="mt-3 mb-2 font-bold text-gray-100">{content.replace('### ', '')}</h3>;
      }
      if (content.startsWith('## ')) {
        return <h2 key={index} className="mt-4 mb-2 font-bold text-gray-100">{content.replace('## ', '')}</h2>;
      }
      if (content.startsWith('1. ') || content.startsWith('- ') || content.startsWith('* ')) {
        const cleanLine = content.replace(/^(1\.\s|-\s|\*\s)/, '');
        return <li key={index} className="ml-5 mb-1 list-disc text-gray-200">{parseInlineStyles(cleanLine)}</li>;
      }
      return <p key={index} className="mb-2 text-gray-200">{parseInlineStyles(content)}</p>;
    });
  };

  const parseInlineStyles = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-extrabold text-white">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  // Onboarding UI Guard
  if (loadingHabit) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a0b10', gap: '16px' }}>
        <RefreshCw className="animate-spin text-purple-500" size={32} />
        <span style={{ fontSize: '18px', fontWeight: '500', color: '#9ca3af' }}>Connecting to Aura Core...</span>
      </div>
    );
  }

  return (
    <div className="app-container">
      
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Brain size={20} color="white" />
          </div>
          <span className="logo-text">AURA AI</span>
        </div>

        <nav className="nav-links">
          {habit ? (
            <>
              <button 
                onClick={() => setActiveTab('dashboard')} 
                className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              >
                <Activity size={18} />
                Dashboard
              </button>

              <button 
                onClick={() => setActiveTab('log')} 
                className={`nav-item ${activeTab === 'log' ? 'active' : ''}`}
              >
                <PlusCircle size={18} />
                Daily Check-in
              </button>

              <button 
                onClick={() => setActiveTab('history')} 
                className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
              >
                <History size={18} />
                History & Logs
              </button>

              <button 
                onClick={() => setActiveTab('chat')} 
                className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
              >
                <MessageSquare size={18} />
                Aura Coach
              </button>

              <button 
                onClick={() => setActiveTab('analysis')} 
                className={`nav-item ${activeTab === 'analysis' ? 'active' : ''}`}
              >
                <TrendingUp size={18} />
                AI Analysis
              </button>
            </>
          ) : (
            <button className="nav-item active">
              <Sparkles size={18} />
              Setup Habit
            </button>
          )}

          <button 
            onClick={() => setActiveTab('settings')} 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            style={{ marginTop: 'auto' }}
          >
            <Settings size={18} />
            Settings & Reset
          </button>
        </nav>

        {habit && (
          <div className="sidebar-footer">
            <button onClick={triggerSOS} className="sos-trigger">
              <AlertTriangle size={16} />
              SOS: URGENT URGE
            </button>
          </div>
        )}
      </aside>

      {/* Main Panel */}
      <main className="main-content">
        
        {/* Error Notification Banners */}
        {errorMessage && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '16px 20px',
            marginBottom: '28px',
            color: '#f87171',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }} className="animate-fade">
            <AlertTriangle size={20} />
            <div style={{ flexGrow: 1 }}>{errorMessage}</div>
            <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontWeight: 'bold' }}>✕</button>
          </div>
        )}

        {/* ONBOARDING FLOW */}
        {!habit ? (
          <div className="onboarding-card animate-fade">
            <div style={{ textAlign: 'center', marginBottom: '28px' }}>
              <div style={{
                display: 'inline-flex',
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: 'rgba(139, 92, 246, 0.1)',
                border: '1px solid rgba(139, 92, 246, 0.2)',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <Sparkles size={30} color="#8b5cf6" />
              </div>
              <h1 style={{ fontSize: '26px' }}>Begin Your Journey</h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
                Let's configure Aura to target the habit you wish to alter.
              </p>
            </div>

            <form onSubmit={handleOnboardHabit}>
              <div className="form-group">
                <label className="form-label">WHAT HABIT DO YOU WANT TO OVERCOME?</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Doomscrolling Twitter, Late night snacking, Nail biting..." 
                  value={newHabitName}
                  onChange={e => setNewHabitName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">BRIEF DESCRIPTION</label>
                <textarea 
                  className="form-input" 
                  rows={2}
                  placeholder="Briefly state when or how this habit manifests."
                  value={newHabitDesc}
                  onChange={e => setNewHabitDesc(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">CORE TRIGGERS (WHAT SPARKS THE URGE?)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Boredom, stress, bedtime, notifications, fatigue..." 
                  value={newHabitTriggers}
                  onChange={e => setNewHabitTriggers(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">YOUR MOTIVATION (WHY STRIVE TO BREAK IT?)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Improve deep sleep, regain productivity, lung health..." 
                  value={newHabitMotiv}
                  onChange={e => setNewHabitMotiv(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">REDUCTION TARGET / OBJECTIVE</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Max 30 mins/day, zero cigarettes, no snacking after 9PM..." 
                  value={newHabitTarget}
                  onChange={e => setNewHabitTarget(e.target.value)}
                />
              </div>

              <button 
                type="submit" 
                className="btn btn-primary" 
                style={{ width: '100%', padding: '14px', marginTop: '12px' }}
                disabled={submittingHabit}
              >
                {submittingHabit ? <RefreshCw className="animate-spin" size={16} /> : "Initialize Aura Coach"}
              </button>
            </form>
          </div>
        ) : (
          /* TAB VIEWS */
          <>
            
            {/* VIEW 1: DASHBOARD */}
            {activeTab === 'dashboard' && (
              <div className="animate-fade">
                <header style={{ marginBottom: '32px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--primary)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px' }}>BEHAVIOR DASHBOARD</span>
                  <h1>My Recovery Path</h1>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Target: <strong>{habit.name}</strong> — {habit.target_reduction}</p>
                </header>

                {/* Daily Nudge widget */}
                <div className="nudge-widget" style={{ marginBottom: '32px' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: 'rgba(139, 92, 246, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <Sparkles size={18} color="#8b5cf6" />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '14px', fontWeight: '700', letterSpacing: '0.2px' }}>Aura's Daily Nudge</h3>
                    <p style={{ fontSize: '13.5px', color: '#d1d5db', marginTop: '2px', lineStyle: 'normal' }}>
                      {nudge || "Analyzing logs to prepare your daily nudge..."}
                    </p>
                  </div>
                </div>

                {/* Grid stats */}
                <div className="dashboard-grid">
                  <div className="glass-card stat-card">
                    <div className="stat-icon" style={{ background: 'var(--success-glow)', color: 'var(--success)' }}>
                      <Flame size={24} />
                    </div>
                    <div>
                      <div className="stat-val">{calculateStreak()} Days</div>
                      <div className="stat-label">Urge-Free Streak</div>
                    </div>
                  </div>

                  <div className="glass-card stat-card">
                    <div className="stat-icon" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                      <TrendingUp size={24} />
                    </div>
                    <div>
                      <div className="stat-val">
                        {logs.length > 0 
                          ? (logs.reduce((acc, curr) => acc + curr.craving_level, 0) / logs.length).toFixed(1)
                          : "0.0"
                        }/10
                      </div>
                      <div className="stat-label">Avg Urge Intensity</div>
                    </div>
                  </div>

                  <div className="glass-card stat-card">
                    <div className="stat-icon" style={{ background: 'var(--danger-glow)', color: 'var(--danger)' }}>
                      <XCircle size={24} />
                    </div>
                    <div>
                      <div className="stat-val">
                        {logs.filter(l => l.slip_up).length} Days
                      </div>
                      <div className="stat-label">Recorded Slip-ups</div>
                    </div>
                  </div>

                  {/* Left Column: Recent logs */}
                  <div className="glass-card col-span-2">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                      <h2>Recent Tracking History</h2>
                      <button onClick={() => setActiveTab('log')} className="btn btn-secondary" style={{ padding: '8px 12px', fontSize: '12px' }}>
                        + Add Entry
                      </button>
                    </div>

                    {logs.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-secondary)' }}>
                        <Calendar size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                        <p style={{ fontSize: '14px' }}>No days tracked yet. Create your first check-in log.</p>
                      </div>
                    ) : (
                      <div className="logs-list">
                        {[...logs].reverse().slice(0, 5).map(log => (
                          <div key={log.id} className="log-item">
                            <div>
                              <div style={{ fontWeight: '700', fontSize: '14px' }}>{log.date}</div>
                              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                Value logged: {log.metric_value} | Craving: {log.craving_level}/10
                              </div>
                              {log.notes && (
                                <div style={{ fontStyle: 'italic', fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                  "{log.notes}"
                                </div>
                              )}
                            </div>
                            <div>
                              {log.slip_up ? (
                                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--danger)', fontWeight: '600' }}>
                                  <XCircle size={14} /> Slip-up
                                </span>
                              ) : (
                                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--success)', fontWeight: '600' }}>
                                  <CheckCircle size={14} /> Success
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Right Column: Mini coach helper */}
                  <div className="glass-card">
                    <h2>Urge Grounding</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.5', marginBottom: '20px' }}>
                      Cravings usually peak within 10 to 15 minutes. Aura uses CBT urge-surfing protocols to talk you down in high-stress moments.
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <button onClick={triggerSOS} className="btn btn-danger" style={{ width: '100%' }}>
                        <AlertTriangle size={16} />
                        Trigger SOS Guide
                      </button>
                      <button onClick={() => setActiveTab('chat')} className="btn btn-secondary" style={{ width: '100%' }}>
                        <MessageSquare size={16} />
                        Talk to Coach
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* VIEW 2: LOG DAY ENTRY */}
            {activeTab === 'log' && (
              <div className="animate-fade" style={{ maxWidth: '600px', margin: '0 auto' }}>
                <header style={{ marginBottom: '28px' }}>
                  <h2>Daily Tracker Check-in</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                    Tracking daily cravings builds cognitive awareness of behavioral triggers. Be honest with your answers.
                  </p>
                </header>

                <form onSubmit={handlePostLog} className="glass-card">
                  <div className="form-group">
                    <label className="form-label">LOGGING DATE</label>
                    <input 
                      type="date" 
                      className="form-input" 
                      value={logDate}
                      onChange={e => setLogDate(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">METRIC MEASUREMENT (e.g. Minutes of Screen Time, Number of Cigarettes)</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      min="0"
                      step="any"
                      placeholder="0"
                      value={logMetric}
                      onChange={e => setLogMetric(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">CRAVING INTENSITY (1 = MINIMAL, 10 = SEVERE)</label>
                    <div className="slider-container">
                      <input 
                        type="range" 
                        min="1" 
                        max="10" 
                        className="slider-input" 
                        value={logCraving}
                        onChange={e => setLogCraving(e.target.value)}
                      />
                      <span className="slider-value">{logCraving}</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <div className="switch-container" onClick={() => setLogSlipUp(!logSlipUp)}>
                      <input 
                        type="checkbox" 
                        className="switch-input" 
                        checked={logSlipUp}
                        onChange={() => {}} // Controlled by parent div click
                      />
                      <div>
                        <div style={{ fontWeight: '700', fontSize: '13.5px', color: logSlipUp ? 'var(--danger)' : 'var(--text-primary)' }}>
                          I experienced a Slip-up today
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                          Toggle this if you engaged in the habit you're trying to break.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">REFLECTIONS & TRIGGERS OBSERVED</label>
                    <textarea 
                      className="form-input" 
                      rows={3}
                      placeholder="e.g. Bored at 4pm after meetings. Felt a sudden trigger. Managed to breathe through it."
                      value={logNotes}
                      onChange={e => setLogNotes(e.target.value)}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                    <button type="button" onClick={() => setActiveTab('dashboard')} className="btn btn-secondary" style={{ flexGrow: 1 }}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" style={{ flexGrow: 2 }} disabled={submittingLog}>
                      {submittingLog ? <RefreshCw className="animate-spin" size={16} /> : "Save Daily Log"}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* VIEW 3: FULL HISTORY LOGS */}
            {activeTab === 'history' && (
              <div className="animate-fade">
                <header style={{ marginBottom: '28px' }}>
                  <h2>Historical Progress Logs</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                    Your raw history entries. Analyze trends and review trigger logs.
                  </p>
                </header>

                <div className="glass-card">
                  {logs.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
                      <Calendar size={36} style={{ marginBottom: '12px', opacity: 0.5 }} />
                      <p>No logged entries found in database.</p>
                    </div>
                  ) : (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                            <th style={{ padding: '12px 16px' }}>Date</th>
                            <th style={{ padding: '12px 16px' }}>Metric</th>
                            <th style={{ padding: '12px 16px' }}>Craving</th>
                            <th style={{ padding: '12px 16px' }}>Status</th>
                            <th style={{ padding: '12px 16px' }}>Trigger Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {logs.map(log => (
                            <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                              <td style={{ padding: '14px 16px', fontWeight: '600' }}>{log.date}</td>
                              <td style={{ padding: '14px 16px' }}>{log.metric_value}</td>
                              <td style={{ padding: '14px 16px' }}>
                                <span style={{
                                  display: 'inline-block',
                                  padding: '2px 8px',
                                  borderRadius: '12px',
                                  fontSize: '11px',
                                  background: log.craving_level >= 7 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.05)',
                                  color: log.craving_level >= 7 ? 'var(--danger)' : 'var(--text-primary)'
                                }}>
                                  Intensity {log.craving_level}/10
                                </span>
                              </td>
                              <td style={{ padding: '14px 16px' }}>
                                {log.slip_up ? (
                                  <span style={{ color: 'var(--danger)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <XCircle size={14} /> Slip-up
                                  </span>
                                ) : (
                                  <span style={{ color: 'var(--success)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <CheckCircle size={14} /> Success
                                  </span>
                                )}
                              </td>
                              <td style={{ padding: '14px 16px', color: 'var(--text-secondary)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={log.notes}>
                                {log.notes || "-"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* VIEW 4: CHAT COACH */}
            {activeTab === 'chat' && (
              <div className="animate-fade chat-container">
                <header style={{
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'between',
                  borderBottom: '1px solid var(--border-color)',
                  paddingBottom: '16px',
                  marginBottom: '8px'
                }}>
                  <div style={{ flexGrow: 1 }}>
                    <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 0 }}>
                      <Brain size={22} color="var(--primary)" />
                      Coaching Sessions
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
                      Aura uses cognitive principles to break urges. Type regular check-ins or request urgings help.
                    </p>
                  </div>
                  <button onClick={triggerSOS} className="btn btn-danger" style={{ padding: '8px 16px', fontSize: '12px' }}>
                    Trigger Urgent SOS
                  </button>
                </header>

                <div className="chat-messages">
                  {chatMessages.length === 0 ? (
                    <div style={{
                      textAlign: 'center',
                      padding: '48px 24px',
                      color: 'var(--text-secondary)',
                      margin: 'auto 0'
                    }}>
                      <div style={{
                        display: 'inline-flex',
                        width: '56px',
                        height: '56px',
                        borderRadius: '50%',
                        background: 'rgba(139, 92, 246, 0.1)',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: '16px'
                      }}>
                        <Brain size={28} color="#8b5cf6" />
                      </div>
                      <h3>Start Chatting with Aura</h3>
                      <p style={{ fontSize: '13px', maxWidth: '340px', margin: '6px auto 0', lineHeight: '1.4' }}>
                        Share how you are feeling, talk about a slip-up, or explore trigger settings. Aura is here to help.
                      </p>
                    </div>
                  ) : (
                    chatMessages.map(msg => (
                      <div 
                        key={msg.id} 
                        className={`message-bubble ${msg.sender === 'coach' ? 'message-coach' : 'message-user'} ${
                          msg.message.includes("EMERGENCY") || msg.message.includes("Urgent") ? 'sos' : ''
                        }`}
                      >
                        {msg.sender === 'coach' ? (
                          <div className="markdown-content">
                            {renderMarkdown(msg.message)}
                          </div>
                        ) : (
                          <div>{msg.message}</div>
                        )}
                        <div style={{
                          fontSize: '10px',
                          color: msg.sender === 'coach' ? 'var(--text-muted)' : 'rgba(255,255,255,0.7)',
                          textAlign: 'right',
                          marginTop: '6px'
                        }}>
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    ))
                  )}
                  {sendingChat && (
                    <div className="message-bubble message-coach animate-pulse" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <RefreshCw className="animate-spin text-purple-400" size={14} />
                      <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Aura is drafting advice...</span>
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                <div className="chat-input-area">
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Reflect on your trigger, talk about cravings, or express stress..."
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') handleSendChat(chatInput);
                    }}
                    disabled={sendingChat}
                  />
                  <button 
                    onClick={() => handleSendChat(chatInput)}
                    className="btn btn-primary"
                    disabled={sendingChat || !chatInput.trim()}
                  >
                    Send
                  </button>
                </div>
              </div>
            )}

            {/* VIEW 5: WEEKLY COGNITIVE ANALYSIS */}
            {activeTab === 'analysis' && (
              <div className="animate-fade" style={{ maxWidth: '800px', margin: '0 auto' }}>
                <header style={{ marginBottom: '28px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--primary)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px' }}>AI STATISTICAL REPORT</span>
                  <h2>Aura's weekly Behavioral Analysis</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                    Cognitive analyses run on demand. Aura processes trigger notes, craving levels, and slip-up patterns.
                  </p>
                </header>

                <div className="glass-card markdown-content" style={{ minHeight: '260px', padding: '32px' }}>
                  {!analysis ? (
                    <div style={{ display: 'flex', height: '180px', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
                      <RefreshCw className="animate-spin text-purple-500" size={28} />
                      <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Drafting behavioral assessment from your logs...</span>
                    </div>
                  ) : (
                    renderMarkdown(analysis)
                  )}
                </div>
              </div>
            )}

          </>
        )}

        {/* VIEW 6: SETTINGS & RESET */}
        {activeTab === 'settings' && (
          <div className="animate-fade" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <header style={{ marginBottom: '28px' }}>
              <h2>Application Settings & Evaluation Panel</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
                Configure local preferences or wipe simulated test databases to perform a complete end-to-end evaluation check.
              </p>
            </header>

            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <h3 style={{ fontSize: '16px', color: 'var(--text-primary)', marginBottom: '8px' }}>System Diagnosis</h3>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  <p>Backend Connection: <strong style={{ color: 'var(--success)' }}>Online (http://localhost:8000)</strong></p>
                  <p>Database: <strong>SQLite (local aura.db file)</strong></p>
                  <p>Habits Registered: <strong>{habit ? `1 (${habit.name})` : "None (Pending setup)"}</strong></p>
                  <p>Logs Count: <strong>{logs.length} entries</strong></p>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
                <h3 style={{ fontSize: '16px', color: 'var(--danger)', marginBottom: '8px' }}>Reset Simulation Data</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.5' }}>
                  Performing a reset deletes all rows from SQLite tables (`habits`, `logs`, `chat_messages`). 
                  Use this to test the initial habit profile onboarding form flow.
                </p>
                <button onClick={handleResetData} className="btn btn-danger" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  Delete All Local Data
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
