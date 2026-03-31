import { useState } from 'react';
import { 
  Lightbulb, 
  Type, 
  Volume2, 
  Send, 
  Trash2, 
  Zap, 
  ArrowRightLeft,
  Settings,
  MessageSquare,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { api } from '../../lib/api';

const PRESET_MESSAGES = [
  { id: 'ready', label: 'SYSTEM: READY', icon: <Zap className="w-4 h-4" /> },
  { id: 'low_batt', label: 'BATTERY: LOW', icon: <Volume2 className="w-4 h-4" /> },
  { id: 'scanning', label: 'SCANNING AREA...', icon: <ArrowRightLeft className="w-4 h-4" /> },
  { id: 'intruder', label: 'INTRUDER ALERT', icon: <Zap className="w-4 h-4" /> },
  { id: 'patrol', label: 'PATROL ACTIVE', icon: <Settings className="w-4 h-4" /> },
];

const SOUND_LIBRARY = [
  { id: 'siren', label: 'Police Siren', sid: 1 },
  { id: 'horn', label: 'Truck Horn', sid: 2 },
  { id: 'bark', label: 'Dog Bark', sid: 3 },
  { id: 'beep', label: 'System Beep', sid: 4 },
];

export default function Peripherals() {
  // LED State
  const [ledColor, setLedColor] = useState('#ff0000');
  const [brightness, setBrightness] = useState(50);
  
  // OLED State
  const [oledText, setOledText] = useState('');
  const [isScrolling, setIsScrolling] = useState(false);
  
  // Voice State
  const [voiceText, setVoiceText] = useState('');

  // Custom Toast State
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSetLED = async () => {
    try {
      const r = parseInt(ledColor.slice(1, 3), 16);
      const g = parseInt(ledColor.slice(3, 5), 16);
      const b = parseInt(ledColor.slice(5, 7), 16);
      await api.postLightstripControl(r, g, b, 0); 
      showToast('Lightstrip state applied');
    } catch (error) {
      showToast('LED synchronization failed', 'error');
    }
  };

  const handleOLEDAction = async (action: 'write' | 'scroll' | 'clear', text?: string) => {
    try {
      const content = text || oledText;
      if (action === 'scroll') {
        await api.postDisplayControl('scroll', content);
        setIsScrolling(true);
      } else if (action === 'write') {
        await api.postDisplayControl('write', content, 2); 
        setIsScrolling(false);
      } else {
        await api.postDisplayControl('clear');
        setOledText('');
        setIsScrolling(false);
      }
      showToast(`OLED operation: ${action}`);
    } catch (error) {
      showToast('OLED hardware exception', 'error');
    }
  };

  const handleVoicePlay = async () => {
    if (!voiceText) return;
    try {
      await api.postVoiceControl(voiceText);
      showToast('Voice buffer transmitted');
    } catch (error) {
      showToast('STT engine failure', 'error');
    }
  };

  const handleSoundPlay = async (sid: number) => {
    try {
      // Assuming api.js will eventually support sound_id
      // but current Peripherals definition was for voiceText
      showToast(`Triggering sound ID ${sid}`);
    } catch (error) {
      showToast('Sound library error', 'error');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <AnimatePresence>
        {toast && (
          <motion.div 
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed top-8 right-8 z-[100] flex items-center gap-3 px-6 py-4 rounded-3xl bg-[#12121a]/95 border border-white/5 backdrop-blur-2xl shadow-2xl shadow-black/40"
          >
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <span className="text-sm font-medium text-white">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Zap className="w-8 h-8 text-yellow-400" />
          Peripheral Control
        </h1>
        <p className="text-zinc-400">Manage high-fidelity actuators and hardware interfaces.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* LED STRIP CONTROL */}
        <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-transparent pointer-events-none" />
          <div className="relative z-10 space-y-6">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              Chassis Lightstrip
            </h2>

            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <input 
                    id="led-color-picker"
                    type="color" 
                    value={ledColor}
                    onChange={(e) => setLedColor(e.target.value)}
                    aria-label="Lightstrip Color Picker"
                    title="Select Lightstrip Color"
                    className="w-16 h-16 rounded-xl border-none bg-transparent cursor-pointer overflow-hidden transform hover:scale-105 transition-transform"
                  />
                </div>
                <div className="flex-1 space-y-1">
                  <label htmlFor="led-color-picker" className="text-xs font-bold text-zinc-600 uppercase tracking-[2px]">Core Color</label>
                  <p className="font-mono text-white text-lg uppercase">{ledColor}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-xs text-zinc-500 font-bold uppercase tracking-wider">
                  <label htmlFor="intensity-slider">Global Intensity</label>
                  <span>{brightness}%</span>
                </div>
                <input 
                  id="intensity-slider"
                  type="range" 
                  min="0" max="100" 
                  value={brightness}
                  onChange={(e) => setBrightness(parseInt(e.target.value))}
                  aria-label="Lightstrip Intensity Slider"
                  title="Adjust Intensity"
                  className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-yellow-400"
                />
              </div>

              <button 
                onClick={handleSetLED}
                className="w-full py-4 rounded-2xl bg-yellow-400 text-black font-bold hover:bg-yellow-300 transition-colors flex items-center justify-center gap-2"
              >
                Apply Hardware State
              </button>
            </div>
          </div>
        </section>

        {/* OLED DISPLAY CONTROL */}
        <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none" />
          <div className="relative z-10 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Type className="w-5 h-5 text-blue-400" />
                OLED Interface
              </h2>
              {isScrolling && (
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
              )}
            </div>

            <div className="space-y-4">
              <div className="relative group">
                <input 
                  id="oled-input"
                  type="text"
                  placeholder="Enter message..."
                  value={oledText}
                  onChange={(e) => setOledText(e.target.value)}
                  aria-label="OLED Message Input"
                  title="Enter message for OLED"
                  className="w-full bg-zinc-950 border border-white/5 rounded-2xl p-4 text-white placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={() => handleOLEDAction('write')}
                  className="py-3 rounded-xl bg-zinc-800/50 text-white font-medium hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2 border border-white/5"
                >
                  <Send className="w-4 h-4 text-blue-400" /> Static
                </button>
                <button 
                  onClick={() => handleOLEDAction('scroll')}
                  className="py-3 rounded-xl bg-zinc-800/50 text-white font-medium hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2 border border-white/5"
                >
                  <ArrowRightLeft className="w-4 h-4 text-blue-400" /> Scroll
                </button>
              </div>

              <div className="space-y-3 pt-2">
                <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Quick Diagnostics</label>
                <div className="flex flex-wrap gap-2">
                  {PRESET_MESSAGES.map((msg) => (
                    <button 
                      key={msg.id}
                      onClick={() => handleOLEDAction('scroll', msg.label)}
                      className="px-3 py-2 rounded-xl bg-zinc-950 border border-white/5 text-[11px] text-zinc-400 hover:text-white hover:border-blue-500/50 transition-all flex items-center gap-1.5"
                    >
                      {msg.icon}
                      {msg.label}
                    </button>
                  ))}
                </div>
              </div>

              <button 
                onClick={() => handleOLEDAction('clear')}
                className="w-full py-2 rounded-xl text-zinc-500 hover:text-red-400 transition-colors text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" /> Reset Hardware Buffer
              </button>
            </div>
          </div>
        </section>

        {/* VOICE & AUDIO CONTROL */}
        <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none" />
          <div className="relative z-10 space-y-6">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-purple-400" />
              TTS & Sound Board
            </h2>

            <div className="space-y-4">
              <div className="relative group">
                <textarea 
                  id="voice-transmit"
                  rows={3}
                  placeholder="Type to transmit..."
                  value={voiceText}
                  onChange={(e) => setVoiceText(e.target.value)}
                  aria-label="Voice Transmission Input"
                  title="Type text to speak"
                  className="w-full bg-zinc-950 border border-white/5 rounded-2xl p-4 text-white placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all resize-none"
                />
              </div>

              <button 
                onClick={handleVoicePlay}
                className="w-full py-4 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 font-bold hover:bg-purple-500/20 transition-all flex items-center justify-center gap-2 group-hover:scale-[1.02]"
              >
                Transmit Audio Buffer
              </button>

              <div className="space-y-3 pt-2">
                <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Hardware Sounds</label>
                <div className="grid grid-cols-2 gap-2">
                  {SOUND_LIBRARY.map((sound) => (
                    <button 
                      key={sound.id}
                      onClick={() => handleSoundPlay(sound.sid)}
                      className="px-4 py-3 rounded-2xl bg-zinc-950 border border-white/5 text-[11px] text-zinc-400 hover:text-white hover:border-purple-500/50 transition-all flex items-center gap-2"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      {sound.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
