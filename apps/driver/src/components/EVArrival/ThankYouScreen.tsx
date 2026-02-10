interface Props {
  merchantName: string;
}

export function ThankYouScreen({ merchantName }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      <div className="text-6xl mb-6">🎉</div>

      <h1 className="text-3xl font-bold text-gray-900 mb-4 text-center">
        Credit Applied!
      </h1>

      <p className="text-xl text-gray-700 mb-2 text-center">
        Thanks for visiting {merchantName}
      </p>

      <p className="text-gray-500 text-center">
        Your charging credit has been applied.
      </p>
    </div>
  );
}
