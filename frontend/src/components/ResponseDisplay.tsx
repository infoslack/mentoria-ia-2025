'use client'

import React, { JSX, useState, useEffect } from 'react'
import { Bot, FileText, AlertCircle, Search, Sparkles } from 'lucide-react'
import { SearchResponse, Document } from '../types'

interface ResponseDisplayProps {
  response: SearchResponse | null
  error: string | null
  loading: boolean
  streaming?: boolean
  streamingText?: string
  sourceDocuments?: Document[]
}

// Função para converter markdown simples em HTML
function formatMarkdown(text: string): JSX.Element[] {
  const lines = text.split('\n')
  const elements: JSX.Element[] = []
  
  let currentListItems: string[] = []
  let listKey = 0
  
  const flushList = () => {
    if (currentListItems.length > 0) {
      elements.push(
        <ul key={`list-${listKey++}`} className="list-disc list-inside space-y-2 mb-4 ml-4">
          {currentListItems.map((item, idx) => (
            <li key={idx} className="text-gray-700">
              <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(item) }} />
            </li>
          ))}
        </ul>
      )
      currentListItems = []
    }
  }
  
  lines.forEach((line, index) => {
    line = line.trim()
    
    if (!line) {
      flushList()
      elements.push(<div key={`space-${index}`} className="h-4" />)
      return
    }
    
    // Lista numerada (1. 2. 3.)
    const numberedMatch = line.match(/^(\d+)\.\s*(.+)/)
    if (numberedMatch) {
      flushList()
      const content = numberedMatch[2]
      elements.push(
        <div key={index} className="flex items-start gap-3 mb-3">
          <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-semibold">
            {numberedMatch[1]}
          </span>
          <p className="text-gray-700 flex-1" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(content) }} />
        </div>
      )
      return
    }
    
    // Lista com bullet (-)
    const bulletMatch = line.match(/^[-*]\s*(.+)/)
    if (bulletMatch) {
      currentListItems.push(bulletMatch[1])
      return
    }
    
    // Título/heading
    if (line.startsWith('##')) {
      flushList()
      elements.push(
        <h3 key={index} className="text-lg font-semibold text-gray-800 mb-3 mt-6">
          {line.replace(/^##\s*/, '')}
        </h3>
      )
      return
    }
    
    if (line.startsWith('#')) {
      flushList()
      elements.push(
        <h2 key={index} className="text-xl font-bold text-gray-800 mb-4 mt-6">
          {line.replace(/^#\s*/, '')}
        </h2>
      )
      return
    }
    
    // Parágrafo normal
    flushList()
    elements.push(
      <p key={index} className="text-gray-700 mb-3 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(line) }} />
    )
  })
  
  flushList() // Flush any remaining list items
  return elements
}

// Função para formatar markdown inline (negrito, itálico)
function formatInlineMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
}

// Componente para cursor piscante
function BlinkingCursor() {
  return (
    <span className="inline-block w-0.5 h-5 bg-blue-600 animate-pulse ml-1" />
  )
}

export default function ResponseDisplay({ 
  response, 
  error, 
  loading, 
  streaming = false,
  streamingText = '',
  sourceDocuments = []
}: ResponseDisplayProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Efeito de digitação suave para texto não-streaming
  useEffect(() => {
    if (response && !streaming && response.answer && !streamingText) {
      setDisplayedText('')
      setIsTyping(true)
      let currentIndex = 0
      const text = response.answer
      
      const typeWriter = () => {
        if (currentIndex < text.length) {
          setDisplayedText(text.substring(0, currentIndex + 1))
          currentIndex++
          setTimeout(typeWriter, 5) // Velocidade de digitação
        } else {
          setIsTyping(false)
        }
      }
      
      typeWriter()
    }
  }, [response, streaming, streamingText])

  // Para streaming, exibe o texto diretamente
  useEffect(() => {
    if (streaming && streamingText) {
      setDisplayedText(streamingText)
    }
  }, [streaming, streamingText])

  if (loading && !streaming) {
    return (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Bot className="w-5 h-5 animate-pulse text-blue-600" />
          <h3 className="text-lg font-semibold">Analisando documentos...</h3>
        </div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border-red-200 bg-red-50">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-red-800">Erro na consulta</h3>
        </div>
        <p className="text-red-700">{error}</p>
        <div className="mt-4 p-3 bg-red-100 rounded-lg">
          <p className="text-sm text-red-600">
            💡 <strong>Dica:</strong> Verifique se a API RAG está rodando e se a URL está configurada corretamente.
          </p>
        </div>
      </div>
    )
  }

  if (!response && !streaming && !displayedText) {
    return (
      <div className="card text-center py-12">
        <Search className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-xl font-semibold text-gray-600 mb-2">
          Faça sua consulta
        </h3>
        <p className="text-gray-500 max-w-md mx-auto">
          Digite uma pergunta.
        </p>
      </div>
    )
  }

  const documentsToShow = sourceDocuments.length > 0 ? sourceDocuments : (response?.source_documents || [])
  const textToShow = displayedText

  return (
    <div className="space-y-6">
      {/* Resposta Principal */}
      {(textToShow || streaming) && (
        <div className="card animate-fadeIn">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              {streaming ? (
                <Sparkles className="w-4 h-4 text-white animate-pulse" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-800">
              Resposta
            </h3>
            {streaming && loading && (
              <span className="text-xs text-blue-600 animate-pulse">
                Gerando resposta em tempo real...
              </span>
            )}
          </div>
          
          <div className="prose prose-gray max-w-none">
            {textToShow ? formatMarkdown(textToShow) : null}
            {(streaming && loading) || isTyping ? <BlinkingCursor /> : null}
          </div>
        </div>
      )}

      {/* Documentos Fonte (aparecem depois da resposta) */}
      {documentsToShow.length > 0 && (
        <div className="card animate-fadeIn">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <FileText className="w-4 h-4 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800">
              Artigos e Dispositivos Consultados
            </h3>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
              {documentsToShow.length} fonte{documentsToShow.length !== 1 ? 's' : ''}
            </span>
          </div>
          
          <div className="space-y-4">
            {documentsToShow.map((doc, index) => (
              <div 
                key={index}
                className="p-4 bg-gray-50 rounded-xl border-l-4 border-blue-500 hover:bg-gray-100 transition-colors animate-slideIn"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-medium text-blue-600">
                      {index + 1}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {doc.page_content}
                    </p>
                    {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(doc.metadata).map(([key, value]) => (
                            <span 
                              key={key}
                              className="inline-flex items-center gap-1 px-2 py-1 bg-white text-xs text-gray-600 rounded border"
                            >
                              <span className="font-medium">{key}:</span>
                              <span>{String(value)}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}