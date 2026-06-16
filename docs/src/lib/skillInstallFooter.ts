export function skillIdForInstallFooter(path: string): string | null {
  const catalogMatch = path.match(/^skills\/catalog\/(?:custom|external)\/([^/]+)$/);
  return catalogMatch?.[1] ?? null;
}
