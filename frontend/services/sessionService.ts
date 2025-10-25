import axios from 'axios';
import { Session, SessionVersion } from '../types';

const API_BASE = 'http://127.0.0.1:8000/api';

export const createSession = async (
  userId: string,
  sessionId: string,
  videoId?: string,
  videoUrl?: string,
  featureId?: string
): Promise<{ session_pk: number; message: string }> => {
  const params = new URLSearchParams({
    user_id: userId,
    session_id: sessionId,
  });
  
  if (videoId) params.append('video_id', videoId);
  if (videoUrl) params.append('video_url', videoUrl);
  if (featureId) params.append('feature_id', featureId);

  const response = await axios.post(`${API_BASE}/sessions/create?${params.toString()}`);
  return response.data;
};

export const getSession = async (
  userId: string,
  sessionId: string
): Promise<Session> => {
  const params = new URLSearchParams({
    user_id: userId,
    session_id: sessionId,
  });

  const response = await axios.get(`${API_BASE}/sessions/get?${params.toString()}`);
  return response.data;
};

export const listSessions = async (
  userId: string,
  videoId?: string,
  featureId?: string
): Promise<Session[]> => {
  const params = new URLSearchParams({ user_id: userId });
  
  if (videoId) params.append('video_id', videoId);
  if (featureId) params.append('feature_id', featureId);

  const response = await axios.get(`${API_BASE}/sessions/list?${params.toString()}`);
  return response.data;
};

export const createVersion = async (
  sessionPk: number,
  videoUrl?: string
): Promise<{ version_id: number; message: string }> => {
  const params = new URLSearchParams({ session_pk: sessionPk.toString() });
  
  if (videoUrl) params.append('video_url', videoUrl);

  const response = await axios.post(`${API_BASE}/sessions/version?${params.toString()}`);
  return response.data;
};

export const getVersions = async (sessionPk: number): Promise<SessionVersion[]> => {
  const params = new URLSearchParams({ session_pk: sessionPk.toString() });

  const response = await axios.get(`${API_BASE}/sessions/versions?${params.toString()}`);
  return response.data;
};

export const deleteSession = async (userId: string, sessionId: string): Promise<void> => {
  const params = new URLSearchParams({
    user_id: userId,
    session_id: sessionId,
  });

  await axios.delete(`${API_BASE}/sessions/delete?${params.toString()}`);
};

export const updateSessionState = async (
  userId: string,
  sessionId: string,
  state: Record<string, any>
): Promise<void> => {
  const params = new URLSearchParams({
    user_id: userId,
    session_id: sessionId,
  });

  await axios.put(`${API_BASE}/sessions/update?${params.toString()}`, { state });
};

export const renameSession = async (
  userId: string,
  sessionId: string,
  newName: string
): Promise<void> => {
  const params = new URLSearchParams({
    user_id: userId,
    session_id: sessionId,
    new_name: newName,
  });

  await axios.put(`${API_BASE}/sessions/rename?${params.toString()}`);
};

export const deleteAllSessions = async (userId: string): Promise<{ deleted_count: number; message: string }> => {
  const params = new URLSearchParams({
    user_id: userId,
  });

  const response = await axios.delete(`${API_BASE}/sessions/delete-all?${params.toString()}`);
  return response.data;
};
