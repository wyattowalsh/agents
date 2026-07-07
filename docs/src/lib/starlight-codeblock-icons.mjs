const languageIcons = new Map([
  ['astro', 'i-material-icon-theme:astro'],
  ['bash', 'i-material-icon-theme:console'],
  ['css', 'i-material-icon-theme:css'],
  ['html', 'i-material-icon-theme:html'],
  ['javascript', 'i-material-icon-theme:javascript'],
  ['js', 'i-material-icon-theme:javascript'],
  ['json', 'i-material-icon-theme:json'],
  ['md', 'i-material-icon-theme:markdown'],
  ['mdx', 'i-material-icon-theme:mdx'],
  ['shell', 'i-material-icon-theme:console'],
  ['sh', 'i-material-icon-theme:console'],
  ['ts', 'i-material-icon-theme:typescript'],
  ['typescript', 'i-material-icon-theme:typescript'],
  ['yaml', 'i-material-icon-theme:yaml'],
  ['yml', 'i-material-icon-theme:yaml'],
]);

const element = (tagName, properties = {}, children = []) => ({
  type: 'element',
  tagName,
  properties,
  children,
});

const extensionIcons = new Map([
  ['astro', 'i-material-icon-theme:astro'],
  ['css', 'i-material-icon-theme:css'],
  ['html', 'i-material-icon-theme:html'],
  ['js', 'i-material-icon-theme:javascript'],
  ['json', 'i-material-icon-theme:json'],
  ['md', 'i-material-icon-theme:markdown'],
  ['mdx', 'i-material-icon-theme:mdx'],
  ['mjs', 'i-material-icon-theme:javascript'],
  ['sh', 'i-material-icon-theme:console'],
  ['ts', 'i-material-icon-theme:typescript'],
  ['yaml', 'i-material-icon-theme:yaml'],
  ['yml', 'i-material-icon-theme:yaml'],
]);

const fileExtension = (title) => {
  if (!title) return undefined;
  const cleanTitle = title.split('/').pop()?.toLowerCase();
  const parts = cleanTitle?.split('.');
  return parts && parts.length > 1 ? parts.at(-1) : undefined;
};

const resolveIconClass = (title, language) => {
  const extension = fileExtension(title);
  if (extension && extensionIcons.has(extension)) {
    return extensionIcons.get(extension);
  }
  if (language && languageIcons.has(language)) {
    return languageIcons.get(language);
  }
  return 'i-material-icon-theme:document';
};

const fallbackSvg = element(
  'svg',
  {
    viewBox: '0 0 16 16',
    width: '1em',
    height: '1em',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': '1.6',
    'aria-hidden': 'true',
  },
  [
    element('path', { d: 'M4.5 2.5h4.2L12 5.8v7.7H4.5z' }),
    element('path', { d: 'M8.7 2.5v3.3H12' }),
  ],
);

export function starlightCodeblockIcons() {
  return {
    name: 'Starlight Codeblock Icons',
    hooks: {
      postprocessRenderedBlock(context) {
        const { codeBlock, renderData } = context;
        if (!codeBlock.props.title) return;

        const ast = renderData?.blockAst;
        if (!ast || !('children' in ast)) return;

        const figcaption = ast.children.find(
          (child) => child.type === 'element' && child.tagName === 'figcaption',
        );
        const titleSpan = figcaption?.children?.find(
          (child) =>
            child.type === 'element' &&
            child.tagName === 'span' &&
            child.properties?.className?.includes('title'),
        );
        if (!titleSpan) return;

        const iconClass = resolveIconClass(codeBlock.props.title, codeBlock.language);
        titleSpan.children ??= [];
        titleSpan.children.unshift(
          element(
            'span',
            {
              className: [iconClass, 'code-block-icon'],
              'data-icon': iconClass,
              'data-language': codeBlock.language,
              'aria-hidden': 'true',
            },
            [fallbackSvg],
          ),
        );
      },
    },
  };
}
