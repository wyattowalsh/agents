'use strict';

const http = require('node:http');
const path = require('node:path');

const entrypoint = process.argv[1] || '';
const isMcpHubEntrypoint =
  path.basename(entrypoint) === 'mcphub' ||
  (entrypoint.endsWith('/bin/cli.js') && entrypoint.includes('@samanhappy/mcphub'));
const forceForTest = process.env.MCPHUB_BIND_SHIM_FORCE === '1';

if (isMcpHubEntrypoint || forceForTest) {
  const allowedHosts = new Set(['127.0.0.1', '::1', 'localhost']);
  const bindHost = process.env.MCPHUB_BIND_HOST || '127.0.0.1';
  const rawPort = process.env.PORT || '46683';
  const bindPort = Number(rawPort);

  if (!allowedHosts.has(bindHost)) {
    throw new Error(`MCPHUB_BIND_HOST must be loopback-only, got ${bindHost}`);
  }
  if (!Number.isInteger(bindPort) || bindPort < 0 || bindPort > 65535) {
    throw new Error(`PORT must be an integer from 0 through 65535, got ${rawPort}`);
  }

  const parentNodeOptions = process.env.MCPHUB_PARENT_NODE_OPTIONS;
  if (parentNodeOptions) {
    process.env.NODE_OPTIONS = parentNodeOptions;
  } else {
    delete process.env.NODE_OPTIONS;
  }
  delete process.env.MCPHUB_PARENT_NODE_OPTIONS;
  delete process.env.MCPHUB_BIND_SHIM_FORCE;

  const originalListen = http.Server.prototype.listen;
  http.Server.prototype.listen = function loopbackListen(...args) {
    const first = args[0];
    const requestedPort =
      typeof first === 'object' && first !== null
        ? Number(first.port)
        : Number(first);

    if (requestedPort !== bindPort) {
      return originalListen.apply(this, args);
    }

    if (typeof first === 'object' && first !== null) {
      const requestedHost = first.host;
      if (requestedHost && !allowedHosts.has(requestedHost)) {
        throw new Error(`MCPHub refused non-loopback listen host ${requestedHost}`);
      }
      args[0] = { ...first, host: requestedHost || bindHost };
    } else if (typeof args[1] === 'string') {
      if (!allowedHosts.has(args[1])) {
        throw new Error(`MCPHub refused non-loopback listen host ${args[1]}`);
      }
    } else {
      args.splice(1, 0, bindHost);
    }

    return originalListen.apply(this, args);
  };
}
