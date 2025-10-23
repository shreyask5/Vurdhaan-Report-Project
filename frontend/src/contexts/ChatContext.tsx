import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { ChatMessage, ChatSession, ChatMetadata } from '../types/chat';
import { chatService } from '../services/chat';
import { projectChatService } from '../services/projectChat';
import { chatHistoryService } from '../services/chatHistory';

interface ChatContextType {
  sessionId: string | null;
  projectId: string | null;
  messages: ChatMessage[];
  isInitialized: boolean;
  isLoading: boolean;
  hasUserMessage: boolean;
  databaseInfo?: ChatSession['database_info'];

  // Chat history management
  chats: ChatMetadata[];
  currentChatId: string | null;
  isLoadingChats: boolean;

  initializeSession: (cleanFile: File, errorFile: File) => Promise<void>;
  initializeFromProject: (projectId: string) => Promise<void>;
  autoInitialize: (sessionId: string) => Promise<void>;
  sendMessage: (query: string) => Promise<void>;
  reset: () => void;

  // Chat history methods
  loadProjectChats: (projectId: string) => Promise<void>;
  createNewChat: () => Promise<void>;
  switchChat: (chatId: string) => Promise<void>;
  renameChat: (chatId: string, newName: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
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

  // Chat history state
  const [chats, setChats] = useState<ChatMetadata[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isLoadingChats, setIsLoadingChats] = useState(false);

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
    setChats([]);
    setCurrentChatId(null);
  };

  // Chat history management methods
  const loadProjectChats = useCallback(async (pid: string) => {
    setIsLoadingChats(true);
    try {
      const projectChats = await chatHistoryService.getProjectChats(pid);
      setChats(projectChats);

      // Set active chat as current
      const activeChat = projectChats.find(c => c.is_active);
      if (activeChat) {
        setCurrentChatId(activeChat.id);
      }

      chatHistoryService.logDebug('Loaded project chats', { count: projectChats.length });
    } catch (error) {
      chatHistoryService.logError('Failed to load chats', error);
    } finally {
      setIsLoadingChats(false);
    }
  }, []);

  const createNewChat = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    try {
      const newChat = await chatHistoryService.createChat(projectId);

      // Set as active
      await chatHistoryService.setActiveChat(projectId, newChat.id);

      // Update chats list
      setChats(prev => [newChat, ...prev.map(c => ({ ...c, is_active: false }))]);
      setCurrentChatId(newChat.id);

      // Clear messages for new chat
      setMessages([]);
      setHasUserMessage(false);

      chatHistoryService.logDebug('Created new chat', { chatId: newChat.id });
    } catch (error) {
      chatHistoryService.logError('Failed to create chat', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const switchChat = useCallback(async (chatId: string) => {
    if (!projectId || chatId === currentChatId) return;

    setIsLoading(true);
    try {
      // Load messages for the chat
      const chatData = await chatHistoryService.getChatMessages(projectId, chatId, 100, 0);

      // Convert stored messages to ChatMessage format
      const loadedMessages: ChatMessage[] = chatData.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        sql_query: msg.sql_query,
        table_data: msg.table_data,
        timestamp: new Date(msg.timestamp),
        metadata: msg.metadata
      }));

      setMessages(loadedMessages);
      setCurrentChatId(chatId);
      setHasUserMessage(loadedMessages.some(m => m.role === 'user'));

      // Set as active
      await chatHistoryService.setActiveChat(projectId, chatId);

      // Update chats list to reflect active status
      setChats(prev => prev.map(c => ({
        ...c,
        is_active: c.id === chatId
      })));

      chatHistoryService.logDebug('Switched to chat', { chatId });
    } catch (error) {
      chatHistoryService.logError('Failed to switch chat', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [projectId, currentChatId]);

  const renameChat = useCallback(async (chatId: string, newName: string) => {
    if (!projectId) return;

    try {
      await chatHistoryService.renameChat(projectId, chatId, newName);

      // Update local state
      setChats(prev => prev.map(c =>
        c.id === chatId ? { ...c, name: newName } : c
      ));

      chatHistoryService.logDebug('Renamed chat', { chatId, newName });
    } catch (error) {
      chatHistoryService.logError('Failed to rename chat', error);
      throw error;
    }
  }, [projectId]);

  const deleteChat = useCallback(async (chatId: string) => {
    if (!projectId) return;

    try {
      await chatHistoryService.deleteChat(projectId, chatId);

      // Remove from local state
      setChats(prev => prev.filter(c => c.id !== chatId));

      // If deleted chat was current, switch to first available or create new
      if (chatId === currentChatId) {
        const remainingChats = chats.filter(c => c.id !== chatId);
        if (remainingChats.length > 0) {
          await switchChat(remainingChats[0].id);
        } else {
          // No chats left, create a new one
          await createNewChat();
        }
      }

      chatHistoryService.logDebug('Deleted chat', { chatId });
    } catch (error) {
      chatHistoryService.logError('Failed to delete chat', error);
      throw error;
    }
  }, [projectId, currentChatId, chats, switchChat, createNewChat]);

  return (
    <ChatContext.Provider value={{
      sessionId,
      projectId,
      messages,
      isInitialized,
      isLoading,
      hasUserMessage,
      databaseInfo,
      chats,
      currentChatId,
      isLoadingChats,
      initializeSession,
      initializeFromProject,
      autoInitialize,
      sendMessage,
      reset,
      loadProjectChats,
      createNewChat,
      switchChat,
      renameChat,
      deleteChat
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
