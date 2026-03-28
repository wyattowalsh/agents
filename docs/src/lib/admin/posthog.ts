import { getPostHogApiHost, getPostHogApiKey, getPostHogProjectId, isPostHogQueryConfigured } from './config';
import { captureServerEvent, logStructured } from './telemetry';

export type AdminEventRow = {
  distinctId: string;
  event: string;
  outcome: string;
  path: string;
  requestId: string;
  summary: string;
  timestamp: string;
};

export type DashboardData = {
  adminLogins: number;
  authFailures: number;
  queryStatus: 'error' | 'missing' | 'ready';
  recentAdminEvents: AdminEventRow[];
  recentErrors: AdminEventRow[];
  topPages: Array<{ path: string; views: number }>;
  totalPageviews: number;
  uniqueVisitors: number;
};

function quoteSqlString(value: string): string {
  return `'${value.replaceAll('\\', '\\\\').replaceAll("'", "\\'")}'`;
}

function toRowObjects(payload: unknown): Array<Record<string, unknown>> {
  if (!payload || typeof payload !== 'object') return [];

  const root = payload as {
    columns?: unknown;
    results?: unknown;
  };

  if (Array.isArray(root.results) && root.results.every((row) => typeof row === 'object' && row !== null && !Array.isArray(row))) {
    return root.results as Array<Record<string, unknown>>;
  }

  if (Array.isArray(root.columns) && Array.isArray(root.results)) {
    return root.results.map((row) => {
      if (!Array.isArray(row)) return {};
      return Object.fromEntries(root.columns!.map((column, index) => [String(column), row[index]]));
    });
  }

  if (typeof root.results === 'object' && root.results !== null) {
    const nested = root.results as {
      columns?: unknown;
      results?: unknown;
    };

    if (Array.isArray(nested.results) && nested.results.every((row) => typeof row === 'object' && row !== null && !Array.isArray(row))) {
      return nested.results as Array<Record<string, unknown>>;
    }

    if (Array.isArray(nested.columns) && Array.isArray(nested.results)) {
      return nested.results.map((row) => {
        if (!Array.isArray(row)) return {};
        return Object.fromEntries(nested.columns!.map((column, index) => [String(column), row[index]]));
      });
    }
  }

  return [];
}

async function runHogQlQuery<T extends Record<string, unknown>>(
  query: string,
  requestId: string
): Promise<T[]> {
  if (!isPostHogQueryConfigured()) return [];

  const apiKey = getPostHogApiKey();
  const projectId = getPostHogProjectId();
  const queryUrl = new URL(`/api/projects/${projectId}/query/`, getPostHogApiHost());

  try {
    const response = await fetch(queryUrl, {
      body: JSON.stringify({
        query: {
          kind: 'HogQLQuery',
          query,
        },
      }),
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'content-type': 'application/json',
      },
      method: 'POST',
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`PostHog query failed with ${response.status}: ${body.slice(0, 280)}`);
    }

    const payload = (await response.json()) as unknown;
    return toRowObjects(payload) as T[];
  } catch (error) {
    logStructured('error', 'PostHog query failed', {
      error: error instanceof Error ? error.message : 'Unknown PostHog query failure',
      request_id: requestId,
    });
    await captureServerEvent(
      'admin_posthog_query_failed',
      {
        message: error instanceof Error ? error.message : 'Unknown PostHog query failure',
        outcome: 'query_error',
        request_id: requestId,
        route: 'posthog_query',
      },
      { distinctId: 'admin:query-client' }
    );
    throw error;
  }
}

async function queryScalar(query: string, column: string, requestId: string): Promise<number> {
  const rows = await runHogQlQuery<Record<string, unknown>>(query, requestId);
  const value = Number(rows[0]?.[column] ?? 0);
  return Number.isFinite(value) ? value : 0;
}

function normalizeEventRow(row: Record<string, unknown>): AdminEventRow {
  return {
    distinctId: String(row.distinct_id ?? row.distinctId ?? ''),
    event: String(row.event ?? ''),
    outcome: String(row.outcome ?? ''),
    path: String(row.path ?? ''),
    requestId: String(row.request_id ?? row.requestId ?? ''),
    summary: String(row.summary ?? ''),
    timestamp: String(row.timestamp ?? ''),
  };
}

export async function getDashboardData(requestId: string): Promise<DashboardData> {
  if (!isPostHogQueryConfigured()) {
    return {
      adminLogins: 0,
      authFailures: 0,
      queryStatus: 'missing',
      recentAdminEvents: [],
      recentErrors: [],
      topPages: [],
      totalPageviews: 0,
      uniqueVisitors: 0,
    };
  }

  try {
    const [totalPageviews, uniqueVisitors, adminLogins, authFailures, topPagesRaw, recentAdminRaw, recentErrorRaw] =
      await Promise.all([
        queryScalar(
          "SELECT count() AS value FROM events WHERE event = 'docs_pageview' AND timestamp >= now() - INTERVAL 7 DAY",
          'value',
          requestId
        ),
        queryScalar(
          "SELECT uniq(distinct_id) AS value FROM events WHERE event = 'docs_pageview' AND timestamp >= now() - INTERVAL 7 DAY",
          'value',
          requestId
        ),
        queryScalar(
          "SELECT count() AS value FROM events WHERE event = 'admin_login_succeeded' AND timestamp >= now() - INTERVAL 7 DAY",
          'value',
          requestId
        ),
        queryScalar(
          "SELECT count() AS value FROM events WHERE event = 'admin_login_failed' AND timestamp >= now() - INTERVAL 7 DAY",
          'value',
          requestId
        ),
        runHogQlQuery<Record<string, unknown>>(
          [
            'SELECT',
            "  coalesce(properties.$pathname, properties.path, properties.route, properties.$current_url, 'unknown') AS path,",
            '  count() AS views',
            'FROM events',
            "WHERE event = 'docs_pageview' AND timestamp >= now() - INTERVAL 7 DAY",
            'GROUP BY path',
            'ORDER BY views DESC',
            'LIMIT 8',
          ].join(' '),
          requestId
        ),
        runHogQlQuery<Record<string, unknown>>(
          [
            'SELECT',
            '  timestamp,',
            '  event,',
            '  distinct_id,',
            "  coalesce(properties.route, properties.path, properties.$pathname, '') AS path,",
            "  coalesce(properties.outcome, '') AS outcome,",
            "  coalesce(properties.request_id, '') AS request_id,",
            "  coalesce(properties.reason, properties.message, '') AS summary",
            'FROM events',
            "WHERE event LIKE 'admin_%'",
            'ORDER BY timestamp DESC',
            'LIMIT 20',
          ].join(' '),
          requestId
        ),
        runHogQlQuery<Record<string, unknown>>(
          [
            'SELECT',
            '  timestamp,',
            '  event,',
            '  distinct_id,',
            "  coalesce(properties.route, properties.path, properties.$pathname, '') AS path,",
            "  coalesce(properties.outcome, '') AS outcome,",
            "  coalesce(properties.request_id, '') AS request_id,",
            "  coalesce(properties.message, properties.reason, '') AS summary",
            'FROM events',
            "WHERE event IN ('docs_client_error', 'docs_client_promise_rejection', 'admin_posthog_query_failed', 'admin_server_error')",
            'ORDER BY timestamp DESC',
            'LIMIT 20',
          ].join(' '),
          requestId
        ),
      ]);

    return {
      adminLogins,
      authFailures,
      queryStatus: 'ready',
      recentAdminEvents: recentAdminRaw.map(normalizeEventRow),
      recentErrors: recentErrorRaw.map(normalizeEventRow),
      topPages: topPagesRaw.map((row) => ({
        path: String(row.path ?? 'unknown'),
        views: Number(row.views ?? 0),
      })),
      totalPageviews,
      uniqueVisitors,
    };
  } catch {
    return {
      adminLogins: 0,
      authFailures: 0,
      queryStatus: 'error',
      recentAdminEvents: [],
      recentErrors: [],
      topPages: [],
      totalPageviews: 0,
      uniqueVisitors: 0,
    };
  }
}

export async function getEventExplorerData(
  filter: string | null,
  limit: number,
  requestId: string
): Promise<{ queryStatus: 'error' | 'missing' | 'ready'; rows: AdminEventRow[] }> {
  if (!isPostHogQueryConfigured()) return { queryStatus: 'missing', rows: [] };

  const safeLimit = Math.max(10, Math.min(limit, 100));
  const safeFilter = filter && /^[a-z0-9_:$-]{1,64}$/i.test(filter) ? filter : null;
  const whereClause = safeFilter ? `WHERE event = ${quoteSqlString(safeFilter)}` : '';

  try {
    const rows = await runHogQlQuery<Record<string, unknown>>(
      [
        'SELECT',
        '  timestamp,',
        '  event,',
        '  distinct_id,',
        "  coalesce(properties.route, properties.path, properties.$pathname, properties.$current_url, '') AS path,",
        "  coalesce(properties.outcome, '') AS outcome,",
        "  coalesce(properties.request_id, '') AS request_id,",
        "  coalesce(properties.label, properties.reason, properties.message, '') AS summary",
        'FROM events',
        whereClause,
        'ORDER BY timestamp DESC',
        `LIMIT ${safeLimit}`,
      ]
        .filter(Boolean)
        .join(' '),
      requestId
    );

    return {
      queryStatus: 'ready',
      rows: rows.map(normalizeEventRow),
    };
  } catch {
    return { queryStatus: 'error', rows: [] };
  }
}

export async function getRecentSecurityEvents(
  requestId: string
): Promise<{ queryStatus: 'error' | 'missing' | 'ready'; rows: AdminEventRow[] }> {
  if (!isPostHogQueryConfigured()) return { queryStatus: 'missing', rows: [] };

  try {
    const rows = await runHogQlQuery<Record<string, unknown>>(
      [
        'SELECT',
        '  timestamp,',
        '  event,',
        '  distinct_id,',
        "  coalesce(properties.route, properties.path, '') AS path,",
        "  coalesce(properties.outcome, '') AS outcome,",
        "  coalesce(properties.request_id, '') AS request_id,",
        "  coalesce(properties.reason, properties.message, '') AS summary",
        'FROM events',
        "WHERE event IN ('admin_login_succeeded', 'admin_login_failed', 'admin_logout_succeeded', 'admin_flag_overrides_saved')",
        'ORDER BY timestamp DESC',
        'LIMIT 30',
      ].join(' '),
      requestId
    );

    return {
      queryStatus: 'ready',
      rows: rows.map(normalizeEventRow),
    };
  } catch {
    return { queryStatus: 'error', rows: [] };
  }
}