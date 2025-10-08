import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ChatMessage, ChatSession } from '../types/chat';
import { chatService } from '../services/chat';

interface ChatContextType {
  sessionId: string | null;
  messages: ChatMessage[];
  isInitialized: boolean;
  isLoading: boolean;
  databaseInfo?: ChatSession['database_info'];

  initializeSession: (cleanFile: File, errorFile: File) => Promise<void>;
  autoInitialize: (sessionId: string) => Promise<void>;
  sendMessage: (query: string) => Promise<void>;
  reset: () => void;
}

export const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [databaseInfo, setDatabaseInfo] = useState<ChatSession['database_info']>();

  const initializeSession = async (cleanFile: File, errorFile: File) => {
    setIsLoading(true);
    try {
      const uploadResponse = await chatService.uploadFiles(cleanFile, errorFile);
      const newSessionId = chatService.generateSessionId();

      await chatService.initializeSession(
        newSessionId,
        uploadResponse.clean_flights_path,
        uploadResponse.error_flights_path
      );

      const sessionData = await chatService.getSessionStatus(newSessionId);

      setSessionId(newSessionId);
      setDatabaseInfo(sessionData.database_info);
      setIsInitialized(true);

      chatService.logDebug('Session initialized', { session_id: newSessionId });
    } finally {
      setIsLoading(false);
    }
  };

  const autoInitialize = async (sid: string) => {
    setIsLoading(true);
    try {
      const sessionData = await chatService.getSessionStatus(sid);
      setSessionId(sid);
      setDatabaseInfo(sessionData.database_info);
      setIsInitialized(true);

      chatService.logDebug('Auto-initialized from URL', { session_id: sid });
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (query: string) => {
    if (!sessionId) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await chatService.sendQuery(sessionId, query);

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.answer || response.response || '',
        sql_query: response.sql_query,
        table_data: response.table_data,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      chatService.logError('Query failed', { error: error instanceof Error ? error.message : 'Unknown' });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setSessionId(null);
    setMessages([]);
    setIsInitialized(false);
    setDatabaseInfo(undefined);
  };

  return (
    <ChatContext.Provider value={{
      sessionId,
      messages,
      isInitialized,
      isLoading,
      databaseInfo,
      initializeSession,
      autoInitialize,
      sendMessage,
      reset
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
};
