export enum Role {
  USER = 'user',
  MODEL = 'model',
}

export interface Message {
  role: Role;
  text: string;
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