import { useState, useEffect } from "react";
import axios from "axios";
import { ScrollArea } from "@/components/ui/scroll-area";
import { API_BASE_URL } from "@/App";
import {
  MessageSquare,
  Sparkles,
  Pencil,
  Trash2,
  Check,
  X,
} from "lucide-react";

interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
}

interface ChatSidebarProps {
  chats: Chat[];
  selectedChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void | Promise<void>;
  onRenameChat: (chatId: string, newTitle: string) => void | Promise<void>;
  onDeleteChat: (chatId: string) => void | Promise<void>;
}

export function ChatSidebar({
  chats,
  selectedChatId,
  onSelectChat,
  onRenameChat,
  onDeleteChat,
}: ChatSidebarProps) {
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editedTitle, setEditedTitle] = useState("");
  const [userName, setUserName] = useState<string>("");
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem("siro_token");
        if (!token) return;

        const res = await axios.get(`${API_BASE_URL}/get_username`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUserName(res.data.name || "User");
        setUserEmail(res.data.email || "");
      } catch (error) {
        console.error("Failed to fetch user info:", error);
      }
    };

    fetchUserInfo();
  }, []);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((word) => word[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };
  
  const startEditing = (chatId: string, currentTitle: string) => {
    setEditingChatId(chatId);
    setEditedTitle(currentTitle);
  };

  const cancelEditing = () => {
    setEditingChatId(null);
    setEditedTitle("");
  };

  const saveEditing = async (chatId: string) => {
    const trimmed = editedTitle.trim();
    if (!trimmed) return;

    await onRenameChat(chatId, trimmed);
    setEditingChatId(null);
    setEditedTitle("");
  };

  const handleDelete = async (chatId: string) => {
    const confirmed = window.confirm("Bu sohbeti silmek istediğinize emin misiniz?");
    if (!confirmed) return;

    await onDeleteChat(chatId);
  };

  return (
    <div className="flex h-full flex-col bg-[#0f172a] text-white">
      <div className="border-b border-white/10 p-4">
        <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3 hover:bg-white/[0.06] transition-colors">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-emerald-400 text-sm font-semibold text-black">
            {getInitials(userName)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-white">
              {userName}
            </p>
            <p className="truncate text-xs text-gray-400">
              {userEmail}
            </p>
          </div>
        </div>
      </div>

      <div className="px-4 pb-2 pt-4">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-gray-400">
          <Sparkles className="h-3.5 w-3.5" />
          Sohbet Geçmişi
        </div>
      </div>

      <ScrollArea className="flex-1 px-3 pb-3">
        <div className="space-y-2">
          {chats.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] p-4 text-sm text-gray-400">
              Henüz sohbet bulunmuyor.
            </div>
          ) : (
            chats.map((chat) => {
              const isSelected = selectedChatId === chat.id;
              const isEditing = editingChatId === chat.id;

              return (
                <div
                  key={chat.id}
                  className={`relative w-full rounded-2xl border px-3 py-3 transition-all ${
                    isSelected
                      ? "border-cyan-400/30 bg-cyan-400/10 shadow-lg shadow-cyan-500/5"
                      : "border-transparent bg-white/[0.03] hover:border-white/10 hover:bg-white/[0.06]"
                  }`}
                >
                  {!isEditing && (
                    <div className="absolute right-3 top-3 z-10 flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditing(chat.id, chat.title);
                        }}
                        className="rounded-lg p-2 text-gray-400 hover:bg-white/10 hover:text-cyan-300"
                        title="Yeniden adlandır"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleDelete(chat.id);
                        }}
                        className="rounded-lg p-2 text-gray-400 hover:bg-white/10 hover:text-red-400"
                        title="Sil"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  )}

                  <button
                    onClick={() => onSelectChat(chat.id)}
                    className="w-full text-left"
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
                          isSelected
                            ? "bg-cyan-400/20 text-cyan-300"
                            : "bg-white/5 text-gray-400"
                        }`}
                      >
                        <MessageSquare className="h-4 w-4" />
                      </div>

                      <div className="min-w-0 flex-1 pr-20">
                        {isEditing ? (
                          <div className="space-y-2">
                            <input
                              value={editedTitle}
                              onChange={(e) => setEditedTitle(e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-sm text-white outline-none focus:border-cyan-400/40"
                              autoFocus
                            />
                            <div className="flex items-center gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  void saveEditing(chat.id);
                                }}
                                className="rounded-md p-1 text-emerald-300 hover:bg-white/10"
                                title="Kaydet"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  cancelEditing();
                                }}
                                className="rounded-md p-1 text-red-300 hover:bg-white/10"
                                title="İptal"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <p
                              className={`truncate text-sm font-medium ${
                                isSelected ? "text-white" : "text-gray-200"
                              }`}
                            >
                              {chat.title}
                            </p>
                            <p className="mt-1 truncate text-xs text-gray-400">
                              {chat.lastMessage || ""}
                            </p>
                            <p className="mt-2 text-[11px] text-gray-500">
                              {chat.timestamp}
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                  </button>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}