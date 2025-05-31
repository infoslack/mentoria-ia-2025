'use client'

import { Settings, Zap } from 'lucide-react'
import { SearchConfig } from '@/types'

interface ConfigPanelProps {
  config: SearchConfig
  onConfigChange: (config: SearchConfig) => void
}

export default function ConfigPanel({ config, onConfigChange }: ConfigPanelProps) {
  const handleChange = (key: keyof SearchConfig, value: string | number | boolean) => {
    onConfigChange({
      ...config,
      [key]: value
    })
  }

  return (
    <div className="card bg-gradient-to-r from-gray-50 to-gray-100">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
          <Settings className="w-4 h-4 text-gray-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-800">
          Configurações da API
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Modo Streaming */}
        <div className="md:col-span-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={config.useStreaming || false}
              onChange={(e) => handleChange('useStreaming', e.target.checked)}
              className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">
                Modo Streaming
              </span>
              <span className="text-xs text-gray-500">
                (Respostas em tempo real)
              </span>
            </div>
          </label>
          <p className="text-xs text-gray-500 mt-2 ml-8">
            Quando ativado, você verá a resposta sendo gerada em tempo real, com um efeito de digitação.
          </p>
        </div>

        {/* API URL */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            URL da API
          </label>
          <input
            type="url"
            value={config.apiUrl}
            onChange={(e) => handleChange('apiUrl', e.target.value)}
            className="input-field"
            placeholder="http://localhost:8000"
          />
          <p className="text-xs text-gray-500 mt-1">
            Endereço completo da sua API RAG
          </p>
        </div>

        {/* Limit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Limite de Documentos
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={config.limit || ''}
            onChange={(e) => handleChange('limit', parseInt(e.target.value))}
            className="input-field"
          />
          <p className="text-xs text-gray-500 mt-1">
            Número máximo de documentos a consultar (1-20)
          </p>
        </div>

        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Temperatura
          </label>
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={config.temperature?.toString() || ''}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            className="input-field"
          />
          <p className="text-xs text-gray-500 mt-1">
            Criatividade das respostas (0.0 - 2.0)
          </p>
        </div>

        {/* Max Tokens */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Máximo de Tokens
          </label>
          <input
            type="number"
            min="100"
            max="8192"
            step="100"
            value={config.maxTokens.toString() || ''}
            onChange={(e) => handleChange('maxTokens', parseInt(e.target.value))}
            className="input-field"
          />
          <p className="text-xs text-gray-500 mt-1">
            Tamanho máximo da resposta em tokens (100-8192)
          </p>
        </div>
      </div>

      {/* Reset Button */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={() => onConfigChange({
            apiUrl: process.env.NEXT_PUBLIC_RAG_API_URL || 'http://localhost:8000',
            limit: parseInt(process.env.NEXT_PUBLIC_DEFAULT_LIMIT || '5'),
            temperature: parseFloat(process.env.NEXT_PUBLIC_DEFAULT_TEMPERATURE || '0.5'),
            maxTokens: parseInt(process.env.NEXT_PUBLIC_DEFAULT_MAX_TOKENS || '4096'),
            useStreaming: true
          })}
          className="text-sm text-gray-600 hover:text-gray-800 underline"
        >
          Restaurar padrões
        </button>
      </div>
    </div>
  )
}