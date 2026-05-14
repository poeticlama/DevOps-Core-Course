import { Request as CloudflareRequest, KVNamespace } from "@cloudflare/workers-types";

export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: CloudflareRequest, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;

    // Log incoming request
    console.log(
      `${method} ${url.pathname} from ${request.cf?.country} (colo: ${request.cf?.colo})`
    );

    // Health check endpoint
    if (url.pathname === "/health") {
      console.log("Health check requested");
      return Response.json(
        {
          status: "ok",
          timestamp: new Date().toISOString(),
          app: env.APP_NAME,
        },
        { status: 200 }
      );
    }

    // Root endpoint - general app information
    if (url.pathname === "/") {
      console.log("Root endpoint requested");
      return Response.json(
        {
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          message: "Hello from Cloudflare Workers",
          timestamp: new Date().toISOString(),
          version: "1.0.0",
        },
        { status: 200 }
      );
    }

    // Edge metadata endpoint
    if (url.pathname === "/edge") {
      console.log("Edge metadata requested");
      return Response.json(
        {
          colo: request.cf?.colo,
          country: request.cf?.country,
          city: request.cf?.city,
          asn: request.cf?.asn,
          httpProtocol: request.cf?.httpProtocol,
          tlsVersion: request.cf?.tlsVersion,
          continent: request.cf?.continent,
          postalCode: request.cf?.postalCode,
          timezone: request.cf?.timezone,
          latitude: request.cf?.latitude,
          longitude: request.cf?.longitude,
        },
        { status: 200 }
      );
    }

    // Counter endpoint - KV-backed persistent counter
    if (url.pathname === "/counter") {
      if (method === "GET") {
        const raw = await env.SETTINGS.get("visits");
        const visits = Number(raw ?? "0") + 1;
        await env.SETTINGS.put("visits", String(visits));
        console.log(`Counter incremented to ${visits}`);
        return Response.json({ visits }, { status: 200 });
      }

      if (method === "POST") {
        await env.SETTINGS.put("visits", "0");
        console.log("Counter reset");
        return Response.json({ visits: 0, message: "Counter reset" }, { status: 200 });
      }
    }

    // Info endpoint - deployment and environment info
    if (url.pathname === "/info") {
      console.log("Info endpoint requested");
      return Response.json(
        {
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          deployment: {
            platform: "Cloudflare Workers",
            timestamp: new Date().toISOString(),
            apiTokenSet: !!env.API_TOKEN,
            adminEmailSet: !!env.ADMIN_EMAIL,
          },
          request: {
            method: request.method,
            url: request.url,
            country: request.cf?.country,
            colo: request.cf?.colo,
          },
        },
        { status: 200 }
      );
    }

    // 404 Not Found
    console.log(`404 Not Found: ${url.pathname}`);
    return Response.json(
      {
        error: "Not Found",
        message: `Route ${url.pathname} does not exist`,
        availableRoutes: ["/", "/health", "/edge", "/counter", "/info"],
      },
      { status: 404 }
    );
  },
};

