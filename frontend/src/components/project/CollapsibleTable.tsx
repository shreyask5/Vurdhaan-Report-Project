/**
 * CollapsibleTable Component
 * Displays SQL query results in a collapsible table with CSV export
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { chatService } from '@/services/chat';

interface CollapsibleTableProps {
  data: any[];
  title?: string;
  defaultOpen?: boolean;
  maxRows?: number;
}

export function CollapsibleTable({
  data,
  title = 'Query Results',
  defaultOpen = true,
  maxRows = 100,
}: CollapsibleTableProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!data || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);
  const displayData = data.slice(0, maxRows);
  const hasMore = data.length > maxRows;

  const handleExport = () => {
    try {
      chatService.exportTableToCSV(data, `${title.replace(/\s+/g, '_').toLowerCase()}.csv`);
    } catch (error: any) {
      console.error('Export failed:', error);
    }
  };

  return (
    <Card className="mt-4">
      <div className="p-4 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
            className="h-8 w-8 p-0"
          >
            {isOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
          <div>
            <h3 className="font-semibold text-sm">{title}</h3>
            <p className="text-xs text-muted-foreground">
              {data.length} row{data.length !== 1 ? 's' : ''} × {columns.length} column
              {columns.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleExport}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {isOpen && (
        <CardContent className="p-0">
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-muted z-10">
                <TableRow>
                  {columns.map((col) => (
                    <TableHead key={col} className="font-semibold whitespace-nowrap">
                      {col}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayData.map((row, idx) => (
                  <TableRow key={idx}>
                    {columns.map((col) => (
                      <TableCell key={col} className="text-sm">
                        {formatCellValue(row[col])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {hasMore && (
            <div className="p-4 text-center text-sm text-muted-foreground border-t border-border">
              Showing first {maxRows} of {data.length} rows. Export to CSV to view all data.
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

function formatCellValue(value: any): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'number') {
    // Format numbers with appropriate precision
    return value.toLocaleString(undefined, {
      maximumFractionDigits: 2,
    });
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  if (value instanceof Date) {
    return value.toLocaleDateString();
  }

  return String(value);
}
