// src/components/ui/date-range-picker.tsx
'use client';

import * as React from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Check, FunnelPlus } from 'lucide-react';
import { DateRange } from 'react-day-picker';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
// Correctly import PopoverClose from the underlying Radix UI library
import { PopoverClose } from '@radix-ui/react-popover';

interface DatePickerWithRangeProps {
  date: DateRange | undefined;
  setDate: (date: DateRange | undefined) => void;
  className?: string;
  onApply?: () => void;
}

export function DatePickerWithRange({
  date,
  setDate,
  className,
  onApply,
}: DatePickerWithRangeProps) {
  const [month, setMonth] = React.useState<Date | undefined>(date?.from);
  
  return (
    <div className={cn('grid gap-2', className)}>
      <Popover onOpenChange={(open) => {
        if (open && date?.from) {
          setMonth(date.from);
        }
      }}>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={'outline'}
            className={cn(
              'w-[300px] justify-start text-left font-normal',
              !date && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, 'LLL dd, y')} -{' '}
                  {format(date.to, 'LLL dd, y')}
                </>
              ) : (
                format(date.from, 'LLL dd, y')
              )
            ) : (
              <span>Pick a date range</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            month={month}
            onMonthChange={setMonth}
            selected={date}
            onSelect={setDate}
            numberOfMonths={2}
          />
          {onApply && (
            <div className="p-3 flex justify-end">
                

              <PopoverClose asChild>
                <Button onClick={onApply}>
                  <FunnelPlus className="outline" />
                  Filter Dates
                </Button>
              </PopoverClose>
            </div>
          )}
        </PopoverContent>
      </Popover>
    </div>
  );
}