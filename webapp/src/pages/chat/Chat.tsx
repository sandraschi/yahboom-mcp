import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Send, Cpu, User } from 'lucide-react';

const Chat: React.FC = () => {
    const [messages, setMessages] = useState([
        { role: 'ai', content: 'Greetings. G1 Substrate Link sequence complete. I am ready for manual or autonomous directives. What is our objective?' }
    ]);
    const [input, setInput] = useState('');

    return (
        <div className="h-full flex flex-col py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center gap-4 mb-8">
                <MessageSquare className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">AI Companion</h1>
                    <p className="text-slate-400 text-sm">Natural language interface for Yahboom G1 hardware.</p>
                </div>
            </div>

            <div className="flex-1 bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 flex flex-col min-h-0 shadow-2xl backdrop-blur-xl">
                <div className="flex-1 overflow-y-auto space-y-6 mb-8 pr-4 scrollbar-thin">
                    {messages.map((msg, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: msg.role === 'ai' ? -10 : 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse text-right' : ''}`}
                        >
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${msg.role === 'ai' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-700/50 text-slate-300'}`}>
                                {msg.role === 'ai' ? <Cpu size={20} /> : <User size={20} />}
                            </div>
                            <div className={`p-5 rounded-2xl text-sm leading-relaxed max-w-[80%] ${msg.role === 'ai' ? 'bg-white/5 text-slate-200 border border-white/5' : 'bg-indigo-600 text-white'}`}>
                                {msg.content}
                            </div>
                        </motion.div>
                    ))}
                </div>

                <div className="relative group">
                    <input
                        type="text"
                        placeholder="Command robot or ask about system status..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 pr-16 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-all group-focus-within:bg-white/[0.08]"
                    />
                    <button className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-all shadow-lg shadow-indigo-600/20 group-focus-within:scale-105 active:scale-95">
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat;
