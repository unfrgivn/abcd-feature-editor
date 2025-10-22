import { GoogleGenAI, Chat } from "@google/genai";

let ai: GoogleGenAI;
let chat: Chat;

export function startChatSession(systemInstruction?: string) {
  if (!process.env.API_KEY) {
    throw new Error("API_KEY environment variable not set");
  }
  ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  chat = ai.chats.create({
    model: 'gemini-2.5-flash',
    config: {
      systemInstruction: systemInstruction || 'You are a helpful and friendly AI assistant. Your responses should be informative and engaging.',
    },
  });
}

export async function sendMessageStream(
  message: string, 
  onChunk: (chunk: string) => void
): Promise<void> {
  if (!chat) {
    throw new Error("Chat session not initialized. Call startChatSession first.");
  }

  try {
    const stream = await chat.sendMessageStream({ message });
    for await (const chunk of stream) {
      onChunk(chunk.text);
    }
  } catch (error) {
    console.error("Error sending message to Gemini:", error);
    onChunk("Sorry, I encountered an error. Please try again.");
  }
}