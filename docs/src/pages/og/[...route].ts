import { getCollection } from 'astro:content';
import { OGImageRoute } from 'astro-og-canvas';

const docs = await getCollection('docs');

const pages = Object.fromEntries(
  docs.map(({ id, data }) => [id, { title: data.title, description: data.description || '' }])
);

export const { getStaticPaths, GET } = await OGImageRoute({
  param: 'route',
  pages,
  getImageOptions: (_path, page) => ({
    title: page.title,
    description: page.description,
    bgGradient: [[23, 13, 33]],
    border: {
      color: [139, 92, 246],
      width: 4,
      side: 'block-start',
    },
    font: {
      title: {
        size: 64,
        families: ['Geist Sans', 'sans-serif'],
        weight: 'Bold',
        color: [255, 255, 255],
      },
      description: {
        size: 28,
        families: ['Geist Sans', 'sans-serif'],
        color: [180, 180, 200],
      },
    },
    padding: 60,
  }),
});
