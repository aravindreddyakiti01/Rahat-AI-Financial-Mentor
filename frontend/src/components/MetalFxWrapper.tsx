import React from 'react';

interface Props {
  preset?: 'chromatic' | 'silver' | 'gold';
  variant?: 'button' | 'circle';
  strength?: number;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
}

export const MetalFxWrapper: React.FC<Props> = ({
  variant = 'button',
  children,
  className = '',
  onClick,
  disabled = false,
}) => {
  return (
    <div className={`inline-block ${className}`}>
      <button
        type="button"
        onClick={disabled ? undefined : onClick}
        disabled={disabled}
        className={`metal-btn px-4 py-2 rounded-xl flex items-center justify-center font-medium text-sm text-slate-100 disabled:opacity-50 disabled:cursor-not-allowed ${
          variant === 'circle' ? 'w-10 h-10 !p-0 rounded-full' : ''
        }`}
      >
        {children}
      </button>
    </div>
  );
};
