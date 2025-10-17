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

  const handleSchemeClick = (selectedScheme: SchemeType) => {
    setScheme(selectedScheme);
    onSelect(selectedScheme);
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
              type="button"
              onClick={() => handleSchemeClick(s.value)}
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
    </div>
  );
};
