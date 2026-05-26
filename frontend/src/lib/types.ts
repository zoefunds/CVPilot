export interface UserPublic {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  wallet_address: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface WalletPublic {
  address: string;
  balance_wei: number;
  balance_gen: string;
  contract_address: string;
}

export interface WalletExport {
  address: string;
  private_key: string;
  warning: string;
}

export interface WalletSendRequest {
  to_address: string;
  amount_gen: string;
}

export interface WalletSendResponse {
  tx_hash: string;
  from_address: string;
  to_address: string;
  amount_wei: number;
  amount_gen: string;
  explorer_url: string | null;
}

export type WalletActivityKind = 'evaluation' | 'send';

export interface WalletActivityItem {
  kind: WalletActivityKind;
  timestamp: string;
  tx_hash: string | null;
  status: string;
  description: string;
  to_address: string | null;
  amount_wei: number | null;
  amount_gen: string | null;
  application_id: string | null;
  explorer_url: string | null;
}

export type ApplicationStatus =
  | 'pending'
  | 'processing'
  | 'ready'
  | 'evaluating'
  | 'complete'
  | 'failed';

export type FileKind = 'cv' | 'cover_letter';

export interface FileAssetPublic {
  id: string;
  kind: FileKind;
  original_filename: string;
  content_type: string;
  byte_size: number;
  detected_kind: string | null;
  extracted_text: string | null;
}

export interface ApplicationPublic {
  user_id: string;
  id: string;
  job_url: string;
  job_final_url: string | null;
  job_title: string | null;
  job_text: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  status: ApplicationStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
  files: FileAssetPublic[];
}

export interface ApplicationListItem {
  id: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
}

export type EvaluationStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface EvaluationRationale {
  cv_score?: string;
  cover_letter_score?: string;
  job_match_score?: string;
  ats_score?: string;
  competitiveness_score?: string;
  overall_score?: string;
}

export interface EvaluationPublic {
  id: string;
  application_id: string;
  status: EvaluationStatus;
  backend: string | null;
  cv_score: number | null;
  cover_letter_score: number | null;
  job_match_score: number | null;
  ats_score: number | null;
  competitiveness_score: number | null;
  overall_score: number | null;
  summary: string | null;
  improved_positioning: string | null;
  recommendations: string[];
  missing_keywords: string[];
  missing_skills: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  strengths: string[];
  risks: string[];
  rationale: EvaluationRationale | null;
  raw: Record<string, unknown> | null;
  error: string | null;
  contract_tx_hash: string | null;
  content_hash: string | null;
  contract_address: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublicEvaluation {
  content_hash: string;
  contract_address: string;
  found: boolean;
  cv_score: number | null;
  cover_letter_score: number | null;
  job_match_score: number | null;
  ats_score: number | null;
  competitiveness_score: number | null;
  overall_score: number | null;
  summary: string | null;
  improved_positioning: string | null;
  missing_keywords: string[];
  missing_skills: string[];
  recommendations: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  strengths: string[];
  risks: string[];
  rationale: EvaluationRationale | null;
}

export interface AdminStats {
  user_count: number;
  application_count: number;
  evaluations_complete: number;
  evaluations_failed: number;
  last_24h_users: number;
  last_24h_applications: number;
  by_status: Record<string, number>;
}

export interface AdminUserListItem {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  created_at: string;
  application_count: number;
  last_application_at: string | null;
}

export interface AdminApplicationListItem {
  id: string;
  user_id: string;
  user_email: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
  has_evaluation: boolean;
  competitiveness: number | null;
}
