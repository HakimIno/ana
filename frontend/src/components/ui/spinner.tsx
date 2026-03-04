import { LucideProps } from 'lucide-react';
import { Loader2 } from 'lucide-react';

function cn(...classes: (string | undefined | false)[]) {
    return classes.filter(Boolean).join(' ');
}

interface SpinnerProps extends LucideProps {
    className?: string;
    size?: number;
}

export const Spinner = ({ className, size = 24, ...props }: SpinnerProps) => {
    return (
        <Loader2
            className={cn('animate-spin text-muted-foreground', className)}
            size={size}
            {...props}
        />
    );
};
