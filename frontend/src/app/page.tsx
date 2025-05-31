'use client'

import { useState } from 'react'
import { Search, Settings, FileText, Scale, BookOpen, Zap } from 'lucide-react'
import SearchForm from '../components/SearchForm'
import ResponseDisplay from '../components/ResponseDisplay'
import ConfigPanel from '../components/ConfigPanel'
import { SearchConfig, SearchResponse, Document, StreamEvent } from '../types'

const defaultConfig: SearchConfig = {
  apiUrl: process.env.NEXT_PUBLIC_RAG_API_URL || 'http://localhost:8000',
  limit: parseInt(process.env.NEXT_PUBLIC_DEFAULT_LIMIT || '5'),
  temperature: parseFloat(process.env.NEXT_PUBLIC_DEFAULT_TEMPERATURE || '0.5'),
  maxTokens: parseInt(process.env.NEXT_PUBLIC_DEFAULT_MAX_TOKENS || '4096'),
  useStreaming: true, // Ativado por padrão
}

export default function HomePage() {
  const [config, setConfig] = useState<SearchConfig>(defaultConfig)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  
  // Estados para streaming
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [sourceDocuments, setSourceDocuments] = useState<Document[]>([])

  const handleSearch = async (query: string) => {
    if (!query.trim()) return

    // Limpa estados anteriores
    setLoading(true)
    setError(null)
    setResponse(null)
    setStreaming(false)
    setStreamingText('')
    setSourceDocuments([])

    try {
      if (config.useStreaming) {
        // Modo streaming
        setStreaming(true)
        await handleStreamingSearch(query)
      } else {
        // Modo tradicional
        await handleTraditionalSearch(query)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido'
      setError(errorMessage)
      setResponse(null)
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  const handleTraditionalSearch = async (query: string) => {
    const res = await fetch(`${config.apiUrl}/openai`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        limit: config.limit,
        temperature: config.temperature,
        max_output_tokens: config.maxTokens,
      }),
    })

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.detail || `Erro ${res.status}: ${res.statusText}`)
    }

    const data: SearchResponse = await res.json()
    setResponse(data)
  }

  const handleStreamingSearch = async (query: string) => {
    const response = await fetch(`${config.apiUrl}/openai/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        limit: config.limit,
        temperature: config.temperature,
        max_output_tokens: config.maxTokens,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Erro ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('Resposta sem corpo')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let accumulatedText = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: StreamEvent = JSON.parse(line.slice(6))
              
              switch (data.type) {
                case 'source_documents':
                  setSourceDocuments(data.documents || [])
                  break
                  
                case 'text_delta':
                  accumulatedText += data.delta || ''
                  setStreamingText(accumulatedText)
                  break
                  
                case 'response.created':
                  console.log('Resposta iniciada:', data)
                  break
                  
                case 'stream_completed':
                  // Cria o objeto de resposta final
                  setResponse({
                    answer: accumulatedText,
                    source_documents: sourceDocuments
                  })
                  break
                  
                case 'error':
                case 'response.failed':
                  throw new Error(data.message || data.error || 'Erro no streaming')
              }
            } catch (parseError) {
              console.error('Erro ao processar evento:', parseError)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Scale className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">Consulta Jurídica</h1>
          </div>
          
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            Sistema de busca inteligente em documentos normativos e jurídicos.
          </p>

          {/* Indicador de modo streaming */}
          {config.useStreaming && (
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full mb-4">
              <Zap className="w-4 h-4" />
              <span>Modo streaming ativado</span>
            </div>
          )}
        </div>

        {/* Botão configurações */}
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-4 h-4" />
            Configurações
          </button>
        </div>

        {/* Config Panel */}
        {showConfig && (
          <div className="mb-6">
            <ConfigPanel config={config} onConfigChange={setConfig} />
          </div>
        )}

        {/* Search Form */}
        <SearchForm onSearch={handleSearch} loading={loading} />

        {/* Response */}
        <ResponseDisplay 
          response={response} 
          error={error} 
          loading={loading}
          streaming={streaming}
          streamingText={streamingText}
          sourceDocuments={sourceDocuments}
        />

        {/* Footer */}
        <div className="text-center mt-12 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Mentoria IA 2025 - RAG API
          </p>
        </div>
      </div>
    </div>
  )
}