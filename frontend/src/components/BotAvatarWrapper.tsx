import React from 'react';

interface Props {
  size?: number;
  state?: 'default' | 'working' | 'sleeping';
  className?: string;
}

export const BotAvatarWrapper: React.FC<Props> = ({
  size = 36,
  state = 'default',
  className = '',
}) => {
  return (
    <div
      className={`inline-flex items-center justify-center rounded-full overflow-hidden shrink-0 transition-transform duration-300 ${
        state === 'working' ? 'scale-105 rotate-3' : ''
      } ${className}`}
      style={{ width: size, height: size }}
    >
      <div className="w-full h-full rounded-full bg-gradient-to-tr from-emerald-700 via-teal-600 to-emerald-500 flex items-center justify-center p-1.5 shadow-sm border border-emerald-400/30">
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full text-white" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
      </div>
    </div>
  );
};
