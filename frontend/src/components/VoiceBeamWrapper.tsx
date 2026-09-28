import React from 'react';

interface Props {
  isListening?: boolean;
  isProcessing?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const VoiceBeamWrapper: React.FC<Props> = ({
  isListening = false,
  isProcessing = false,
  children,
  className = '',
}) => {
  return (
    <div className={`relative ${className}`}>
      <div className="relative group">
        {isListening && (
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-400 to-sky-500 opacity-75 blur-md animate-pulse pointer-events-none" />
        )}
        {isProcessing && (
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-sky-500 via-indigo-500 to-emerald-500 opacity-60 blur-md animate-spin pointer-events-none" />
        )}
        <div className="relative">{children}</div>
      </div>
    </div>
  );
};
