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
    bgGradient: [
      [10, 15, 24],
      [11, 33, 43],
      [36, 24, 12],
    ],
    border: {
      color: [71, 201, 204],
      width: 4,
      side: 'block-start',
    },
    font: {
      title: {
        size: 64,
        families: ['Geist Sans', 'sans-serif'],
        weight: 'Bold',
        color: [238, 248, 249],
      },
      description: {
        size: 28,
        families: ['Geist Sans', 'sans-serif'],
        color: [176, 208, 214],
      },
    },
    padding: 60,
  }),
});
