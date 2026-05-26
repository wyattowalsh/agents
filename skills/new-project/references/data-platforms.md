# Data Platforms

## SQLite

Use for local embedded transactional app state. Do not commit local database files by default.

## DuckDB

Use for embedded analytics, CSV/Parquet workflows, notebooks, and local data exploration.

## Supabase

Use local Supabase for Postgres/auth/storage/RLS workflows. Default to `supabase init` and `supabase start` only after approval. Never expose service-role keys. Generate `.env.example` placeholders only.

## Kaggle And Colab

Generate notebook and metadata templates only. Never copy `~/.kaggle/kaggle.json` into a project. Publishing kernels/datasets is an external side effect.
