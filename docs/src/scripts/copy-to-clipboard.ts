/** Delegated clipboard copy for install commands and code blocks across docs surfaces. */

const COPY_RESET_MS = 1600;

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
  } catch {
    button.textContent = 'Copy failed';
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