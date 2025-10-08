/**
 * ErrorDisplay Component
 * Displays validation errors grouped by category with inline editing
 */

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, Download, Save } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import type { ValidationErrorData, ErrorCategory as ErrorCategoryType } from '@/types/validation';

interface ErrorDisplayProps {
  errorData: ValidationErrorData;
  onSaveCorrections?: (corrections: { [rowIdx: number]: any }) => Promise<void>;
  onDownloadClean?: () => void;
  onDownloadErrors?: () => void;
}

export function ErrorDisplay({
  errorData,
  onSaveCorrections,
  onDownloadClean,
  onDownloadErrors,
}: ErrorDisplayProps) {
  const [corrections, setCorrections] = useState<{ [rowIdx: number]: any }>({});
  const [isSaving, setIsSaving] = useState(false);

  const handleCellEdit = (rowIdx: number, column: string, value: string) => {
    setCorrections((prev) => ({
      ...prev,
      [rowIdx]: {
        ...(prev[rowIdx] || {}),
        [column]: value,
      },
    }));
  };

  const handleSaveCorrections = async () => {
    if (!onSaveCorrections || Object.keys(corrections).length === 0) return;

    setIsSaving(true);
    try {
      await onSaveCorrections(corrections);
      setCorrections({});
    } catch (error) {
      console.error('Failed to save corrections:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const hasCorrections = Object.keys(corrections).length > 0;

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Validation Results</CardTitle>
              <CardDescription>Review and correct errors in your flight data</CardDescription>
            </div>
            <div className="flex gap-2">
              {onDownloadClean && (
                <Button variant="outline" size="sm" onClick={onDownloadClean}>
                  <Download className="mr-2 h-4 w-4" />
                  Clean Data
                </Button>
              )}
              {onDownloadErrors && (
                <Button variant="outline" size="sm" onClick={onDownloadErrors}>
                  <Download className="mr-2 h-4 w-4" />
                  Errors
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <div className="text-2xl font-bold text-success">
                {errorData.total_clean_rows}
              </div>
              <div className="text-sm text-muted-foreground">Clean Rows</div>
            </div>
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="text-2xl font-bold text-destructive">
                {errorData.total_errors}
              </div>
              <div className="text-sm text-muted-foreground">Errors Found</div>
            </div>
          </div>

          {hasCorrections && (
            <Button
              onClick={handleSaveCorrections}
              disabled={isSaving}
              className="w-full mt-4"
            >
              <Save className="mr-2 h-4 w-4" />
              {isSaving ? 'Saving...' : `Save ${Object.keys(corrections).length} Correction(s)`}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Error Categories */}
      {errorData.categories.map((category, idx) => (
        <ErrorCategoryCard
          key={idx}
          category={category}
          rowsData={errorData.rows_data}
          corrections={corrections}
          onCellEdit={handleCellEdit}
        />
      ))}
    </div>
  );
}

interface ErrorCategoryCardProps {
  category: ErrorCategoryType;
  rowsData: { [key: number]: any };
  corrections: { [rowIdx: number]: any };
  onCellEdit: (rowIdx: number, column: string, value: string) => void;
}

function ErrorCategoryCard({
  category,
  rowsData,
  corrections,
  onCellEdit,
}: ErrorCategoryCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  const getCategoryColor = (name: string) => {
    const colors: { [key: string]: string } = {
      SEQUENCE_ERRORS: 'bg-yellow-500',
      DATE_ERRORS: 'bg-orange-500',
      FUEL_ERRORS: 'bg-red-500',
      ICAO_ERRORS: 'bg-blue-500',
      OTHER: 'bg-gray-500',
    };
    return colors[name] || 'bg-gray-500';
  };

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-accent/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isOpen ? (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
                <div className={`w-3 h-3 rounded-full ${getCategoryColor(category.name)}`} />
                <CardTitle className="text-lg">
                  {category.name.replace(/_/g, ' ')}
                </CardTitle>
              </div>
              <Badge variant="destructive">{category.total_count} errors</Badge>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="space-y-4">
            {category.errors.map((errorGroup, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/50">
                  <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{errorGroup.reason}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Affects {errorGroup.count} row(s)
                    </p>
                  </div>
                </div>

                {/* Error Rows */}
                {errorGroup.rows.slice(0, 5).map((errorRow) => {
                  const rowData = rowsData[errorRow.row_idx] || {};
                  const rowCorrections = corrections[errorRow.row_idx] || {};

                  return (
                    <div
                      key={errorRow.row_idx}
                      className="p-3 rounded-lg border border-border bg-card"
                    >
                      <div className="text-xs text-muted-foreground mb-2">
                        Row {errorRow.row_idx}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {Object.keys(rowData).slice(0, 6).map((col) => (
                          <div key={col} className="space-y-1">
                            <label className="text-xs font-medium text-muted-foreground">
                              {col}
                            </label>
                            <Input
                              value={rowCorrections[col] ?? rowData[col] ?? ''}
                              onChange={(e) =>
                                onCellEdit(errorRow.row_idx, col, e.target.value)
                              }
                              className="h-8 text-xs"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}

                {errorGroup.rows.length > 5 && (
                  <p className="text-xs text-muted-foreground text-center">
                    ... and {errorGroup.rows.length - 5} more row(s)
                  </p>
                )}
              </div>
            ))}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
