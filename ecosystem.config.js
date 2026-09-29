/**
 * NeighborIQ PM2 process manager configuration.
 *
 * Start all:  pm2 start ecosystem.config.js
 * Stop all:   pm2 stop ecosystem.config.js
 * Status:     pm2 status
 * Logs:       pm2 logs neighboriq-api
 */
module.exports = {
  apps: [
    {
      name: "neighboriq-api",
      script: "python",
      args: "-m uvicorn neighboriq.api.server:app --host 0.0.0.0 --port 8000 --reload",
      cwd: "C:\\Sijoy_2.0\\automation",
      interpreter: "none",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: "C:\\Sijoy_2.0\\automation",
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      log_file: "C:\\Sijoy_2.0\\automation\\neighboriq\\data\\logs\\api.log",
      error_file: "C:\\Sijoy_2.0\\automation\\neighboriq\\data\\logs\\api.error.log",
      time: true,
    },
    {
      name: "neighboriq-mcp",
      script: "python",
      args: "-m neighboriq.mcp_server",
      cwd: "C:\\Sijoy_2.0\\automation",
      interpreter: "none",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: "C:\\Sijoy_2.0\\automation",
      },
      watch: false,
      autorestart: false,
      // MCP server runs on-demand via Claude Code; don't keep alive
      exec_mode: "fork",
    },
    {
      name: "neighboriq-content",
      script: "python",
      args: "-m neighboriq.content.pipeline --zip 02122 --top 3",
      cwd: "C:\\Sijoy_2.0\\automation",
      interpreter: "none",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: "C:\\Sijoy_2.0\\automation",
      },
      // Run on a cron — daily at 07:00 ET
      cron_restart: "0 7 * * *",
      watch: false,
      autorestart: false,
      log_file: "C:\\Sijoy_2.0\\automation\\neighboriq\\data\\logs\\content.log",
      error_file: "C:\\Sijoy_2.0\\automation\\neighboriq\\data\\logs\\content.error.log",
      time: true,
    },
  ],
};
