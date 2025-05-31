'use client'

import { useState, FormEvent } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchFormProps {
  onSearch: (query: string) => void
  loading: boolean
}

export default function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim() && !loading) {
      onSearch(query)
    }
  }

  const exampleQueries = [
    "Quais são as penalidades para profissionais de engenharia?",
    "Como funciona a transferência de funcionários públicos?",
    "Quais são os requisitos para exercer arquitetura?",
  ]

  return (
    <div className="mb-6">
      {/* Form */}
      <div className="card relative">
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Faça sua consulta... Exemplo: 'Quais são as penalidades previstas?' ou 'Como funciona a licença profissional?'"
              className="w-full p-4 border-2 border-gray-200 rounded-xl resize-none h-24 text-base focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            
            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="absolute bottom-3 right-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg font-medium transition-all hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              {loading ? 'Consultando...' : 'Consultar'}
            </button>
          </div>
        </form>
      </div>

      {/* Examples */}
      <div className="mt-4">
        <p className="text-sm text-gray-600 mb-3">💡 Experimente estas consultas:</p>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => !loading && setQuery(example)}
              disabled={loading}
              className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
