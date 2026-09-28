import React from 'react';
import type { ThinkingState } from '../types';

interface Props {
  state?: ThinkingState;
  size?: number;
  className?: string;
  speed?: number;
  paused?: boolean;
}

export const ThinkingOrbWrapper: React.FC<Props> = ({
  state = 'breathing',
  size = 64,
  className = '',
  speed = 1,
  paused = false,
}) => {
  // Color mapping based on semantic agent action
  const getStateColor = (s: ThinkingState) => {
    switch (s) {
      case 'searching': return 'from-emerald-400 to-teal-600';
      case 'solving': return 'from-amber-400 to-emerald-600';
      case 'listening': return 'from-sky-400 to-blue-600';
      case 'connecting': return 'from-indigo-400 to-purple-600';
      case 'weaving': return 'from-teal-400 to-emerald-700';
      case 'composing': return 'from-emerald-300 to-cyan-500';
      case 'working': return 'from-emerald-500 to-teal-500';
      case 'breathing': return 'from-emerald-600/60 to-teal-700/60';
      default: return 'from-emerald-500 to-teal-600';
    }
  };

  return (
    <div className={`relative flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <div className="relative w-full h-full flex items-center justify-center">
        <div
          className={`absolute inset-0 rounded-full bg-gradient-to-tr ${getStateColor(state)} opacity-80 blur-md animate-pulse`}
          style={{ animationDuration: `${Math.max(1 / speed, 0.4)}s` }}
        />
        <div
          className={`relative rounded-full bg-gradient-to-tr ${getStateColor(state)} shadow-lg border border-white/20 transition-all duration-300`}
          style={{ width: size * 0.75, height: size * 0.75 }}
        />
        {!paused && (
          <div className="absolute w-2 h-2 rounded-full bg-white/90 shadow-sm animate-ping" />
        )}
      </div>
    </div>
  );
};
