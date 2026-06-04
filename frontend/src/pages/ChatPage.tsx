import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Sparkles, RefreshCw } from "lucide-react";
import { ChatMessage } from "@/types";
import { generateId, formatCurrency } from "@/utils/helpers";
import { getAccessToken } from "@/services/api";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STARTER_PROMPTS = [
  "How can I reduce my food & dining expenses?",
  "Am I saving enough money each month?",
  "What's the 50/30/20 budgeting rule?",
  "Help me build a 3-month emergency fund plan",
];

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      <Bot className="w-5 h-5 text-primary-500 shrink-0" />
      <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-card">
        <div className="flex gap-1">
          <span className="typing-dot w-1.5 h-1.5 bg-gray-400 rounded-full" />
          <span className="typing-dot w-1.5 h-1.5 bg-gray-400 rounded-full" />
          <span className="typing-dot w-1.5 h-1.5 bg-gray-400 rounded-full" />
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`p-1.5 rounded-full shrink-0 ${isUser ? "bg-primary-100" : "bg-gray-100"}`}>
        {isUser
          ? <User className="w-4 h-4 text-primary-600" />
          : <Bot className="w-4 h-4 text-gray-600" />}
      </div>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-card ${
          isUser
            ? "bg-primary-600 text-white rounded-tr-sm"
            : "bg-white border border-gray-100 text-gray-800 rounded-tl-sm"
        }`}
      >
        {message.content.split("\n").map((line, i) => (
          <p key={i} className={i > 0 ? "mt-2" : ""}>{line}</p>
        ))}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your FinSight AI financial advisor. I can help you understand your spending patterns, optimize your budget, and build better financial habits. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    const assistantId = generateId();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const allMessages = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ messages: allMessages }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.delta) {
                accumulated += parsed.delta;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: accumulated } : m
                  )
                );
              }
            } catch {
              // Skip malformed SSE data
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: "Sorry, I encountered an error. Please check your API keys and try again." }
              : m
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [messages, isStreaming]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
  };

  const handleReset = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setMessages([{
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your FinSight AI financial advisor. How can I help you today?",
      timestamp: new Date(),
    }]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary-500" />
            AI Financial Advisor
          </h1>
          <p className="text-gray-500 text-sm mt-0.5">Powered by GPT-4o with your financial context</p>
        </div>
        <button onClick={handleReset} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-3.5 h-3.5" />
          New chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-xl border border-gray-100 p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isStreaming && messages[messages.length - 1]?.content === "" && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Starter prompts */}
      {messages.length <= 1 && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {STARTER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="text-left text-xs text-gray-600 bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-primary-300 hover:text-primary-700 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="mt-3 bg-white border border-gray-200 rounded-xl shadow-card p-3">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your finances..."
            rows={1}
            className="flex-1 resize-none border-0 outline-none text-sm text-gray-800 placeholder-gray-400 bg-transparent leading-relaxed max-h-32 overflow-auto"
            style={{ fieldSizing: "content" } as React.CSSProperties}
            disabled={isStreaming}
          />
          {isStreaming ? (
            <button
              onClick={handleStop}
              className="p-2 rounded-lg bg-danger-100 text-danger-600 hover:bg-danger-200 transition-colors shrink-0"
            >
              <div className="w-4 h-4 bg-danger-600 rounded-sm" />
            </button>
          ) : (
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim()}
              className="p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
        <p className="text-[10px] text-gray-400 mt-2">
          Enter to send · Shift+Enter for new line · Not financial advice — consult a professional for complex decisions
        </p>
      </div>
    </div>
  );
}
