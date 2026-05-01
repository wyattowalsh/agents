# LCP Breakdown

Largest Contentful Paint is composed of four sequential subparts.

| LCP subpart | Optimal share | Description |
| --- | --- | --- |
| Time to First Byte | about 40% | Navigation start to first HTML byte |
| Resource load delay | less than 10% | TTFB to LCP resource request start |
| Resource load duration | about 40% | LCP resource download time |
| Element render delay | less than 10% | Resource complete to element render |

Delay subparts should be near zero. If either delay dominates, optimize discovery, priority, rendering, or main-thread blocking before reducing bytes.
