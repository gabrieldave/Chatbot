import { NextResponse } from 'next/server'

export const runtime = 'nodejs'

// GET: Obtener mensajes de una conversación específica
export async function GET(
  req: Request,
  { params }: { params: Promise<{ conversationId: string }> }
) {
  try {
    const authHeader = req.headers.get('Authorization') || ''
    const authToken = authHeader.replace('Bearer ', '').trim()
    
    if (!authToken) {
      return NextResponse.json({ error: "No se proporcionó token de autenticación" }, { status: 401 })
    }

    const { searchParams } = new URL(req.url)
    const limit = parseInt(searchParams.get('limit') || '100')
    const { conversationId } = await params

    const backendBaseUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const backendUrl = `${backendBaseUrl}/chat-sessions/${conversationId}/messages?limit=${limit}`
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json({ error: errorText }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Error desconocido' 
    }, { status: 500 })
  }
}

