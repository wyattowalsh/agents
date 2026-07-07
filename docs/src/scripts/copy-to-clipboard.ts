/** Delegated clipboard copy for install commands and code blocks across docs surfaces. */

const COPY_RESET_MS = 1600;

function announceCopyStatus(message: string): void {
  let status = document.getElementById('agents-copy-status');
  if (!status) {
    status = document.createElement('div');
    status.id = 'agents-copy-status';
    status.setAttribute('aria-live', 'polite');
    status.setAttribute('aria-atomic', 'true');
    Object.assign(status.style, {
      border: '0',
      clip: 'rect(0, 0, 0, 0)',
      height: '1px',
      margin: '-1px',
      overflow: 'hidden',
      padding: '0',
      position: 'absolute',
      whiteSpace: 'nowrap',
      width: '1px',
    });
    document.body.append(status);
  }
  status.textContent = message;
}

function resolveCopyText(button: HTMLButtonElement): string {
  const copyId = button.getAttribute('data-copy-command');
  if (copyId) {
    const root = document.querySelector(`[data-install-command="${copyId}"]`);
    return root?.querySelector('code')?.textContent ?? '';
  }

  const direct = button.getAttribute('data-copy-text') ?? button.getAttribute('data-install-command');
  if (direct) {
    return direct;
  }

  if (button.classList.contains('install-command__copy')) {
    return button.closest('.install-command')?.querySelector('code')?.textContent ?? '';
  }

  return '';
}

async function copyFromButton(button: HTMLButtonElement): Promise<void> {
  const text = resolveCopyText(button);
  if (!text) {
    return;
  }

  const previous = button.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = 'Copied';
    announceCopyStatus('Copied command to clipboard.');
  } catch {
    button.textContent = 'Copy failed';
    announceCopyStatus('Copy failed.');
  }

  window.setTimeout(() => {
    button.textContent = previous;
  }, COPY_RESET_MS);
}

document.addEventListener('click', (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const button = target.closest<HTMLButtonElement>(
    '[data-copy-command], [data-copy-text], .install-command__copy, .skill-install-copy',
  );
  if (!button) {
    return;
  }

  event.preventDefault();
  void copyFromButton(button);
});
