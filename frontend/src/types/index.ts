export interface SearchConfig {
  apiUrl: string
  limit: number
  temperature: number
  maxTokens: number
  useStreaming?: boolean // Nova opção
}

export interface Document {
  page_content: string
  metadata?: Record<string, any>
}

export interface SearchResponse {
  answer: string
  source_documents: Document[]
}

export interface SearchRequest {
  query: string
  limit?: number
  temperature?: number
  max_output_tokens?: number
}

// Novos tipos para streaming
export interface StreamEvent {
  type: 'source_documents' | 'text_delta' | 'text_done' | 'response.created' | 
        'response.completed' | 'stream_completed' | 'error' | 'response.failed'
  [key: string]: any
}

export interface TextDeltaEvent extends StreamEvent {
  type: 'text_delta'
  delta: string
  output_index: number
  content_index: number
}

export interface SourceDocumentsEvent extends StreamEvent {
  type: 'source_documents'
  documents: Document[]
}