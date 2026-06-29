import type { APIRoute } from 'astro';

import { skillResearchRedirectTarget } from '../../lib/skill-research-redirect';

export const prerender = false;

export const GET: APIRoute = ({ params, redirect }) => {
  const raw = params.id;
  if (!raw || Array.isArray(raw)) {
    return new Response('Not found', { status: 404 });
  }
  return redirect(skillResearchRedirectTarget(decodeURIComponent(raw)), 301);
};
