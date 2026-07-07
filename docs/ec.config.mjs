import { defineEcConfig } from '@astrojs/starlight/expressive-code';
import { starlightCodeblockIcons } from './src/lib/starlight-codeblock-icons.mjs';

export default defineEcConfig({
  plugins: [starlightCodeblockIcons()],
});
