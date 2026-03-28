export function formatDateTime(value: string | number | Date | null | undefined): string {
  if (!value) return 'Unavailable';

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unavailable';

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0';
  return new Intl.NumberFormat('en').format(value);
}

export function formatSessionTtl(expiresAt: number | null | undefined): string {
  if (!expiresAt) return 'Unavailable';

  const millisecondsRemaining = expiresAt - Date.now();
  if (millisecondsRemaining <= 0) return 'Expired';

  const hours = Math.floor(millisecondsRemaining / (1000 * 60 * 60));
  const minutes = Math.floor((millisecondsRemaining % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) return `${hours}h ${minutes}m remaining`;
  return `${minutes}m remaining`;
}