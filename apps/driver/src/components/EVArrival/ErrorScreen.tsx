import { Button } from '../shared/Button';

interface Props {
  message: string;
  onRetry?: () => void;
}

export function ErrorScreen({ message, onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      <div className="text-5xl mb-6">⚠️</div>

      <h1 className="text-2xl font-bold text-gray-900 mb-4 text-center">
        Something went wrong
      </h1>

      <p className="text-gray-600 mb-8 text-center max-w-md">
        {message}
      </p>

      {onRetry && (
        <Button onClick={onRetry} className="w-full max-w-md">
          Try Again
        </Button>
      )}
    </div>
  );
}
