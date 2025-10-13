import React, { useState } from 'react';
import { SchemeType, AirlineSize } from '../../types/validation';

interface SchemeSelectorProps {
  onSelect: (scheme: SchemeType, airlineSize: AirlineSize) => void;
  selectedScheme?: SchemeType | null;
  selectedAirlineSize?: AirlineSize | null;
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

const AIRLINE_SIZES: { value: AirlineSize; label: string; range: string; description: string }[] = [
  {
    value: 'small',
    label: 'Small Operator',
    range: '1-30',
    description: 'Small operators with 1-30 aircraft'
  },
  {
    value: 'medium',
    label: 'Medium Operator',
    range: '30-80',
    description: 'Medium operators with 30-80 aircraft'
  },
  {
    value: 'large',
    label: 'Large Operator',
    range: '80+',
    description: 'Large operators with 80 or more aircraft'
  }
];

export const SchemeSelector: React.FC<SchemeSelectorProps> = ({
  onSelect,
  selectedScheme,
  selectedAirlineSize
}) => {
  const [scheme, setScheme] = useState<SchemeType | null>(selectedScheme || null);
  const [airlineSize, setAirlineSize] = useState<AirlineSize | null>(selectedAirlineSize || null);

  const handleSubmit = () => {
    if (scheme && airlineSize) {
      onSelect(scheme, airlineSize);
    }
  };

  return (
    <div className="space-y-8">
      {/* Scheme Selection */}
      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          1. Select Scheme
        </h3>
        <p className="text-gray-600 mb-4">
          Choose the emissions trading scheme that applies to your operations
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SCHEMES.map((s) => (
            <button
              key={s.value}
              onClick={() => setScheme(s.value)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                scheme === s.value
                  ? 'border-primary bg-primary bg-opacity-10'
                  : 'border-gray-200 hover:border-primary hover:bg-gray-50'
              }`}
            >
              <div className="font-semibold text-lg text-gray-800">{s.label}</div>
              <div className="text-sm text-gray-600 mt-1">{s.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Airline Size Selection */}
      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          2. Select Airline Size
        </h3>
        <p className="text-gray-600 mb-4">
          Choose the category that best describes your airline's fleet size
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {AIRLINE_SIZES.map((size) => (
            <button
              key={size.value}
              onClick={() => setAirlineSize(size.value)}
              className={`p-6 rounded-lg border-2 text-center transition-all ${
                airlineSize === size.value
                  ? 'border-primary bg-primary bg-opacity-10'
                  : 'border-gray-200 hover:border-primary hover:bg-gray-50'
              }`}
            >
              <div className="text-3xl font-bold text-primary mb-2">{size.range}</div>
              <div className="font-semibold text-lg text-gray-800">{size.label}</div>
              <div className="text-sm text-gray-600 mt-2">{size.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSubmit}
          disabled={!scheme || !airlineSize}
          className={`px-8 py-3 rounded-lg font-semibold transition-all ${
            scheme && airlineSize
              ? 'bg-primary text-white hover:bg-primary-dark'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Continue to Monitoring Plan
        </button>
      </div>

      {/* Selection Summary */}
      {(scheme || airlineSize) && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-2">Current Selection:</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            {scheme && <li>Scheme: <strong>{scheme}</strong></li>}
            {airlineSize && (
              <li>
                Airline Size: <strong>
                  {AIRLINE_SIZES.find(s => s.value === airlineSize)?.label}
                </strong>
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
