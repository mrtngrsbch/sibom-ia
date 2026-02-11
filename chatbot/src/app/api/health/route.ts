/**
 * API Route para health check
 */
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ status: 'healthy', service: 'chatbot' });
}
