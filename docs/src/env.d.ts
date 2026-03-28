interface ImportMetaEnv {
  readonly DOCS_ADMIN_PASSWORD?: string;
  readonly DOCS_ADMIN_SESSION_SECRET?: string;
  readonly PUBLIC_POSTHOG_KEY?: string;
  readonly PUBLIC_POSTHOG_HOST?: string;
  readonly POSTHOG_API_KEY?: string;
  readonly POSTHOG_PROJECT_ID?: string;
  readonly POSTHOG_API_HOST?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare namespace App {
  interface Locals {
    admin: {
      csrfToken: string;
      featureOverrides: Record<string, boolean>;
      isAuthenticated: boolean;
      requestId: string;
      session: {
        actor: 'shared-password';
        expiresAt: number;
        issuedAt: number;
        nonce: string;
      } | null;
    };
  }
}