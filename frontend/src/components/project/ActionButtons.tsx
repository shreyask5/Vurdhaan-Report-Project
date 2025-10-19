// Action Buttons Component
// From index4.html:1253-1287

import React from 'react';

interface ActionButtonsProps {
  projectId: string;
  onSaveCorrections: () => void;
  onIgnoreErrors: () => void;
  onDownloadClean: () => void;
  onDownloadErrors: () => void;
  onOpenChat: () => void;
  onStartOver: () => void;
  hasCorrections?: boolean;
  aiChatEnabled?: boolean;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onSaveCorrections,
  onIgnoreErrors,
  onDownloadClean,
  onDownloadErrors,
  onOpenChat,
  onStartOver,
  hasCorrections = false,
  aiChatEnabled = false
}) => {
  const baseButtonClass = "inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 justify-center min-w-[200px] md:min-w-0 md:flex-1";
  const successButtonClass = `${baseButtonClass} bg-gradient-to-br from-success to-success-light text-white hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:hover:translate-y-0`;
  const dangerButtonClass = `${baseButtonClass} bg-gradient-to-br from-error to-error-light text-white hover:shadow-lg hover:-translate-y-0.5`;
  const primaryButtonClass = `${baseButtonClass} bg-gradient-primary text-white hover:shadow-lg hover:-translate-y-0.5`;
  const highlightButtonClass = `${baseButtonClass} bg-gradient-to-br from-warning to-warning-light text-white hover:shadow-lg hover:-translate-y-0.5`;
  const secondaryButtonClass = `${baseButtonClass} bg-gradient-to-br from-gray-600 to-gray-700 text-white hover:shadow-lg hover:-translate-y-0.5`;

  return (
    <div className="space-y-3">
      {/* Primary Actions */}
      <div className="flex flex-col md:flex-row gap-3">
        <button
          className={successButtonClass}
          onClick={onSaveCorrections}
          disabled={!hasCorrections}
        >
          <span className="text-xl">💾</span> Save Corrections
        </button>
        <button className={dangerButtonClass} onClick={onIgnoreErrors}>
          <span className="text-xl">⚠️</span> Ignore Remaining Errors
        </button>
      </div>

      {/* Download Actions */}
      <div className="flex flex-col md:flex-row gap-3">
        <button className={primaryButtonClass} onClick={onDownloadClean}>
          <span className="text-xl">📥</span> Download Clean Data CSV
        </button>
        <button className={primaryButtonClass} onClick={onDownloadErrors}>
          <span className="text-xl">📥</span> Download Errors CSV
        </button>
      </div>

      {/* Analysis & Reset Actions */}
      <div className="flex flex-col md:flex-row gap-3">
        {aiChatEnabled && (
          <button className={highlightButtonClass} onClick={onOpenChat}>
            <span className="text-xl">💬</span> Analyze Data with AI Chat
          </button>
        )}
        <button className={secondaryButtonClass} onClick={onStartOver}>
          <span className="text-xl">🔄</span> Start Over
        </button>
      </div>
    </div>
  );
};
