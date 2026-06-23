import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex max-w-[85%] items-start gap-3 md:max-w-[75%] ${
          isUser ? "flex-row-reverse" : "flex-row"
        }`}
      >
        <div
          className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
            isUser
              ? "bg-emerald-500/20 text-emerald-300"
              : "bg-cyan-400/15 text-cyan-300"
          }`}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>

        <div
          className={`rounded-2xl border px-4 py-3 shadow-lg ${
            isUser
              ? "border-emerald-400/20 bg-emerald-500/10 text-white"
              : "border-white/10 bg-white/[0.04] text-gray-100"
          }`}
        >
          <p className="whitespace-pre-wrap break-words text-sm leading-7">
            {content || (role === "assistant" ? "▋" : "")}
          </p>
          <span className="mt-2 block text-[11px] text-gray-400">
            {timestamp}
          </span>
        </div>
      </div>
    </div>
  );
}