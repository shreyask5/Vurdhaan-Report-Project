// Success Section Component
// From index4.html:1291-1311

import React from 'react';

interface SuccessSectionProps {
  onGenerateReport: () => void;
  onDownloadClean: () => void;
  onRevalidate: () => void;
}

export const SuccessSection: React.FC<SuccessSectionProps> = ({
  onGenerateReport,
  onDownloadClean,
  onRevalidate
}) => {
  return (
    <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-success-light rounded-xl p-12 text-center">
      <div className="mb-8">
        <div className="w-20 h-20 bg-gradient-to-br from-success to-success-light text-white rounded-full flex items-center justify-center text-5xl font-bold mx-auto mb-6 shadow-lg animate-pulse">
          ✓
        </div>
        <h2 className="text-3xl font-bold text-green-800 mb-2">Validation Complete!</h2>
        <p className="text-green-900 mb-8">
          Your CSV file has been successfully validated.
        </p>
      </div>

      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex flex-col md:flex-row gap-4 justify-center">
          <button
            className="inline-flex items-center gap-2 px-8 py-5 bg-gradient-primary text-white rounded-lg font-semibold text-base hover:shadow-lg hover:-translate-y-0.5 transition-all"
            onClick={onGenerateReport}
          >
            <span className="text-xl">📊</span> Generate CORSIA Report
          </button>
        </div>

        <div className="flex flex-col md:flex-row gap-4 justify-center">
          <button
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-br from-success to-success-light text-white rounded-lg font-semibold hover:shadow-lg hover:-translate-y-0.5 transition-all flex-1 md:flex-none md:min-w-[200px] justify-center"
            onClick={onDownloadClean}
          >
            <span className="text-xl">📥</span> Download Clean Data CSV
          </button>
          <button
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-br from-gray-600 to-gray-700 text-white rounded-lg font-semibold hover:shadow-lg hover:-translate-y-0.5 transition-all flex-1 md:flex-none md:min-w-[200px] justify-center"
            onClick={onRevalidate}
          >
            <span className="text-xl">🔄</span> Re-Validate & Process Again
          </button>
        </div>
      </div>
    </div>
  );
};
