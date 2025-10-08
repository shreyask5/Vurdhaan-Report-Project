/**
 * ColumnMappingWizard Component
 * Interactive wizard for mapping CSV columns to required fields
 */

import { useState, useEffect } from 'react';
import { Check, AlertCircle, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { ColumnMapping } from '@/types/validation';

interface ColumnMappingWizardProps {
  csvColumns: string[];
  suggestedMapping?: ColumnMapping;
  onMappingComplete: (mapping: ColumnMapping) => void;
  onSkip?: () => void;
}

const REQUIRED_COLUMNS = [
  {
    key: 'Flight Number',
    label: 'Flight Number',
    description: 'Unique flight identifier',
    required: true,
  },
  {
    key: 'Departure Airport ICAO',
    label: 'Departure Airport (ICAO)',
    description: 'Origin airport ICAO code (e.g., KJFK)',
    required: true,
  },
  {
    key: 'Arrival Airport ICAO',
    label: 'Arrival Airport (ICAO)',
    description: 'Destination airport ICAO code',
    required: true,
  },
  {
    key: 'Departure Date',
    label: 'Departure Date',
    description: 'Flight departure date',
    required: true,
  },
  {
    key: 'Fuel Uplift',
    label: 'Fuel Uplift',
    description: 'Fuel loaded before flight',
    required: true,
  },
  {
    key: 'Block-Off',
    label: 'Block-Off Time',
    description: 'When aircraft starts moving',
    required: false,
  },
  {
    key: 'Block-On',
    label: 'Block-On Time',
    description: 'When aircraft stops at destination',
    required: false,
  },
];

export function ColumnMappingWizard({
  csvColumns,
  suggestedMapping = {},
  onMappingComplete,
  onSkip,
}: ColumnMappingWizardProps) {
  const [mapping, setMapping] = useState<ColumnMapping>(suggestedMapping);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    setMapping(suggestedMapping);
  }, [suggestedMapping]);

  const handleColumnSelect = (requiredColumn: string, csvColumn: string) => {
    setMapping((prev) => ({
      ...prev,
      [requiredColumn]: csvColumn,
    }));
    setErrors([]);
  };

  const validateMapping = (): boolean => {
    const newErrors: string[] = [];

    // Check that all required columns are mapped
    REQUIRED_COLUMNS.forEach((col) => {
      if (col.required && !mapping[col.key]) {
        newErrors.push(`${col.label} is required`);
      }
    });

    // Check for duplicate mappings
    const usedColumns = new Set<string>();
    Object.values(mapping).forEach((csvCol) => {
      if (csvCol && usedColumns.has(csvCol)) {
        newErrors.push(`Column "${csvCol}" is mapped multiple times`);
      }
      usedColumns.add(csvCol);
    });

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleContinue = () => {
    if (validateMapping()) {
      onMappingComplete(mapping);
    }
  };

  const isMapped = (requiredColumn: string): boolean => {
    return !!mapping[requiredColumn];
  };

  const completionPercentage = Math.round(
    (Object.keys(mapping).filter((k) => mapping[k]).length / REQUIRED_COLUMNS.filter(c => c.required).length) * 100
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Map CSV Columns</CardTitle>
            <CardDescription>
              Match your CSV columns to the required flight data fields
            </CardDescription>
          </div>
          <div className="text-sm font-medium">
            <span className="text-2xl font-bold text-primary">{completionPercentage}%</span>
            <span className="text-muted-foreground ml-1">complete</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {errors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1">
                {errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {REQUIRED_COLUMNS.map((column) => (
            <div key={column.key} className="space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Label htmlFor={column.key} className="text-sm font-medium">
                    {column.label}
                    {column.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {column.description}
                  </p>
                </div>
                {isMapped(column.key) && (
                  <Check className="h-4 w-4 text-success mt-1" />
                )}
              </div>

              <Select
                value={mapping[column.key] || ''}
                onValueChange={(value) => handleColumnSelect(column.key, value)}
              >
                <SelectTrigger id={column.key}>
                  <SelectValue placeholder="Select a column from your CSV" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">-- Not mapped --</SelectItem>
                  {csvColumns.map((csvCol) => (
                    <SelectItem key={csvCol} value={csvCol}>
                      {csvCol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          {onSkip && (
            <Button variant="ghost" onClick={onSkip}>
              Skip for Now
            </Button>
          )}
          <Button
            onClick={handleContinue}
            className="ml-auto"
            disabled={completionPercentage < 100}
            size="lg"
          >
            Continue
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
