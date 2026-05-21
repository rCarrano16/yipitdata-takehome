interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

/** A shared error panel. When `onRetry` is given it renders a retry button. */
export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="state state-error">
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
