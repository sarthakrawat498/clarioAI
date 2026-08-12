import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../api';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  History, 
  BookOpen, 
  Calculator, 
  Stethoscope, 
  Scale, 
  ExternalLink,
  MessageSquarePlus,
  Trash2,
  Pencil,
  Check
} from 'lucide-react';



const QUICK_PROMPTS = [
  { text: "🧮 Calculate premium for 35yo in Tier 1 city", query: "Can you calculate my annual estimated premium for age 35, Tier 1 city with Family Floater?" },
  { text: "🩺 Check claim eligibility", query: "Am I eligible to claim ₹2,00,000 for a surgery hospital stay after 2 years of policy?" },
  { text: "💡 Recommend best policy for diabetes", query: "Which health policy is best for someone with pre-existing diabetes and 2 family members?" },
  { text: "⚖️ Compare Star Comprehensive vs HDFC Optima", query: "Compare Star Health Comprehensive vs HDFC ERGO Optima Secure side by side." },
  { text: "📜 What is pre-existing disease waiting period?", query: "What is the standard pre-existing disease (PED) waiting period across policies?" },
];


const FormattedMessage = ({ content }) => {
  if (!content) return null;

  const parseBlocks = (text) => {
    let cleanText = text
      .replace(/📖 Policy Excerpt Citations:[\s\S]*$/gi, '')
      .replace(/📖 Policy Citations & Excerpts:[\s\S]*$/gi, '')
      .replace(/📖 Citations:[\s\S]*$/gi, '')
      .replace(/\[\s*(Company|Policy|Page|Source)[^\]]*?\]/gi, '')
      .replace(/\[[^\]]*?(Company|Policy|Page):\s*[^\]]*?\]/gi, '')
      .replace(/\[[^\]]*?Page\s*\d+[^\]]*?\]/gi, '')
      .replace(/(,\s*|\s+)?\(?\s*Page:\s*\d+\s*\)?/gi, '')
      .replace(/(,\s*|\s+)?\(?\s*Page\s+\d+\s*\)?/gi, '')
      .replace(/\(\s*\)/g, '')
      .replace(/\[\s*\]/g, '')
      .replace(/,\s*,/g, ',')
      .replace(/\s{2,}/g, ' ')
      .trim();

    const lines = cleanText.split('\n');

    const blocks = [];
    let tableRows = [];
    let inTable = false;
    let listItems = [];
    let inList = false;

    const renderBold = (str) => {
      const parts = str.split(/(\*\*.*?\*\*|\*.*?\*|__.*?__|`.*?`)/g);
      return parts.map((part, i) => {
        if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
          return <strong key={i} style={{ color: '#f8fafc', fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={i} style={{ color: '#e2e8f0' }}>{part.slice(1, -1)}</em>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return <code key={i} style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8', padding: '2px 6px', borderRadius: '4px', fontSize: '0.82em', fontFamily: 'monospace' }}>{part.slice(1, -1)}</code>;
        }
        return part;
      });
    };

    const flushList = () => {
      if (listItems.length > 0) {
        blocks.push(
          <ul key={`ul-${blocks.length}`} style={{ margin: '8px 0 12px 18px', paddingLeft: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {listItems.map((item, idx) => (
              <li key={idx} style={{ color: '#cbd5e1', fontSize: '0.92rem', lineHeight: '1.5' }}>
                {renderBold(item)}
              </li>
            ))}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    const flushTable = () => {
      if (tableRows.length > 0) {
        const headerRow = tableRows[0];
        const bodyRows = tableRows.slice(1).filter(r => !r.every(cell => cell.trim().startsWith('---') || cell.trim() === ''));

        blocks.push(
          <div key={`table-${blocks.length}`} style={{ overflowX: 'auto', margin: '14px 0', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.12)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left', background: 'rgba(15,23,42,0.6)' }}>
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.9)', borderBottom: '1px solid rgba(255,255,255,0.15)' }}>
                  {headerRow.map((cell, cIdx) => (
                    <th key={cIdx} style={{ padding: '10px 14px', color: '#38bdf8', fontWeight: 700 }}>
                      {renderBold(cell.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bodyRows.map((r, rIdx) => (
                  <tr key={rIdx} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: rIdx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
                    {r.map((cell, cIdx) => (
                      <td key={cIdx} style={{ padding: '9px 14px', color: '#cbd5e1' }}>
                        {renderBold(cell.trim())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
        inTable = false;
      }
    };

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim();
      if (!line) {
        flushList();
        flushTable();
        continue;
      }

      if (line.startsWith('|') && line.endsWith('|')) {
        flushList();
        inTable = true;
        const cells = line.split('|').slice(1, -1);
        tableRows.push(cells);
        continue;
      } else if (inTable) {
        flushTable();
      }

      if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ') || /^\d+\.\s/.test(line)) {
        inList = true;
        const itemContent = line.replace(/^(-|\*|•|\d+\.)\s*/, '');
        listItems.push(itemContent);
        continue;
      } else if (inList) {
        flushList();
      }

      if (line.startsWith('#')) {
        const headerText = line.replace(/^#+\s*/, '');
        const level = line.match(/^#+/)[0].length;

        if (level === 1) {
          blocks.push(<h2 key={`h1-${blocks.length}`} style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', margin: '14px 0 8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '6px' }}>{renderBold(headerText)}</h2>);
        } else if (level === 2) {
          blocks.push(<h3 key={`h2-${blocks.length}`} style={{ fontSize: '1.08rem', fontWeight: 700, color: '#38bdf8', margin: '12px 0 6px 0' }}>{renderBold(headerText)}</h3>);
        } else {
          blocks.push(<h4 key={`h3-${blocks.length}`} style={{ fontSize: '0.96rem', fontWeight: 700, color: '#34d399', margin: '10px 0 4px 0' }}>{renderBold(headerText)}</h4>);
        }
        continue;
      }

      blocks.push(
        <p key={`p-${blocks.length}`} style={{ margin: '6px 0 10px 0', lineHeight: '1.6', color: '#cbd5e1', fontSize: '0.92rem' }}>
          {renderBold(line)}
        </p>
      );
    }

    flushList();
    flushTable();

    return blocks;
  };

  return <div className="formatted-msg-container">{parseBlocks(content)}</div>;
};

export const ChatbotView = ({ onNavigate }) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      agent_name: 'Clario AI Assistant',
      content: 'Hello! I am your AI Health Insurance Advisor. Powered by multi-agent RAG (Coverage Explainer, Sales Recommendation, Actuarial Premium & Claims Evaluator), how can I help you today?',
      sources: [],
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const data = await chatAPI.getSessions();
      setSessions(data || []);
    } catch (e) {
      console.warn('Could not load chat sessions:', e);
    }
  };

  const handleDeleteSession = async (e, idToDelete) => {
    e.stopPropagation();
    try {
      await chatAPI.deleteSession(idToDelete);
      setSessions((prev) => prev.filter((s) => s.id !== idToDelete));
      if (sessionId === idToDelete) {
        startNewChat();
      }
    } catch (err) {
      console.error('Delete session error:', err);
    }
  };

  const handleStartEdit = (e, session) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.session_title);
  };

  const handleSaveEdit = async (e, targetId) => {
    e.stopPropagation();
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      await chatAPI.updateSessionTitle(targetId, editingTitle.trim());
      setSessions((prev) =>
        prev.map((s) => (s.id === targetId ? { ...s, session_title: editingTitle.trim() } : s))
      );
    } catch (err) {
      console.error('Update session title error:', err);
    } finally {
      setEditingSessionId(null);
    }
  };

      console.error('Delete session error:', err);
    }
  };


  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: textToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInputQuery('');
    setLoading(true);

    try {
      const res = await chatAPI.sendQuery(textToSend, sessionId);
      if (res.session_id) setSessionId(res.session_id);

      const assistantMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        agent_name: res.agent_used || 'Multi-Agent Assistant',
        intent: res.intent,
        content: res.message,
        sources: res.sources || [],
        recommended_policies: res.recommended_policies,
        comparison_table: res.comparison_table,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      fetchSessions();
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          agent_name: 'Error',
          content: 'Unable to reach backend server. Please verify FastAPI service is running.',
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadSession = (s) => {
    setSessionId(s.id);
    const converted = s.messages.map((m) => ({
      id: m.id,
      sender: m.sender,
      agent_name: m.agent_name || (m.sender === 'user' ? 'User' : 'Assistant'),
      content: m.content,
      sources: m.sources || [],
    }));
    setMessages(converted);
    setShowHistory(false);
  };

  const startNewChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        agent_name: 'Clario AI Assistant',
        content: 'New session started! What insurance question or calculation would you like to perform?',
        sources: [],
      }
    ]);
    setShowHistory(false);
  };

  const getAgentBadgeClass = (agentName) => {
    if (!agentName) return 'badge-coverage';
    const lower = agentName.toLowerCase();
    if (lower.includes('sales')) return 'badge-sales';
    if (lower.includes('compare')) return 'badge-comparison';
    if (lower.includes('claim')) return 'badge-claims';
    return 'badge-coverage';
  };

  return (
    <div className="chat-container">
      {/* Header Banner */}
      <div className="chat-header-banner">
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={22} style={{ color: 'var(--cyan)' }} /> 
            Multi-Agent AI Advisor
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Ask anything about insurance policies, calculate estimates, check claims, or request smart recommendations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="btn-secondary" 
            onClick={() => setShowHistory(!showHistory)}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <History size={16} /> History ({sessions.length})
          </button>
          <button 
            className="btn-primary" 
            onClick={startNewChat}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <MessageSquarePlus size={16} /> New Chat
          </button>
        </div>
      </div>

      {/* History Slide-over Drawer */}
      {showHistory && (
        <div className="history-drawer">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>Past Chat Sessions</span>
            <button className="btn-secondary" style={{ padding: '2px 8px', fontSize: '0.75rem' }} onClick={() => setShowHistory(false)}>Close</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
            {sessions.length === 0 ? (
              <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>No prior chat sessions found.</span>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => loadSession(s)}
                  className={`history-item ${s.id === sessionId ? 'active' : ''}`}
                >
                  <Bot size={14} style={{ flexShrink: 0, color: 'var(--cyan)' }} />
                  
                  {editingSessionId === s.id ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flex: 1 }} onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        className="form-input"
                        style={{ padding: '2px 6px', fontSize: '0.8rem', height: '26px' }}
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(e, s.id);
                          if (e.key === 'Escape') setEditingSessionId(null);
                        }}
                        autoFocus
                      />
                      <button
                        className="delete-session-btn"
                        style={{ color: '#34d399' }}
                        onClick={(e) => handleSaveEdit(e, s.id)}
                        title="Save title"
                      >
                        <Check size={14} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <span className="history-item-title">{s.session_title}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                        <button
                          className="delete-session-btn"
                          onClick={(e) => handleStartEdit(e, s)}
                          title="Edit query title"
                        >
                          <Pencil size={13} />
                        </button>
                        <button
                          className="delete-session-btn"
                          onClick={(e) => handleDeleteSession(e, s.id)}
                          title="Delete chat session"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))


            )}
          </div>
        </div>
      )}

      {/* Messages Timeline */}
      <div className="chat-messages-scroll">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div key={msg.id} className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
              {!isUser && (
                <div className={`agent-badge ${getAgentBadgeClass(msg.agent_name)}`}>
                  <Sparkles size={12} /> {msg.agent_name || 'AI Assistant'}
                </div>
              )}

              <FormattedMessage content={msg.content} />
            </div>
          );
        })}


        {loading && (
          <div className="chat-bubble assistant" style={{ width: 'fit-content' }}>
            <div className="agent-badge badge-coverage">
              <Sparkles size={12} className="pulse-dot" /> Multi-Agent Workflow Executing...
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Analyzing metadata, ChromaDB RAG vector store & actuarial models...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Prompt Chips ("What do you want to do?") */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} style={{ color: 'var(--cyan)' }} /> Quick AI Prompt Chips ("What do you want to do?"):
        </div>

        <div className="quick-chips-container">
          {QUICK_PROMPTS.map((chip, idx) => (
            <button key={idx} className="chip-btn" onClick={() => handleSend(chip.query)}>
              {chip.text}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '12px', marginTop: '10px' }}
        >
          <input
            type="text"
            className="form-input"
            placeholder="Ask insurance question, claim eligibility, premium estimation..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="btn-primary" disabled={loading || !inputQuery.trim()}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
