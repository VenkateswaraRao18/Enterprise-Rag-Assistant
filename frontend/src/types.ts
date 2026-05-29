export interface Persona {
  label: string;
  team: string;
  role: string;
  clearance: string;
}

export interface Citation {
  ref: number;
  doc_id?: string;
  source_type: string;
  source_id: string;
  title: string;
  source_url?: string;
  timestamp?: string;
}

export interface RetrievalStats {
  total_docs: number;
  allowed_docs: number;
  bm25_count: number;
  dense_count: number;
  fused_count: number;
}

export interface AskResponse {
  query: string;
  answer: string;
  abstained: boolean;
  citations: Citation[];
  stats: RetrievalStats;
  security_blocked: boolean;
  security_category?: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  time?: string;
  abstained?: boolean;
  citations?: Citation[];
  stats?: RetrievalStats;
  securityBlocked?: boolean;
  securityCategory?: string | null;
}
