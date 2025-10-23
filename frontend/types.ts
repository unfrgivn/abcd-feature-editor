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