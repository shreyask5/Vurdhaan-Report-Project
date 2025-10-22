/**
 * Chat History Service
 * Handles API calls for chat history management
 */

import { api } from './api';

export interface ChatMetadata {
  id: string;
  name: string;
  project_id?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string;
  is_active?: boolean;
}

export interface StoredChatMessage {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  table_data?: any[];
  metadata?: {
    tokens_used?: number;
    model?: string;
    cache_savings_pct?: number;
    function_calls?: number;
  };
  timestamp: string;
}

export interface ChatHistoryResponse {
  success: boolean;
  chat: {
    id: string;
    name: string;
    message_count: number;
  };
  messages: StoredChatMessage[];
  has_more: boolean;
}

class ChatHistoryService {
  /**
   * Create a new chat for a project
   */
  async createChat(projectId: string): Promise<ChatMetadata> {
    console.log('[CHAT HISTORY] Creating new chat for project:', projectId);

    try {
      const response = await api.post(`/api/projects/${projectId}/chats`, {});

      console.log('[CHAT HISTORY] Chat created:', response.data);

      return {
        id: response.data.chat.id,
        name: response.data.chat.name,
        created_at: response.data.chat.created_at,
        updated_at: response.data.chat.created_at,
        message_count: 0,
        last_message_preview: '',
        is_active: true
      };
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to create chat:', error);
      throw new Error(`Failed to create chat: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get all chats for a project
   */
  async getProjectChats(projectId: string): Promise<ChatMetadata[]> {
    console.log('[CHAT HISTORY] Fetching chats for project:', projectId);

    try {
      const response = await api.get(`/api/projects/${projectId}/chats`);

      console.log('[CHAT HISTORY] Chats retrieved:', response.data.chats.length);

      return response.data.chats.map((chat: any) => ({
        id: chat.id,
        name: chat.name,
        created_at: chat.created_at,
        updated_at: chat.updated_at,
        message_count: chat.message_count,
        last_message_preview: chat.last_message_preview,
        is_active: chat.is_active
      }));
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to fetch chats:', error);
      throw new Error(`Failed to fetch chats: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get chat details with messages
   */
  async getChatMessages(
    projectId: string,
    chatId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<ChatHistoryResponse> {
    console.log('[CHAT HISTORY] Fetching messages for chat:', chatId);

    try {
      const response = await api.get(
        `/api/projects/${projectId}/chats/${chatId}?limit=${limit}&offset=${offset}`
      );

      console.log('[CHAT HISTORY] Messages retrieved:', response.data.messages.length);

      return {
        success: response.data.success,
        chat: response.data.chat,
        messages: response.data.messages,
        has_more: response.data.has_more
      };
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to fetch messages:', error);
      throw new Error(`Failed to fetch messages: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Rename a chat
   */
  async renameChat(
    projectId: string,
    chatId: string,
    newName: string
  ): Promise<void> {
    console.log('[CHAT HISTORY] Renaming chat:', chatId, 'to:', newName);

    try {
      await api.put(`/api/projects/${projectId}/chats/${chatId}`, {
        name: newName
      });

      console.log('[CHAT HISTORY] Chat renamed successfully');
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to rename chat:', error);
      throw new Error(`Failed to rename chat: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Delete a chat
   */
  async deleteChat(projectId: string, chatId: string): Promise<void> {
    console.log('[CHAT HISTORY] Deleting chat:', chatId);

    try {
      await api.delete(`/api/projects/${projectId}/chats/${chatId}`);

      console.log('[CHAT HISTORY] Chat deleted successfully');
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to delete chat:', error);
      throw new Error(`Failed to delete chat: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Set a chat as active
   */
  async setActiveChat(projectId: string, chatId: string): Promise<void> {
    console.log('[CHAT HISTORY] Setting active chat:', chatId);

    try {
      await api.post(`/api/projects/${projectId}/chats/${chatId}/set-active`, {});

      console.log('[CHAT HISTORY] Active chat set successfully');
    } catch (error) {
      console.error('[CHAT HISTORY] Failed to set active chat:', error);
      throw new Error(`Failed to set active chat: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Log debug information
   */
  logDebug(message: string, data?: any) {
    console.log(`[CHAT HISTORY DEBUG] ${message}`, data || '');
  }

  /**
   * Log error information
   */
  logError(message: string, error?: any) {
    console.error(`[CHAT HISTORY ERROR] ${message}`, error || '');
  }
}

export const chatHistoryService = new ChatHistoryService();
