/**
 * ChatInterface Component
 * AI chat interface for querying flight data with natural language
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageSquare, Code, Lightbulb } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { CollapsibleTable } from './CollapsibleTable';
import { chatService } from '@/services/chat';
import type { ChatMessage } from '@/types/validation';
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
  projectId: string;
  sessionId?: string;
  onSessionCreated?: (sessionId: string) => void;
}

export function ChatInterface({ projectId, sessionId, onSessionCreated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const suggestedQuestions = chatService.getSuggestedQuestions();

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize session if not provided
    if (!currentSessionId) {
      initializeSession();
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    try {
      const session = await chatService.initializeSession(projectId);
      setCurrentSessionId(session.session_id);
      onSessionCreated?.(session.session_id);

      // Add welcome message
      setMessages([
        {
          role: 'system',
          content: `Session initialized. You can now ask questions about your flight data.${
            session.database_info?.clean_flights
              ? `\n\nLoaded ${session.database_info.clean_flights.row_count} clean flight records.`
              : ''
          }`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error: any) {
      setMessages([
        {
          role: 'system',
          content: `Failed to initialize chat session: ${error.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading || !currentSessionId) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatService.sendQuery(projectId, userMessage.content, currentSessionId);

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer || response.response,
        sql_query: response.sql_query,
        table_data: response.table_data,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="border-b border-border flex-shrink-0">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <CardTitle>AI Chat Assistant</CardTitle>
            {currentSessionId && (
              <Badge variant="outline" className="ml-auto">
                Session Active
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="text-center py-12 space-y-4">
              <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <MessageSquare className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Start a Conversation</h3>
                <p className="text-sm text-muted-foreground">
                  Ask questions about your flight data in natural language
                </p>
              </div>

              {/* Suggested Questions */}
              <div className="max-w-2xl mx-auto space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Lightbulb className="h-4 w-4" />
                  <span>Try asking:</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {suggestedQuestions.slice(0, 4).map((question, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestedQuestion(question)}
                      className="justify-start text-left h-auto py-2 px-3 text-xs"
                    >
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <ChatMessageBubble key={idx} message={message} />
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      {/* Input Area */}
      <Card className="flex-shrink-0 mt-4">
        <CardContent className="p-4">
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your flight data..."
              className="min-h-[60px] max-h-[200px] resize-none"
              disabled={isLoading || !currentSessionId}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!input.trim() || isLoading || !currentSessionId}
              size="lg"
              className="px-6"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 space-y-3 ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-muted border border-border'
            : 'bg-card border border-border'
        }`}
      >
        {/* Message Content */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* SQL Query */}
        {message.sql_query && (
          <Card className="bg-muted/50">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <Code className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground">SQL Query</span>
              </div>
              <pre className="text-xs font-mono overflow-x-auto bg-background p-2 rounded">
                {chatService.formatSQL(message.sql_query)}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Table Data */}
        {message.table_data && message.table_data.length > 0 && (
          <CollapsibleTable data={message.table_data} title="Query Results" />
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className="text-xs opacity-70">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
