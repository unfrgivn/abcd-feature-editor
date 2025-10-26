export enum Role {
  USER = 'user',
  MODEL = 'model',
}

export interface MediaAttachment {
  audio_urls?: string[];
  video_url?: string;
}

export interface Message {
  role: Role;
  text: string;
  media?: MediaAttachment;
  isEditQueueSuccess?: boolean;
}

export interface Feature {
  id: string;
  name: string;
  category: string;
  description: string;
  detected: boolean;
  llmExplanation: string;
  isFixed: boolean;
  videoId: string;
  videoUrl: string;
}

export enum RecommendationStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
}

export interface RecommendationMetadata {
  text?: string;
  audio_text?: string;
  position?: string;
  color?: string;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  status: RecommendationStatus;
  videoUrl?: string;
  audioUrls?: string[];
  metadata?: RecommendationMetadata;
  messageIndex?: number;
}

export interface Session {
  pk: number;
  app_name: string;
  user_id: string;
  session_id: string;
  video_id: string | null;
  video_url: string | null;
  feature_id: string | null;
  created_at: string;
  updated_at: string;
  state?: Record<string, any>;
}

export interface SessionVersion {
  id: number;
  version_number: number;
  video_url: string | null;
  created_at: string;
}

export type EditType = 'voiceover' | 'text_overlay' | 'trim' | 'filter';
export type EditStatus = 'pending' | 'applied' | 'reverted' | 'overwritten' | 'superseded';

export interface Edit {
  id: string;
  type: EditType;
  params: Record<string, any>;
  timestamp: string;
  status: EditStatus;
  result_video_url?: string;
}

export interface EditQueue {
  session_id: string;
  original_video_url: string;
  edits: Edit[];
  current_video_url: string;
}
