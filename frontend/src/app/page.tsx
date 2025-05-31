'use client'

import { useState } from 'react'
import { Search, Settings, FileText, Scale, BookOpen } from 'lucide-react'
import SearchForm from '../components/SearchForm'
import ResponseDisplay from '../components/ResponseDisplay'
import ConfigPanel from '../components/ConfigPanel'
import { SearchConfig, SearchResponse } from '../types'

const defaultConfig: SearchConfig = {
  apiUrl: process.env.NEXT_PUBLIC_RAG_API_URL || 'http://localhost:8000',
  limit: parseInt(process.env.NEXT_PUBLIC_DEFAULT_LIMIT || '5'),
  temperature: parseFloat(process.env.NEXT_PUBLIC_DEFAULT_TEMPERATURE || '0.5'),
  maxTokens: parseInt(process.env.NEXT_PUBLIC_DEFAULT_MAX_TOKENS || '4096'),
}

export default function HomePage() {
  const [config, setConfig] = useState<SearchConfig>(defaultConfig)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)

  const handleSearch = async (query: string) => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
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
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido'
      setError(errorMessage)
      setResponse(null)
    } finally {
      setLoading(false)
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
