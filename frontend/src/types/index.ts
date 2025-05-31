export interface SearchConfig {
  apiUrl: string
  limit: number
  temperature: number
  maxTokens: number
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