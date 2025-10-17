import React, { useState } from 'react';
import { SchemeType } from '../../types/validation';

interface SchemeSelectorProps {
  onSelect: (scheme: SchemeType) => void;
  selectedScheme?: SchemeType | null;
}

const SCHEMES: { value: SchemeType; label: string; description: string }[] = [
  {
    value: 'CORSIA',
    label: 'CORSIA',
    description: 'Carbon Offsetting and Reduction Scheme for International Aviation'
  },
  {
    value: 'EU ETS',
    label: 'EU ETS',
    description: 'European Union Emissions Trading System'
  },
  {
    value: 'UK ETS',
    label: 'UK ETS',
    description: 'United Kingdom Emissions Trading Scheme'
  },
  {
    value: 'CH ETS',
    label: 'CH ETS',
    description: 'Swiss Emissions Trading System'
  },
  {
    value: 'ReFuelEU',
    label: 'ReFuelEU',
    description: 'ReFuelEU Aviation Initiative'
  }
];

export const SchemeSelector: React.FC<SchemeSelectorProps> = ({
  onSelect,
  selectedScheme
}) => {
  const [scheme, setScheme] = useState<SchemeType | null>(selectedScheme || null);

  const handleSubmit = () => {
    if (scheme) {
      onSelect(scheme);
    }
  };

  return (
    <div className="space-y-6">
      {/* Scheme Selection */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Select scheme
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-3">
          Choose the scheme that applies to your operations
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SCHEMES.map((s) => (
            <button
              key={s.value}
              onClick={() => setScheme(s.value)}
              className={`p-3 rounded-md border text-left transition-all ${
                scheme === s.value
                  ? 'border-primary bg-primary/10'
                  : 'border-gray-200 hover:border-primary hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800'
              }`}
            >
              <div className="font-semibold text-base text-gray-800 dark:text-gray-200">{s.label}</div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">{s.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end pt-3">
        <button
          onClick={handleSubmit}
          disabled={!scheme}
          className={`px-6 py-2 rounded-md font-semibold transition-all ${
            scheme
              ? 'bg-primary text-white hover:bg-primary-dark'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700'
          }`}
        >
          Continue to Monitoring Plan
        </button>
      </div>

      {/* Selection Summary */}
      {scheme && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Current Selection:</h4>
          <p className="text-sm text-blue-800 dark:text-blue-200">
            Scheme: <strong>{scheme}</strong>
          </p>
        </div>
      )}
    </div>
  );
};
