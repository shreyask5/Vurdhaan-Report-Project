/**
 * ValidationForm Component
 * Form for setting validation parameters (date range, fuel method, etc.)
 */

import { useState } from 'react';
import { Calendar, Fuel, Filter, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { FuelMethod, DateFormat } from '@/types/validation';

interface ValidationFormProps {
  onValidate: (params: ValidationFormData) => void;
  isValidating?: boolean;
}

export interface ValidationFormData {
  monitoring_year: string;
  date_format: DateFormat;
  flight_starts_with: string;
  fuel_method: FuelMethod;
}

export function ValidationForm({ onValidate, isValidating = false }: ValidationFormProps) {
  const currentYear = new Date().getFullYear();

  const [formData, setFormData] = useState<ValidationFormData>({
    monitoring_year: currentYear.toString(),
    date_format: 'DMY',
    flight_starts_with: '',
    fuel_method: 'Block Off - Block On',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onValidate(formData);
  };

  const updateField = <K extends keyof ValidationFormData>(
    field: K,
    value: ValidationFormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Validation Parameters</CardTitle>
        <CardDescription>
          Configure validation settings for your flight data
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Monitoring Year */}
          <div className="space-y-2">
            <Label htmlFor="monitoring-year" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Monitoring Year
            </Label>
            <Select
              value={formData.monitoring_year}
              onValueChange={(value) => updateField('monitoring_year', value)}
            >
              <SelectTrigger id="monitoring-year">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 10 }, (_, i) => currentYear - 5 + i).map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              The year for which you're reporting flight data
            </p>
          </div>

          {/* Date Format */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Date Format
            </Label>
            <RadioGroup
              value={formData.date_format}
              onValueChange={(value: DateFormat) => updateField('date_format', value)}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="DMY" id="dmy" />
                <Label htmlFor="dmy" className="font-normal cursor-pointer">
                  DD/MM/YYYY
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="MDY" id="mdy" />
                <Label htmlFor="mdy" className="font-normal cursor-pointer">
                  MM/DD/YYYY
                </Label>
              </div>
            </RadioGroup>
            <p className="text-xs text-muted-foreground">
              Date format used in your CSV file
            </p>
          </div>

          {/* Fuel Calculation Method */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Fuel className="h-4 w-4" />
              Fuel Calculation Method
            </Label>
            <RadioGroup
              value={formData.fuel_method}
              onValueChange={(value: FuelMethod) => updateField('fuel_method', value)}
              className="space-y-2"
            >
              <div className="flex items-start space-x-2 p-3 rounded-lg border border-border hover:bg-accent transition-colors">
                <RadioGroupItem value="Block Off - Block On" id="block-method" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="block-method" className="font-medium cursor-pointer">
                    Block Off - Block On
                  </Label>
                  <p className="text-xs text-muted-foreground mt-1">
                    Calculate fuel burn using block-off and block-on times
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-2 p-3 rounded-lg border border-border hover:bg-accent transition-colors">
                <RadioGroupItem value="Method B" id="method-b" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="method-b" className="font-medium cursor-pointer">
                    Method B
                  </Label>
                  <p className="text-xs text-muted-foreground mt-1">
                    Alternative fuel calculation method
                  </p>
                </div>
              </div>
            </RadioGroup>
          </div>

          {/* Flight Prefix Filter */}
          <div className="space-y-2">
            <Label htmlFor="flight-prefix" className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Flight Number Prefix (Optional)
            </Label>
            <Input
              id="flight-prefix"
              placeholder="e.g., AA, UA, DL"
              value={formData.flight_starts_with}
              onChange={(e) => updateField('flight_starts_with', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Filter flights by prefix. Leave empty to process all flights.
            </p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={isValidating}
          >
            {isValidating ? (
              <>Validating...</>
            ) : (
              <>
                Validate Flight Data
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
