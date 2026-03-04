import { memo } from 'react';
import { Spinner } from '@/components/ui/spinner';

export const LoadingDisplay = memo(() => (
  <div className="flex h-full w-full flex-col items-center justify-center gap-2">
    <Spinner size={24} />
    <span>Loading...</span>
  </div>
));

LoadingDisplay.displayName = 'LoadingDisplay';
