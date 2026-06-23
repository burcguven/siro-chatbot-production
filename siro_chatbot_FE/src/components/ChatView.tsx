import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Send, Sparkles } from "lucide-react";
import { ChatMessage } from "./ChatMessage";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface ChatViewProps {
  messages: Message[];
  onSendMessage: (message: string) => void | Promise<void>;
  isLoading: boolean;
}

export function ChatView({
  messages,
  onSendMessage,
  isLoading,
}: ChatViewProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);


  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
  setInput(e.target.value);

  const textarea = e.target;
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
  }; 

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "48px";
    }

    await onSendMessage(trimmed);
  };

  

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col bg-transparent text-white">
      <ScrollArea className="flex-1">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center px-6">
            <div className="max-w-2xl text-center">
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-400 to-emerald-400 shadow-2xl shadow-cyan-500/20">
                <Sparkles className="h-9 w-9 text-black" />
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-white">
                Nasıl yardımcı olabilirim?
              </h1>
              <p className="mt-3 text-sm leading-7 text-gray-400">
                İzinler, yan haklar, sigorta, bordro süreçleri ve diğer İK
                konularında sorularınızı yazabilirsiniz.
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 py-6 md:px-6">
            {messages.map((m) => (
              <ChatMessage
                key={m.id}
                role={m.role}
                content={m.content}
                timestamp={m.timestamp}
              />
            ))}

            {isLoading && (
              <div className="flex w-full justify-start">
                <div className="flex max-w-[85%] items-start gap-3 md:max-w-[75%]">
                  <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-400/15 text-cyan-300">
                    <Sparkles className="h-4 w-4" />
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 shadow-lg">
                    <div className="flex items-center gap-1">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.3s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300 [animation-delay:-0.15s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" />
                    </div>
                    <span className="mt-2 block text-[11px] text-gray-400">
                      Yanıt hazırlanıyor...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={endOfMessagesRef} />
          </div>
        )}
      </ScrollArea>

      <div className="border-t border-white/10 bg-[#0b1220]/80 px-4 py-4 backdrop-blur-md">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-end gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3 shadow-2xl shadow-black/20">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKey}
              placeholder="Siro HR Assistant'a soru sorun..."
              rows={1}
              className="min-h-[48px] max-h-40 flex-1 resize-none overflow-y-auto bg-transparent px-2 py-3 text-sm text-white placeholder:text-gray-500 focus:outline-none"
            />

            <Button
              onClick={() => void handleSend()}
              disabled={!input.trim() || isLoading}
              className="h-12 w-12 rounded-xl bg-emerald-500 p-0 text-black hover:bg-emerald-400 disabled:bg-white/10 disabled:text-gray-500"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>

          <p className="mt-3 text-center text-xs text-gray-500">
            Yanıtlar yalnızca yüklenen İK dokümanlarına dayanır.
          </p>
        </div>
      </div>
    </div>
  );
}