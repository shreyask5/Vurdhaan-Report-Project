import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useChat } from '../contexts/ChatContext';
import { ChatInterface } from '../components/project/ChatInterface';
import { ProjectHeader } from '../components/layout/ProjectHeader';

const ProjectChat: React.FC = () => {
  const [searchParams] = useSearchParams();
  const {
    sessionId,
    messages,
    isInitialized,
    isLoading,
    databaseInfo,
    initializeSession,
    autoInitialize,
    sendMessage
  } = useChat();

  // Auto-initialize from URL session_id parameter
  useEffect(() => {
    const sessionIdParam = searchParams.get('session_id');
    if (sessionIdParam && !isInitialized && !sessionId) {
      console.log('🔄 Auto-initializing chat from URL session_id:', sessionIdParam);
      autoInitialize(sessionIdParam).catch(error => {
        console.error('Failed to auto-initialize:', error);
        alert('Failed to load chat session. The session may have expired.');
      });
    }
  }, [searchParams, isInitialized, sessionId]);

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
