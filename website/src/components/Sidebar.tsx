import { Settings, User } from "lucide-react";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { ScrollArea } from "./ui/scroll-area";
import pydeiaLogo from "@/assets/pydeia-logo.png";
import { useEffect, useRef } from "react";

interface Message {
  id: number;
  text: string;
  sender: "user" | "ai";
}

interface SidebarProps {
  messages?: Message[];
}

export const Sidebar = ({ messages = [] }: SidebarProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <aside className="w-80 bg-sidebar-bg text-sidebar-fg flex flex-col h-screen border-r border-sidebar-bg">
      {/* Logo */}
      <div className="p-0 border-b border-sidebar-fg/10">
        <img src={pydeiaLogo} alt="Pydeia" className="h-22 brightness-0 invert opacity-90" />
      </div>

      {/* Conversation Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-sidebar-fg/40 text-sm py-8">
              Your conversation will appear here
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    message.sender === "user"
                      ? "bg-muted-gold/20 text-sidebar-fg rounded-br-sm"
                      : "bg-sidebar-fg/10 text-sidebar-fg/90 rounded-bl-sm"
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))
          )}
          {/* Invisible element to scroll to */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* User Profile - Compact Horizontal */}
      <div className="p-3 border-t border-sidebar-fg/10">
        <div className="flex items-center gap-3">
          <Avatar className="h-9 w-9 border border-muted-gold/30">
            <AvatarFallback className="bg-muted-gold/20 text-muted-gold text-xs">
              <User className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-sidebar-fg truncate">Mario Rossi</p>
            <p className="text-xs text-sidebar-fg/60">Active</p>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            className="h-8 w-8 shrink-0 text-sidebar-fg/60 hover:text-muted-gold hover:bg-sidebar-fg/5"
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
};
