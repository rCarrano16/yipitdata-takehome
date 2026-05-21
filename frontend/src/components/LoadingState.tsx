/** A shared, centered loading message for any async view. */
export default function LoadingState({
  message = 'Loading...',
}: {
  message?: string
}) {
  return <div className="state">{message}</div>
}
