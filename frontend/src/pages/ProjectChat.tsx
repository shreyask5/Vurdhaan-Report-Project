import React, { useEffect, useState } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { useChat } from '../contexts/ChatContext';
import { ChatInterface } from '../components/project/ChatInterface';
import { ProjectHeader } from '../components/layout/ProjectHeader';
import { ChatSidebar } from '../components/chat/ChatSidebar';
import { DeleteChatModal } from '../components/chat/DeleteChatModal';

const ProjectChat: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { projectId: urlProjectId } = useParams<{ projectId: string }>();
  const {
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
    loadProjectChats,
    createNewChat,
    switchChat,
    renameChat,
    deleteChat
  } = useChat();

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Auto-initialize from URL parameters
  // Priority: 1) session_id (for existing sessions), 2) projectId (for new sessions)
  useEffect(() => {
    const sessionIdParam = searchParams.get('session_id');

    if (sessionIdParam && !isInitialized && !sessionId) {
      // Existing session - auto-initialize from session_id
      console.log('🔄 Auto-initializing chat from URL session_id:', sessionIdParam);
      autoInitialize(sessionIdParam).catch(error => {
        console.error('Failed to auto-initialize:', error);
        alert('Failed to load chat session. The session may have expired.');
      });
    } else if (urlProjectId && !isInitialized && !sessionId) {
      // New session - initialize from projectId
      console.log('🔄 Initializing new chat session from project:', urlProjectId);
      initializeFromProject(urlProjectId).catch(error => {
        console.error('Failed to initialize from project:', error);
        alert('Failed to initialize chat session. Please ensure the project has uploaded data.');
      });
    }
  }, [searchParams, urlProjectId, isInitialized, sessionId, initializeFromProject, autoInitialize]);

  // Load chats when project is initialized
  useEffect(() => {
    if (projectId && isInitialized) {
      loadProjectChats(projectId);
    }
  }, [projectId, isInitialized, loadProjectChats]);

  const handleDeleteChat = (chatId: string) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setChatToDelete({ id: chat.id, name: chat.name });
    }
  };

  const confirmDeleteChat = async () => {
    if (!chatToDelete) return;

    setIsDeleting(true);
    try {
      await deleteChat(chatToDelete.id);
      setChatToDelete(null);
    } catch (error) {
      alert('Failed to delete chat. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <ProjectHeader />

      {/* Main Content Area with Sidebar */}
      <div className="flex-1 overflow-hidden flex">
        {/* Chat Sidebar */}
        <ChatSidebar
          chats={chats}
          activeChatId={currentChatId}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          onCreateChat={createNewChat}
          onSelectChat={switchChat}
          onRenameChat={renameChat}
          onDeleteChat={handleDeleteChat}
          isLoading={isLoadingChats}
        />

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            sessionId={sessionId}
            messages={messages}
            isInitialized={isInitialized}
            isLoading={isLoading}
            hasUserMessage={hasUserMessage}
            databaseInfo={databaseInfo}
            onSendMessage={sendMessage}
            onInitialize={initializeSession}
          />
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteChatModal
        chatName={chatToDelete?.name || ''}
        isOpen={chatToDelete !== null}
        onConfirm={confirmDeleteChat}
        onCancel={() => setChatToDelete(null)}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default ProjectChat;
