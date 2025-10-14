import React, { useState } from 'react';

interface MonitoringPlanEditorProps {
  data: any;
  onEdit: (path: string[], value: any) => void;
}

export const MonitoringPlanEditor: React.FC<MonitoringPlanEditorProps> = ({ data, onEdit }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['operator', 'flight_attribution', 'activities']));

  const toggleSection = (sectionKey: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionKey)) {
        next.delete(sectionKey);
      } else {
        next.add(sectionKey);
      }
      return next;
    });
  };

  const renderValue = (path: string[], value: any, label: string): JSX.Element => {
    // Handle null/undefined
    if (value === null || value === undefined) {
      return (
        <div className="mb-3" key={path.join('.')}>
          <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            value=""
            onChange={(e) => onEdit(path, e.target.value)}
            placeholder="No value"
          />
        </div>
      );
    }

    // Handle primitives (string, number, boolean)
    if (typeof value === 'string' || typeof value === 'number') {
      // Use textarea for long strings
      const isLongText = typeof value === 'string' && value.length > 100;

      return (
        <div className="mb-3" key={path.join('.')}>
          <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
          {isLongText ? (
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              rows={4}
              value={String(value)}
              onChange={(e) => onEdit(path, e.target.value)}
            />
          ) : (
            <input
              type={typeof value === 'number' ? 'number' : 'text'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              value={String(value)}
              onChange={(e) => onEdit(path, typeof value === 'number' ? Number(e.target.value) : e.target.value)}
            />
          )}
        </div>
      );
    }

    if (typeof value === 'boolean') {
      return (
        <div className="mb-3 flex items-center" key={path.join('.')}>
          <input
            type="checkbox"
            id={path.join('.')}
            className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
            checked={value}
            onChange={(e) => onEdit(path, e.target.checked)}
          />
          <label htmlFor={path.join('.')} className="ml-2 text-sm font-medium text-gray-700">
            {label}
          </label>
        </div>
      );
    }

    // Handle arrays
    if (Array.isArray(value)) {
      return (
        <div className="mb-4" key={path.join('.')}>
          <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
          <div className="space-y-2 pl-4 border-l-2 border-gray-200">
            {value.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No items</p>
            ) : (
              value.map((item, index) => (
                <div key={index} className="bg-gray-50 p-3 rounded-lg">
                  {renderValue([...path, String(index)], item, `${label} #${index + 1}`)}
                </div>
              ))
            )}
          </div>
        </div>
      );
    }

    // Handle objects - create collapsible section
    if (typeof value === 'object') {
      const sectionKey = path.join('.');
      const isExpanded = expandedSections.has(sectionKey);

      return (
        <div className="mb-4" key={sectionKey}>
          <button
            type="button"
            onClick={() => toggleSection(sectionKey)}
            className="w-full flex items-center justify-between bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg transition-colors"
          >
            <span className="text-sm font-semibold text-gray-800">{label}</span>
            <span className="text-gray-600">{isExpanded ? '▼' : '▶'}</span>
          </button>
          {isExpanded && (
            <div className="mt-2 pl-4 border-l-2 border-gray-300 space-y-2">
              {Object.keys(value).length === 0 ? (
                <p className="text-sm text-gray-500 italic">No fields</p>
              ) : (
                Object.entries(value).map(([key, val]) =>
                  renderValue([...path, key], val, formatLabel(key))
                )
              )}
            </div>
          )}
        </div>
      );
    }

    return <div key={path.join('.')}>Unsupported type</div>;
  };

  const formatLabel = (key: string): string => {
    // Convert snake_case or camelCase to Title Case
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (str) => str.toUpperCase())
      .trim();
  };

  const renderSection = (sectionKey: string, sectionData: any, sectionTitle: string) => {
    if (!sectionData) return null;

    return (
      <div key={sectionKey} className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>{getSectionIcon(sectionKey)}</span>
          {sectionTitle}
        </h4>
        <div className="space-y-2">
          {typeof sectionData === 'object' && !Array.isArray(sectionData) ? (
            Object.entries(sectionData).map(([key, value]) =>
              renderValue([sectionKey, key], value, formatLabel(key))
            )
          ) : (
            renderValue([sectionKey], sectionData, sectionTitle)
          )}
        </div>
      </div>
    );
  };

  const getSectionIcon = (key: string): string => {
    const icons: { [key: string]: string } = {
      operator: '🏢',
      flight_attribution: '✈️',
      activities: '📋',
      basic_info: 'ℹ️',
      fuel_data_collection: '⛽',
      primary_data_source: '📊',
      secondary_source: '📑',
      geographical_presence: '🌍',
      monitoring_plan_processes: '📈',
      aircraft_types: '🛩️',
      fuel_use_monitoring: '⛽',
      emissions_monitoring: '💨',
    };
    return icons[key] || '📄';
  };

  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No monitoring plan data available</p>
      </div>
    );
  }

  // Define the order of sections to display
  const prioritySections = [
    'operator',
    'flight_attribution',
    'activities',
    'basic_info',
    'fuel_data_collection',
    'primary_data_source',
    'secondary_source',
    'geographical_presence',
    'aircraft_types',
    'fuel_use_monitoring',
    'emissions_monitoring',
    'monitoring_plan_processes',
  ];

  // Separate priority sections from other fields
  const remainingKeys = Object.keys(data).filter((key) => !prioritySections.includes(key));

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> Review and edit the extracted information below. Changes are automatically saved.
        </p>
      </div>

      {/* Priority sections in order */}
      {prioritySections.map((key) => {
        if (data[key]) {
          return renderSection(key, data[key], formatLabel(key));
        }
        return null;
      })}

      {/* Remaining sections */}
      {remainingKeys.length > 0 && (
        <>
          <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Additional Fields</h3>
          {remainingKeys.map((key) =>
            renderSection(key, data[key], formatLabel(key))
          )}
        </>
      )}
    </div>
  );
};
