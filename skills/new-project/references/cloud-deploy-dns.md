# Cloud, Deploy, And DNS

Cloud setup is planning-only by default.

| Provider       | Default stance                                                    |
| -------------- | ----------------------------------------------------------------- |
| Vercel         | local CLI/dev guidance; link/deploy requires approval             |
| Cloudflare DNS | IaC plan/checklist; DNS mutation requires zone/account approval   |
| AWS Bedrock    | profile/SSO/OIDC guidance; no static key generation               |
| AgentCore      | local/dev planning first; deploy is separate approval             |
| Supabase       | local development first; cloud project mutation requires approval |

Never ask users to paste tokens or credentials into chat.
