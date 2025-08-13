#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as net from "net";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

interface PortAllocation {
  port: number;
  service: string;
  pid?: number;
  startTime?: string;
  status: "active" | "reserved" | "available";
}

class PortGuardian {
  private allocations: Map<number, PortAllocation> = new Map();
  private readonly RESERVED_PORTS = new Map([
    [5432, "postgresql"],
    [6379, "redis"],
    [8086, "influxdb"],
    [9090, "prometheus"],
    [3000, "grafana"],
    [8080, "cluster-websocket"],
    [8090, "analytics-dashboard"],
    [8000, "api-gateway"],
  ]);

  constructor() {
    this.initializeReservedPorts();
  }

  private initializeReservedPorts() {
    for (const [port, service] of this.RESERVED_PORTS) {
      this.allocations.set(port, {
        port,
        service,
        status: "reserved"
      });
    }
  }

  async checkPort(port: number): Promise<boolean> {
    return new Promise((resolve) => {
      const server = net.createServer();
      
      server.once("error", (err: any) => {
        if (err.code === "EADDRINUSE") {
          resolve(false);
        } else {
          resolve(true);
        }
      });
      
      server.once("listening", () => {
        server.close();
        resolve(true);
      });
      
      server.listen(port, "0.0.0.0");
    });
  }

  async getProcessUsingPort(port: number): Promise<string | null> {
    try {
      const { stdout } = await execAsync(`lsof -i :${port} -t 2>/dev/null || true`);
      const pid = stdout.trim();
      if (pid) {
        const { stdout: cmdOutput } = await execAsync(`ps -p ${pid} -o comm= 2>/dev/null || echo "unknown"`);
        return `PID ${pid}: ${cmdOutput.trim()}`;
      }
    } catch {
      // Fallback for Windows or if lsof isn't available
      try {
        const { stdout } = await execAsync(`netstat -anp tcp 2>/dev/null | grep :${port} || true`);
        if (stdout.trim()) {
          return "Port in use (details unavailable)";
        }
      } catch {}
    }
    return null;
  }

  async claimPort(port: number, service: string): Promise<{ success: boolean; message: string }> {
    // Check if port is reserved for another service
    const allocation = this.allocations.get(port);
    if (allocation && allocation.service !== service) {
      return {
        success: false,
        message: `Port ${port} is reserved for ${allocation.service}. Use port ${this.suggestAlternativePort(service)} instead.`
      };
    }

    // Check if port is actually available
    const isAvailable = await this.checkPort(port);
    if (!isAvailable) {
      const process = await this.getProcessUsingPort(port);
      return {
        success: false,
        message: `Port ${port} is already in use by: ${process || "unknown process"}`
      };
    }

    // Claim the port
    this.allocations.set(port, {
      port,
      service,
      startTime: new Date().toISOString(),
      status: "active"
    });

    return {
      success: true,
      message: `Port ${port} successfully claimed for ${service}`
    };
  }

  private suggestAlternativePort(service: string): number {
    // Suggest ports based on service type
    if (service.includes("web") || service.includes("dashboard")) {
      return this.findAvailablePort(8090, 8099);
    }
    if (service.includes("api")) {
      return this.findAvailablePort(8000, 8099);
    }
    if (service.includes("mcp")) {
      return this.findAvailablePort(8100, 8199);
    }
    return this.findAvailablePort(8200, 8999);
  }

  private findAvailablePort(start: number, end: number): number {
    for (let port = start; port <= end; port++) {
      if (!this.allocations.has(port)) {
        return port;
      }
    }
    return start;
  }

  async releasePort(port: number): Promise<{ success: boolean; message: string }> {
    const allocation = this.allocations.get(port);
    if (!allocation) {
      return {
        success: false,
        message: `Port ${port} is not registered`
      };
    }

    if (this.RESERVED_PORTS.has(port)) {
      return {
        success: false,
        message: `Port ${port} is a reserved system port and cannot be released`
      };
    }

    this.allocations.delete(port);
    return {
      success: true,
      message: `Port ${port} released successfully`
    };
  }

  async validateService(service: string, requestedPort?: number): Promise<{ valid: boolean; port: number; message: string }> {
    // If a specific port is requested
    if (requestedPort) {
      const allocation = this.allocations.get(requestedPort);
      
      // Check if it's the right service for this port
      if (allocation && allocation.service !== service) {
        const suggestedPort = this.suggestAlternativePort(service);
        return {
          valid: false,
          port: suggestedPort,
          message: `Port ${requestedPort} is reserved for ${allocation.service}. Suggested port: ${suggestedPort}`
        };
      }

      // Check if port is available
      const isAvailable = await this.checkPort(requestedPort);
      if (!isAvailable) {
        const process = await this.getProcessUsingPort(requestedPort);
        const suggestedPort = this.suggestAlternativePort(service);
        return {
          valid: false,
          port: suggestedPort,
          message: `Port ${requestedPort} is in use by ${process}. Suggested port: ${suggestedPort}`
        };
      }

      return {
        valid: true,
        port: requestedPort,
        message: `Port ${requestedPort} is available for ${service}`
      };
    }

    // Auto-assign port based on service
    const suggestedPort = this.suggestAlternativePort(service);
    return {
      valid: true,
      port: suggestedPort,
      message: `Suggested port ${suggestedPort} for ${service}`
    };
  }

  getStatus(): any {
    const status = {
      reserved: [] as any[],
      active: [] as any[],
      available_ranges: [
        { start: 8091, end: 8099, purpose: "Web services" },
        { start: 8100, end: 8199, purpose: "MCP servers" },
        { start: 8200, end: 8299, purpose: "Analytics services" },
        { start: 8300, end: 8399, purpose: "Development tools" },
        { start: 8400, end: 8999, purpose: "General services" }
      ]
    };

    for (const [port, allocation] of this.allocations) {
      if (allocation.status === "reserved") {
        status.reserved.push({ port, service: allocation.service });
      } else if (allocation.status === "active") {
        status.active.push(allocation);
      }
    }

    return status;
  }
}

const guardian = new PortGuardian();
const server = new Server(
  {
    name: "port-guardian",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "check_port",
      description: "Check if a port is available for use",
      inputSchema: {
        type: "object",
        properties: {
          port: { type: "number", description: "Port number to check" },
        },
        required: ["port"],
      },
    },
    {
      name: "claim_port",
      description: "Claim a port for a service (prevents conflicts)",
      inputSchema: {
        type: "object",
        properties: {
          port: { type: "number", description: "Port number to claim" },
          service: { type: "string", description: "Service name claiming the port" },
        },
        required: ["port", "service"],
      },
    },
    {
      name: "release_port",
      description: "Release a previously claimed port",
      inputSchema: {
        type: "object",
        properties: {
          port: { type: "number", description: "Port number to release" },
        },
        required: ["port"],
      },
    },
    {
      name: "validate_service",
      description: "Validate and get the correct port for a service",
      inputSchema: {
        type: "object",
        properties: {
          service: { type: "string", description: "Service name" },
          requestedPort: { type: "number", description: "Optional requested port" },
        },
        required: ["service"],
      },
    },
    {
      name: "get_port_status",
      description: "Get current port allocation status",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (!args) {
    throw new Error("Missing arguments");
  }

  try {
    switch (name) {
      case "check_port": {
        const port = args.port as number;
        const isAvailable = await guardian.checkPort(port);
        const process = !isAvailable ? await guardian.getProcessUsingPort(port) : null;
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                port,
                available: isAvailable,
                inUseBy: process,
              }, null, 2),
            },
          ],
        };
      }

      case "claim_port": {
        const port = args.port as number;
        const service = args.service as string;
        const result = await guardian.claimPort(port, service);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "release_port": {
        const port = args.port as number;
        const result = await guardian.releasePort(port);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "validate_service": {
        const service = args.service as string;
        const requestedPort = args.requestedPort as number | undefined;
        const result = await guardian.validateService(service, requestedPort);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "get_port_status": {
        const status = guardian.getStatus();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(status, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Port Guardian MCP server running");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});