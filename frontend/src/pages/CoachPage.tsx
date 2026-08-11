import { useState, useEffect, useRef } from 'react';
import { Sparkles, MessageSquare, Plus, Loader2, Info } from 'lucide-react';
import api from '../services/api';

export default function CoachPage() {
    const [threads, setThreads] = useState<any[]>([]);
    const [activeThreadId, setActiveThreadId] = useState<number | null>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [loadingThreads, setLoadingThreads] = useState(false);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [sending, setSending] = useState(false);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchThreads();
    }, []);

    useEffect(() => {
        if (activeThreadId) {
            fetchMessages(activeThreadId);
        } else {
            setMessages([]);
        }
    }, [activeThreadId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchThreads = async () => {
        setLoadingThreads(true);
        try {
            const res = await api.get('/api/copilot/threads/');
            setThreads(res.data);
            if (res.data.length > 0 && !activeThreadId) {
                setActiveThreadId(res.data[0].id);
            }
        } catch (err) {
            console.error('Failed to fetch threads:', err);
        } finally {
            setLoadingThreads(false);
        }
    };

    const fetchMessages = async (threadId: number) => {
        setLoadingMessages(true);
        try {
            const res = await api.get(`/api/copilot/threads/${threadId}/messages/`);
            setMessages(res.data);
        } catch (err) {
            console.error('Failed to fetch messages:', err);
        } finally {
            setLoadingMessages(false);
        }
    };

    const handleNewThread = async () => {
        try {
            const res = await api.post('/api/copilot/threads/', { title: 'New Career Conversation' });
            setThreads([res.data, ...threads]);
            setActiveThreadId(res.data.id);
        } catch (err) {
            console.error('Failed to create thread:', err);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || sending) return;

        let threadId = activeThreadId;
        if (!threadId) {
            try {
                const res = await api.post('/api/copilot/threads/', { title: input.substring(0, 30) + '...' });
                threadId = res.data.id;
                setThreads([res.data, ...threads]);
                setActiveThreadId(threadId);
            } catch (err) {
                console.error('Failed to create thread before sending:', err);
                return;
            }
        }

        const userMsg = {
            id: Date.now(), // temp id
            role: 'USER',
            content: input
        };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setSending(true);

        try {
            await api.post(`/api/copilot/threads/${threadId}/messages/`, { content: userMsg.content });
            // Re-fetch messages or just append. Safer to re-fetch to get exact DB state.
            if (threadId !== null) {
                await fetchMessages(threadId);
            }
        } catch (err) {
            console.error('Failed to send message:', err);
            setMessages(prev => [...prev, {
                id: Date.now(),
                role: 'SYSTEM',
                content: 'Failed to send message. Please try again.'
            }]);
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-6rem)] gap-6">
            {/* Sidebar */}
            <aside className="flex w-64 flex-col gap-4 glass-panel rounded-3xl p-4">
                <button
                    onClick={handleNewThread}
                    className="flex items-center gap-2 rounded-xl bg-accentTeal px-4 py-2 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                >
                    <Plus className="h-4 w-4" /> New Conversation
                </button>
                <div className="flex-1 overflow-y-auto space-y-2">
                    {loadingThreads ? (
                        <div className="flex justify-center p-4"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>
                    ) : (
                        threads.map(thread => (
                            <button
                                key={thread.id}
                                onClick={() => setActiveThreadId(thread.id)}
                                className={`flex w-full items-center gap-2 rounded-xl p-3 text-left text-sm transition ${activeThreadId === thread.id ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-900/50 hover:text-slate-300'}`}
                            >
                                <MessageSquare className="h-4 w-4 shrink-0" />
                                <span className="truncate">{thread.title || 'Conversation'}</span>
                            </button>
                        ))
                    )}
                </div>
            </aside>

            {/* Chat Area */}
            <section className="flex flex-1 flex-col glass-panel rounded-3xl p-6">
                <div className="flex items-center gap-2 mb-6">
                    <Sparkles className="h-5 w-5 text-accentTeal" />
                    <h1 className="text-xl font-semibold text-white">Career Copilot</h1>
                </div>

                <div className="flex-1 overflow-y-auto space-y-6 pr-4 mb-4">
                    {loadingMessages ? (
                        <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-slate-400" /></div>
                    ) : messages.length === 0 ? (
                        <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
                            <Sparkles className="h-12 w-12 mb-4 opacity-50" />
                            <p>Ask me anything about your career, applications, or skills.</p>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <div key={msg.id} className={`flex ${msg.role === 'USER' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'USER' ? 'bg-accentTeal text-darkBg' : 'bg-slate-800 text-slate-200'}`}>
                                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                                    
                                    {/* Display Evidence if available */}
                                    {msg.evidence && msg.evidence.length > 0 && (
                                        <div className="mt-4 space-y-2 border-t border-slate-700/50 pt-3">
                                            <div className="flex items-center gap-1 text-xs font-semibold text-slate-400">
                                                <Info className="h-3 w-3" /> Evidence Context
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {msg.evidence.map((ev: any, idx: number) => (
                                                    <span key={idx} className="rounded bg-slate-900 px-2 py-1 text-xs text-slate-300">
                                                        {ev.label}: {ev.value}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Display Recommendations if available */}
                                    {msg.recommendations && msg.recommendations.length > 0 && (
                                        <div className="mt-4 space-y-2 border-t border-slate-700/50 pt-3">
                                            <div className="text-xs font-semibold text-emerald-400">Recommendations</div>
                                            <ul className="list-disc pl-4 text-sm">
                                                {msg.recommendations.map((rec: string, idx: number) => (
                                                    <li key={idx}>{rec}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {/* Display Warnings if available */}
                                    {msg.warnings && msg.warnings.length > 0 && (
                                        <div className="mt-4 space-y-2 border-t border-slate-700/50 pt-3">
                                            <div className="text-xs font-semibold text-amber-400">Warnings</div>
                                            <ul className="list-disc pl-4 text-sm">
                                                {msg.warnings.map((warn: string, idx: number) => (
                                                    <li key={idx}>{warn}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    {sending && (
                        <div className="flex justify-start">
                            <div className="max-w-[80%] rounded-2xl bg-slate-800 p-4 text-slate-200">
                                <Loader2 className="h-4 w-4 animate-spin" />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="relative mt-auto">
                    <textarea
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask Copilot..."
                        className="w-full resize-none rounded-2xl border border-cardBorder bg-slate-950/80 p-4 pr-24 text-sm text-white outline-none transition focus:border-accentTeal"
                        rows={3}
                        disabled={sending}
                    />
                    <button
                        onClick={handleSend}
                        disabled={sending || !input.trim()}
                        className="absolute bottom-4 right-4 rounded-xl bg-accentTeal px-4 py-2 text-sm font-semibold text-darkBg transition hover:bg-cyan-500 disabled:opacity-50"
                    >
                        Send
                    </button>
                </div>
            </section>
        </div>
    );
}
