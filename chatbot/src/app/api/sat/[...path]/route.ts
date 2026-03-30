import type { NextRequest } from "next/server";

const SAT_API_INTERNAL_URL =
	process.env.SAT_API_URL ||
	process.env.NEXT_PUBLIC_SAT_API_URL ||
	"http://127.0.0.1:8001";

export const dynamic = "force-dynamic";

function buildTargetUrl(pathSegments: string[], request: NextRequest): string {
	const normalizedPath = pathSegments.join("/");
	const search = request.nextUrl.search;

	return `${SAT_API_INTERNAL_URL}/${normalizedPath}${search}`;
}

async function proxyRequest(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	const { path } = await context.params;
	const targetUrl = buildTargetUrl(path, request);

	const headers = new Headers(request.headers);
	headers.delete("host");
	headers.set("ngrok-skip-browser-warning", "1");

	try {
		const upstreamResponse = await fetch(targetUrl, {
			method: request.method,
			headers,
			body:
				request.method === "GET" || request.method === "HEAD"
					? undefined
					: await request.text(),
			cache: "no-store",
		});

		const responseHeaders = new Headers(upstreamResponse.headers);
		responseHeaders.delete("content-encoding");
		responseHeaders.delete("content-length");
		responseHeaders.delete("transfer-encoding");

		return new Response(upstreamResponse.body, {
			status: upstreamResponse.status,
			statusText: upstreamResponse.statusText,
			headers: responseHeaders,
		});
	} catch {
		return new Response(
			JSON.stringify({
				detail: "Servicio de análisis satelital no disponible",
			}),
			{
				status: 503,
				statusText: "Service Unavailable",
				headers: { "Content-Type": "application/json" },
			},
		);
	}
}

export async function GET(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	return proxyRequest(request, context);
}

export async function POST(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	return proxyRequest(request, context);
}

export async function PUT(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	return proxyRequest(request, context);
}

export async function PATCH(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	return proxyRequest(request, context);
}

export async function DELETE(
	request: NextRequest,
	context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
	return proxyRequest(request, context);
}
