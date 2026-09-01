'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

// Define the props our component will accept
interface DeltaIndicatorProps {
  value: number | string | null | undefined;
  label?: string; // Optional label
  className?: string; // Optional additional class names
}

// use case:
// <DeltaIndicator value={data?.summary.delta_total_conversations_percentage} />


export function DeltaIndicator({ 
  value, 
  label = "from last period", // Default label
  className 
}: DeltaIndicatorProps) {

  // 1. Get the raw value, which might be a string, null, or undefined.
  //    Default to the string '0' if it's null/undefined.
  const rawValue = value ?? '0';

  // 2. Convert the raw string value into a number using parseFloat().
  const percentageChange = parseFloat(String(rawValue));

  // 3. Define variables for the parts that change
  let IconComponent;
  let colorClass;
  let prefix = '';

  // 4. Use a clear if/else block to handle all three cases
  if (percentageChange > 0) {
    IconComponent = TrendingUp;
    colorClass = 'text-green-500';
    prefix = '+';
  } else if (percentageChange < 0) {
    IconComponent = TrendingDown;
    colorClass = 'text-red-500';
  } else {
    // This correctly handles the case where the change is exactly 0
    IconComponent = Minus;
    colorClass = 'text-muted-foreground';
  }

  // 5. Render a single, clean JSX structure using the variables
  return (
    <span className={cn("inline-flex items-center text-xs", className)}>
      <IconComponent className={cn('h-3 w-3 inline mr-1', colorClass)} />
      {prefix}{percentageChange.toFixed(0)}% {label}
    </span>
  );
}