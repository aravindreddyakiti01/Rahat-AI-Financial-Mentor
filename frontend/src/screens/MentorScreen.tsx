import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Brain, Sparkles } from 'lucide-react';
import type { ChatMessage, ThinkingState, StructuredAgentResponse } from '../types';
import { sendAgentMessage, sendVoiceTranscript } from '../api';
import { ThinkingOrbWrapper } from '../components/ThinkingOrbWrapper';
import { VoiceBeamWrapper } from '../components/VoiceBeamWrapper';
import { BotAvatarWrapper } from '../components/BotAvatarWrapper';
import { MetalFxWrapper } from '../components/MetalFxWrapper';
import { WhyThisAdviceModal } from '../components/WhyThisAdviceModal';
import { MicrophonePermissionModal } from '../components/MicrophonePermissionModal';

interface Props {
  presetMessage?: string;
  onClearPreset?: () => void;
  onOpenVoiceModal?: () => void;
}

export const MentorScreen: React.FC<Props> = ({
  presetMessage,
  onClearPreset,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg_welcome',
      sender: 'rahat',
      text: "Namaste Ramesh! I'm Rahat, your personal financial mentor. I remember your ₹4,500 bike loan EMI and your recent earning rhythms. How can I help you today?",
      timestamp: 'Just now'
    }
  ]);
  const [input, setInput] = useState('');
  const [thinkingState, setThinkingState] = useState<ThinkingState>('breathing');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [selectedWhyAdvice, setSelectedWhyAdvice] = useState<StructuredAgentResponse | null>(null);

  // Permission & Voice Modal state
  const [isMicModalOpen, setIsMicModalOpen] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [voiceConfirmation, setVoiceConfirmation] = useState<any | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thinkingState]);

  // Handle preset message execution (from Demo walkthrough or suggested pills)
  useEffect(() => {
    if (presetMessage) {
      handleSend(presetMessage);
      if (onClearPreset) onClearPreset();
    }
  }, [presetMessage]);

  const handleSend = async (messageText: string) => {
    if (!messageText.trim() || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `msg_user_${Date.now()}`,
      sender: 'user',
      text: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsProcessing(true);

    // Dynamic ThinkingOrb states representing actual agent workflow
    setThinkingState('searching'); // Retrieving Hindsight & SQLite
    
    setTimeout(() => {
      setThinkingState('solving'); // Financial reasoning with LLM
    }, 600);

    try {
      const response = await sendAgentMessage(messageText);
      
      setThinkingState('composing'); // Assembling grounded response

      setTimeout(() => {
        const rahatMsg: ChatMessage = {
          id: `msg_rahat_${Date.now()}`,
          sender: 'rahat',
          text: response.text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          structuredResponse: response
        };

        setMessages(prev => [...prev, rahatMsg]);
        setIsProcessing(false);
        setThinkingState('breathing');
      }, 400);

    } catch {
      setIsProcessing(false);
      setThinkingState('breathing');
      const errorMsg: ChatMessage = {
        id: `msg_err_${Date.now()}`,
        sender: 'rahat',
        text: "Rahat couldn't reach the agent workflow right now. Your financial records are safe. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  // Voice Interaction handler
  const handleMicClick = () => {
    if (isListening) {
      stopSpeechRecognition();
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsMicModalOpen(true);
      return;
    }

    startSpeechRecognition();
  };

  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicError("Browser speech recognition is not supported in this browser. You can type your request directly.");
      setIsMicModalOpen(true);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-IN';

      recognition.onstart = () => {
        setIsListening(true);
        setThinkingState('listening');
      };

      recognition.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        setThinkingState('solving');
        
        try {
          const res = await sendVoiceTranscript(transcript);
          if (res.needs_confirmation) {
            setVoiceConfirmation(res);
          } else if (res.response) {
            const rahatMsg: ChatMessage = {
              id: `msg_rahat_${Date.now()}`,
              sender: 'rahat',
              text: res.response.text,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              structuredResponse: res.response
            };
            setMessages(prev => [
              ...prev,
              {
                id: `msg_voice_${Date.now()}`,
                sender: 'user',
                text: `🎤 "${transcript}"`,
                timestamp: 'Voice Input'
              },
              rahatMsg
            ]);
          }
        } catch {
          handleSend(transcript);
        }
        setThinkingState('breathing');
      };

      recognition.onerror = (e: any) => {
        setIsListening(false);
        setThinkingState('breathing');
        if (e.error === 'not-allowed') {
          setMicError("Microphone access is blocked. You can enable it from your browser settings or continue typing.");
          setIsMicModalOpen(true);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        setThinkingState('breathing');
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch {
      setIsListening(false);
    }
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
    setThinkingState('breathing');
  };

  const suggestedPrompts = [
    "I need ₹4,500 for my EMI in 5 days. What should I do?",
    "How am I doing this week?",
    "What did I spend on fuel?",
    "Am I on track for my EMI?"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-4.5rem)] max-w-4xl mx-auto px-3 sm:px-4 py-2">
      {/* Header */}
      <div className="flex items-center justify-between py-3 px-4 bg-[#13171f]/80 backdrop-blur-md rounded-2xl border border-slate-800 shrink-0">
        <div className="flex items-center gap-3">
          <BotAvatarWrapper
            size={40}
            state={isProcessing ? 'working' : 'default'}
          />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-slate-100">Rahat</h2>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Outcome-Aware Mentor
              </span>
            </div>
            <p className="text-xs text-slate-400">Personal AI Financial Companion for Gig Workers</p>
          </div>
        </div>

        {/* Dynamic Thinking Orb Indicator */}
        <div className="flex items-center gap-2">
          <ThinkingOrbWrapper
            state={thinkingState}
            size={36}
          />
        </div>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} animate-in fade-in slide-in-from-bottom-2 duration-200`}
          >
            <div className="flex items-start gap-2.5 max-w-[92%] sm:max-w-[82%]">
              {msg.sender === 'rahat' && (
                <BotAvatarWrapper size={32} state="default" className="mt-1" />
              )}

              <div className="space-y-2">
                {/* Bubble */}
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-emerald-600 text-white rounded-tr-xs shadow-md shadow-emerald-950'
                      : 'bg-[#161b24] text-slate-200 border border-slate-800/80 rounded-tl-xs shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>

                {/* Structured Evidence & Memory Badge (When available) */}
                {msg.structuredResponse && (
                  <div className="p-3.5 rounded-xl bg-[#11141b] border border-slate-800 text-xs space-y-2.5">
                    {/* Primary Memory Badge */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 text-sky-400 font-medium">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Using {msg.structuredResponse.memories_used_count} relevant memories</span>
                      </div>
                      <button
                        onClick={() => setSelectedWhyAdvice(msg.structuredResponse!)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 font-medium text-[11px] border border-slate-700 transition-colors flex items-center gap-1"
                      >
                        <Brain className="w-3 h-3" />
                        <span>Why this advice?</span>
                      </button>
                    </div>

                    {/* Recommendation Card */}
                    {msg.structuredResponse.recommendation && (
                      <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-slate-300 whitespace-pre-line leading-relaxed">
                        {msg.structuredResponse.recommendation}
                      </div>
                    )}
                  </div>
                )}

                <span className="text-[10px] text-slate-500 px-1">{msg.timestamp}</span>
              </div>
            </div>
          </div>
        ))}

        {/* Processing State Indicator */}
        {isProcessing && (
          <div className="flex items-center gap-3 p-3 max-w-sm rounded-xl bg-[#161b24] border border-slate-800 text-xs text-slate-300">
            <ThinkingOrbWrapper state={thinkingState} size={28} />
            <div>
              <p className="font-medium text-emerald-400">
                {thinkingState === 'searching' && "Checking SQLite facts & Hindsight memories..."}
                {thinkingState === 'solving' && "Reasoning over previous outcomes..."}
                {thinkingState === 'composing' && "Structuring personalized guidance..."}
              </p>
              <p className="text-[11px] text-slate-400">Synthesizing grounded financial plan</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      <div className="py-2 overflow-x-auto flex items-center gap-2 no-scrollbar">
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            disabled={isProcessing}
            className="shrink-0 px-3 py-1.5 rounded-xl bg-[#13171f] hover:bg-[#1a202c] text-slate-300 hover:text-emerald-400 text-xs font-medium border border-slate-800 hover:border-emerald-500/30 transition-all"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Voice Confirmation Card (If voice log detected) */}
      {voiceConfirmation && (
        <div className="mb-2 p-3 rounded-xl bg-slate-900 border border-amber-500/30 text-xs flex items-center justify-between gap-3 animate-in fade-in">
          <div>
            <p className="font-semibold text-amber-400">{voiceConfirmation.confirmation_message}</p>
            <p className="text-slate-400">Would you like Rahat to record this transaction?</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setVoiceConfirmation(null)}
              className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              onClick={async () => {
                const tx = voiceConfirmation.proposed_transaction;
                setVoiceConfirmation(null);
                handleSend(`I confirmed adding ₹${tx.amount} ${tx.category}.`);
              }}
              className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
            >
              Confirm
            </button>
          </div>
        </div>
      )}

      {/* Composer Input Bar */}
      <VoiceBeamWrapper isListening={isListening} isProcessing={isProcessing} className="mt-1">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(input);
          }}
          className="flex items-center gap-2 p-2 rounded-2xl bg-[#13171f] border border-slate-800 shadow-xl"
        >
          {/* Microphone button */}
          <button
            type="button"
            onClick={handleMicClick}
            aria-label="Voice Input"
            className={`p-2.5 rounded-xl transition-all ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-emerald-400'
            }`}
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? "Listening to your voice..." : "Ask Rahat anything about your money, EMI, or savings..."}
            disabled={isProcessing || isListening}
            className="flex-1 bg-transparent px-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-60"
          />

          {/* MetalFx Send Action */}
          <MetalFxWrapper
            preset="silver"
            variant="button"
            disabled={!input.trim() || isProcessing}
            onClick={() => handleSend(input)}
          >
            <div className="flex items-center gap-1.5">
              <Send className="w-4 h-4 text-emerald-400" />
              <span className="hidden sm:inline text-xs font-semibold text-slate-200">Send</span>
            </div>
          </MetalFxWrapper>
        </form>
      </VoiceBeamWrapper>

      {/* Evidence & Permission Modals */}
      <WhyThisAdviceModal
        isOpen={!!selectedWhyAdvice}
        onClose={() => setSelectedWhyAdvice(null)}
        response={selectedWhyAdvice || undefined}
      />

      <MicrophonePermissionModal
        isOpen={isMicModalOpen}
        onAllow={() => {
          setIsMicModalOpen(false);
          startSpeechRecognition();
        }}
        onDeny={() => setIsMicModalOpen(false)}
        errorMessage={micError}
      />
    </div>
  );
};
