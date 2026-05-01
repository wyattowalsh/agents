# LCP Debugging Snippets

Use with `evaluate_script` after taking a trace.

## Identify LCP Element

```javascript
async () => {
  return await new Promise(resolve => {
    new PerformanceObserver(list => {
      const entries = list.getEntries();
      const last = entries[entries.length - 1];
      resolve({
        element: last.element?.tagName,
        id: last.element?.id,
        className: last.element?.className,
        url: last.url,
        startTime: last.startTime,
        renderTime: last.renderTime,
        loadTime: last.loadTime,
        size: last.size,
      });
    }).observe({type: 'largest-contentful-paint', buffered: true});
  });
};
```

## Audit Common Issues

```javascript
() => {
  const issues = [];

  document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    const rect = img.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      issues.push({
        issue: 'lazy-loaded image in viewport',
        element: img.outerHTML.substring(0, 200),
        fix: 'Remove loading="lazy" from initial viewport images that may be LCP',
      });
    }
  });

  document.querySelectorAll('img:not([fetchpriority])').forEach(img => {
    const rect = img.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.width * rect.height > 50000) {
      issues.push({
        issue: 'large viewport image without fetchpriority',
        element: img.outerHTML.substring(0, 200),
        fix: 'Add fetchpriority="high" if this is the LCP image',
      });
    }
  });

  document
    .querySelectorAll('head script:not([async]):not([defer]):not([type="module"])')
    .forEach(script => {
      if (script.src) {
        issues.push({
          issue: 'render-blocking script in head',
          element: script.outerHTML.substring(0, 200),
          fix: 'Add async/defer or move the script out of the critical path',
        });
      }
    });

  return {issueCount: issues.length, issues};
};
```
