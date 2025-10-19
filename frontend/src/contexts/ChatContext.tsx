import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ChatMessage, ChatSession } from '../types/chat';
import { chatService } from '../services/chat';
import { projectChatService } from '../services/projectChat';

interface ChatContextType {
  sessionId: string | null;
  projectId: string | null;
  messages: ChatMessage[];
  isInitialized: boolean;
  isLoading: boolean;
  hasUserMessage: boolean;
  databaseInfo?: ChatSession['database_info'];

  initializeSession: (cleanFile: File, errorFile: File) => Promise<void>;
  initializeFromProject: (projectId: string) => Promise<void>;
  autoInitialize: (sessionId: string) => Promise<void>;
  sendMessage: (query: string) => Promise<void>;
  reset: () => void;
}

export const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUserMessage, setHasUserMessage] = useState(false);
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

  const initializeFromProject = async (pid: string) => {
    setIsLoading(true);
    try {
      const session = await projectChatService.initializeFromProject(pid);

      setSessionId(session.sessionId);
      setProjectId(pid);
      setDatabaseInfo(session.databaseInfo);
      setIsInitialized(true);

      // Add welcome message
      const welcomeMessage: ChatMessage = {
        id: `msg_${Date.now()}_welcome`,
        role: 'assistant',
        content: 'Chat session initialized! I can help you analyze your flight data. What would you like to know?',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);

      projectChatService.logDebug('Project chat initialized', { session_id: session.sessionId, project_id: pid });
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
    setHasUserMessage(true); // Mark that user has sent a message
    setIsLoading(true);

    try {
      let response;

      // Use project chat service if we have a projectId, otherwise use file-based chat
      if (projectId) {
        response = await projectChatService.sendQuery(projectId, query, sessionId);
      } else {
        response = await chatService.sendQuery(sessionId, query);
      }

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
      const errorMessage = error instanceof Error ? error.message : 'Unknown';
      if (projectId) {
        projectChatService.logError('Query failed', { error: errorMessage });
      } else {
        chatService.logError('Query failed', { error: errorMessage });
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setSessionId(null);
    setProjectId(null);
    setMessages([]);
    setIsInitialized(false);
    setHasUserMessage(false);
    setDatabaseInfo(undefined);
  };

  return (
    <ChatContext.Provider value={{
      sessionId,
      projectId,
      messages,
      isInitialized,
      isLoading,
      hasUserMessage,
      databaseInfo,
      initializeSession,
      initializeFromProject,
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
