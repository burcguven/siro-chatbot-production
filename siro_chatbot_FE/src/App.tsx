import { useState, useEffect, useCallback } from "react";
import type { ReactNode } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ChatView } from "@/components/ChatView";
import { Button } from "@/components/ui/button";
import { Menu, LogOut, Sparkles } from "lucide-react";
import axios from "axios";

import LoginPage from "@/pages/LoginPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminPage from "./pages/AdminPage";
import AdminRestrictionsPage from "./pages/AdminRestrictionsPage";
import AuthCallbackPage from "./pages/AuthCallbackPage";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
}

export const API_BASE_URL = import.meta.env.VITE_CHATBOT_BACKEND_API;

function ChatPage() {
  const navigate = useNavigate();

  const [chats, setChats] = useState<Chat[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("siro_token");
    navigate("/");
  }, [navigate]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("siro_token");
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  const formatTime = (value: string) => {
    if (!value) return "";
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const fetchChats = useCallback(async () => {
    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return [];
    }

    try {
      const res = await axios.get(`${API_BASE_URL}/all_chats`, {
        headers: getAuthHeaders(),
      });

      const mappedChats: Chat[] = (res.data.chats || []).map((chat: any) => ({
        id: String(chat.chat_id),
        title: chat.title || "Yeni Sohbet",
        lastMessage: chat.last_message || "",
        timestamp: chat.updated_at ? formatTime(chat.updated_at) : "Az önce",
      }));

      setChats(mappedChats);
      return mappedChats;
    } catch (err: any) {
      console.error("Chat listesi alınamadı:", err);

      if (err.response?.status === 401) {
        alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
        handleLogout();
      }

      return [];
    }
  }, [handleLogout]);

  const fetchMessages = useCallback(
    async (chatId: string) => {
      const token = localStorage.getItem("siro_token");
      if (!token) {
        handleLogout();
        return [];
      }

      try {
        const res = await axios.get(
          `${API_BASE_URL}/chat/get_all_messages/${chatId}`,
          {
            headers: getAuthHeaders(),
          }
        );

        const mappedMessages: Message[] = (res.data.messages || []).map(
          (msg: any) => ({
            id: String(msg.message_id),
            role: msg.sender_role,
            content: msg.message_text,
            timestamp: msg.created_at ? formatTime(msg.created_at) : "",
          })
        );

        setMessages(mappedMessages);
        return mappedMessages;
      } catch (err: any) {
        console.error("Mesajlar alınamadı:", err);

        if (err.response?.status === 401) {
          alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
          handleLogout();
          return [];
        }

        setMessages([]);
        return [];
      }
    },
    [handleLogout]
  );

  const findRealEmptyChat = useCallback(async () => {
    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return null;
    }

    for (const chat of chats) {
      try {
        const res = await axios.get(
          `${API_BASE_URL}/chat/get_all_messages/${chat.id}`,
          {
            headers: getAuthHeaders(),
          }
        );

        const msgs = res.data.messages || [];
        if (msgs.length === 0) {
          return chat;
        }
      } catch (err: any) {
        console.error(`Chat ${chat.id} kontrol edilemedi:`, err);

        if (err.response?.status === 401) {
          alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
          handleLogout();
          return null;
        }
      }
    }

    return null;
  }, [chats, handleLogout]);

  useEffect(() => {
    const init = async () => {
      const loadedChats = await fetchChats();

      if (loadedChats.length > 0) {
        setSelectedChatId((prev) => prev ?? loadedChats[0].id);
      }
    };

    init();
  }, [fetchChats]);

  useEffect(() => {
    if (!selectedChatId) {
      setMessages([]);
      return;
    }

    fetchMessages(selectedChatId);
  }, [selectedChatId, fetchMessages]);

  const handleNewChat = async () => {
    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return;
    }

    try {
      const existingEmptyChat = await findRealEmptyChat();

      if (existingEmptyChat) {
        setSelectedChatId(existingEmptyChat.id);
        await fetchMessages(existingEmptyChat.id);
        return;
      }

      const res = await axios.post(
        `${API_BASE_URL}/chat/create`,
        {},
        {
          headers: getAuthHeaders(),
        }
      );

      const newChatId = String(res.data.chat_id);

      setSelectedChatId(newChatId);
      setMessages([]);
      await fetchChats();
    } catch (err: any) {
      console.error("Yeni chat oluşturulamadı:", err);

      if (err.response?.status === 401) {
        alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
        handleLogout();
      }
    }
  };

  const handleRenameChat = async (chatId: string, newTitle: string) => {
    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return;
    }

    try {
      await axios.put(
        `${API_BASE_URL}/chat/${chatId}/rename_chat`,
        { new_title: newTitle },
        {
          headers: getAuthHeaders(),
        }
      );

      await fetchChats();
    } catch (err: any) {
      console.error("Sohbet adı güncellenemedi:", err);

      if (err.response?.status === 401) {
        alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
        handleLogout();
      }
    }
  };

  const handleDeleteChat = async (chatId: string) => {
    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/chat/${chatId}`, {
        headers: getAuthHeaders(),
      });

      const wasSelected = selectedChatId === chatId;

      if (wasSelected) {
        setSelectedChatId(null);
        setMessages([]);
      }

      const updatedChats = await fetchChats();

      if (wasSelected && updatedChats.length > 0) {
        setSelectedChatId(updatedChats[0].id);
      }
    } catch (err: any) {
      console.error("Sohbet silinemedi:", err);

      if (err.response?.status === 401) {
        alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
        handleLogout();
      }
    }
  };

  const handleSendMessage = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;

    const token = localStorage.getItem("siro_token");
    if (!token) {
      handleLogout();
      return;
    }

    let currentChatId = selectedChatId;

    try {
      setIsLoading(true);

      if (!currentChatId) {
        const createRes = await axios.post(
          `${API_BASE_URL}/chat/create`,
          {},
          {
            headers: getAuthHeaders(),
          }
        );

        currentChatId = String(createRes.data.chat_id);
        setSelectedChatId(currentChatId);
        await fetchChats();
      }

      const now = new Date();
      const timeLabel = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const optimisticUserMessage: Message = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: trimmed,
        timestamp: timeLabel,
      };

      const assistantMessageId = `temp-assistant-${Date.now()}`;

      const optimisticAssistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: timeLabel,
      };

      setMessages((prev) => [
        ...prev,
        optimisticUserMessage,
        optimisticAssistantMessage,
      ]);

      const response = await fetch(`${API_BASE_URL}/ask-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: trimmed,
          history: [],
          chat_id: Number(currentChatId),
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
          handleLogout();
          return;
        }

        throw new Error("Streaming response başarısız.");
      }

      if (!response.body) {
        throw new Error("Response body bulunamadı.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let shouldContinue = true;

      while (shouldContinue) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;

          const data = JSON.parse(trimmedLine);

          if (data.type === "token") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + data.content }
                  : msg
              )
            );
          } else if (data.type === "error") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: data.message || "Cevap oluşturulurken hata oluştu.",
                    }
                  : msg
              )
            );
            shouldContinue = false;
          } else if (data.type === "done") {
            shouldContinue = false;
          }
        }
      }

      await fetchChats();
      await fetchMessages(currentChatId);
    } catch (err: any) {
      console.error("Backend error:", err);

      if (err.response?.status === 401) {
        alert("Oturum süreniz doldu, lütfen tekrar giriş yapın.");
        handleLogout();
        return;
      }

      setMessages((prev) => {
        const hasTempAssistant = prev.some(
          (msg) => msg.id.startsWith("temp-assistant-") && msg.content === ""
        );

        if (hasTempAssistant) {
          return prev.map((msg) =>
            msg.id.startsWith("temp-assistant-") && msg.content === ""
              ? {
                  ...msg,
                  content: "Bağlantı hatası veya yetkisiz erişim.",
                }
              : msg
          );
        }

        const errorTime = new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

        return [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content: "Bağlantı hatası veya yetkisiz erişim.",
            timestamp: errorTime,
          },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#0b0f19] text-white">
      <div className="relative flex h-full w-full">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(205,248,255,0.08),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(16,185,129,0.08),transparent_25%)] pointer-events-none" />

        <aside
          className={`relative z-10 h-full border-r border-white/10 bg-[#0f172a]/95 backdrop-blur-xl transition-all duration-300 ${
            sidebarOpen ? "w-[310px]" : "w-0"
          } overflow-hidden`}
        >
          <ChatSidebar
            chats={chats}
            selectedChatId={selectedChatId}
            onSelectChat={setSelectedChatId}
            onNewChat={handleNewChat}
            onRenameChat={handleRenameChat}
            onDeleteChat={handleDeleteChat}
          />
        </aside>

        <main className="relative z-10 flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 items-center justify-between border-b border-white/10 bg-[#0b1220]/80 px-4 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <Button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                variant="ghost"
                size="icon"
                className="text-gray-300 hover:bg-white/10 hover:text-white"
              >
                <Menu className="h-5 w-5" />
              </Button>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-emerald-400 shadow-lg shadow-cyan-500/20">
                  <Sparkles className="h-5 w-5 text-black" />
                </div>
                <div>
                  <p className="text-base font-semibold tracking-wide text-white">
                    Siro HR Assistant
                  </p>
                  <p className="text-xs text-gray-400">
                    Internal AI support for HR processes
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={handleNewChat}
                className="rounded-xl border border-emerald-400/20 bg-emerald-500 px-4 text-sm font-semibold text-black hover:bg-emerald-400"
              >
                Yeni Sohbet
              </Button>

              <Button
                onClick={handleLogout}
                variant="ghost"
                size="icon"
                title="Çıkış Yap"
                className="text-gray-300 hover:bg-red-500/10 hover:text-red-400"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          </header>

          <div className="min-h-0 flex-1">
            <ChatView
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </div>
        </main>
      </div>
    </div>
  );
}

function AdminDashboardWrapper() {
  return <AdminPage />;
}

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const token = localStorage.getItem("siro_token");

  if (!token) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const AdminProtectedRoute = ({ children }: { children: ReactNode }) => {
  const token = localStorage.getItem("admin_token");

  if (!token) {
    return <Navigate to="/admin-login" replace />;
  }

  return children;
};

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/admin-login" element={<AdminLoginPage />} />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminProtectedRoute>
              <AdminDashboardWrapper />
            </AdminProtectedRoute>
          }
        />
        <Route
          path="/admin/restrictions"
          element={
            <AdminProtectedRoute>
              <AdminRestrictionsPage />
            </AdminProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}