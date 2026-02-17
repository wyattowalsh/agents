import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeBlack from 'starlight-theme-black';
import starlightSiteGraph from 'starlight-site-graph';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';

export default defineConfig({
  site: 'https://agents.w4w.dev',
  integrations: [
    starlight({
      title: 'agents',
      description: 'AI agent artifacts, configs, skills, tools, and more',
      plugins: [
        starlightThemeBlack({
          navLinks: [
            { label: 'Skills', link: '/skills/' },
            { label: 'CLI', link: '/cli/' },
          ],
        }),
        starlightLinksValidator(),
        starlightLlmsTxt(),
        starlightSiteGraph({
          graphConfig: {
            depth: 2,
            renderArrows: true,
            enableZoom: true,
            enablePan: true,
            enableDrag: true,
            enableHover: true,
            enableClick: 'auto',
            actions: ['fullscreen', 'depth', 'reset-zoom'],
          },
          sitemapConfig: { includeExternalLinks: false },
        }),
      ],
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/wyattowalsh/agents' }],
      customCss: ['./src/styles/custom.css'],
      components: {
        Head: './src/components/starlight/Head.astro',
      },
      sidebar: [
        { slug: '' },
        {
          label: 'Skills',
          autogenerate: { directory: 'skills' },
          badge: { text: 'Core', variant: 'tip' },
        },
        {
          label: 'Agents',
          autogenerate: { directory: 'agents' },
        },
        {
          label: 'MCP Servers',
          autogenerate: { directory: 'mcp' },
        },
        { slug: 'cli', label: 'CLI Reference' },
      ],
      editLink: { baseUrl: 'https://github.com/wyattowalsh/agents/edit/main/docs/' },
    }),
  ],
});
