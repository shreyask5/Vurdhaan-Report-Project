import React, { useEffect } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { useChat } from '../contexts/ChatContext';
import { ChatInterface } from '../components/project/ChatInterface';
import { ProjectHeader } from '../components/layout/ProjectHeader';

const ProjectChat: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { projectId: urlProjectId } = useParams<{ projectId: string }>();
  const {
    sessionId,
    projectId,
    messages,
    isInitialized,
    isLoading,
    databaseInfo,
    initializeSession,
    initializeFromProject,
    autoInitialize,
    sendMessage
  } = useChat();

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

  const calculateExpiresIn = () => {
    if (!databaseInfo) return null;
    // You can add expiration calculation here if backend provides it
    return '2 hours';
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <ProjectHeader />

      {/* Chat Interface */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface
          sessionId={sessionId}
          messages={messages}
          isInitialized={isInitialized}
          isLoading={isLoading}
          databaseInfo={databaseInfo}
          onSendMessage={sendMessage}
          onInitialize={initializeSession}
        />
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-3">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <div>
            💡 <strong>Tip:</strong> Ask about fuel efficiency, error patterns, or flight statistics
          </div>
          <div>
            Press <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300">Ctrl</kbd> +{' '}
            <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300">Enter</kbd> to send
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ProjectChat;
