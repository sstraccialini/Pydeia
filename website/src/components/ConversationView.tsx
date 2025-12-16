import microphoneIcon from "@/assets/microphone-icon.png";
import { Button } from "./ui/button";
import { MicOff, ArrowRight } from "lucide-react";
import { useEffect, useRef } from "react";

interface ConversationViewProps {
  currentQuestion: string;
  isListening: boolean;
  isSpeaking: boolean;
  isThinking: boolean;
  onStopTalking: () => void;
  onStartListening: () => void;
}

export const ConversationView = ({ 
  currentQuestion, 
  isListening, 
  isSpeaking,
  isThinking,
  onStopTalking,
  onStartListening
}: ConversationViewProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [currentQuestion]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && !isListening && !isSpeaking && !isThinking) {
        onStartListening();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isListening, isSpeaking, isThinking, onStartListening]);

  const getStatusText = () => {
    if (isThinking) return "Thinking...";
    if (isSpeaking) return "Talking...";
    if (isListening) return "Listening...";
    return "";
  };

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center space-y-8">
        {/* Microphone Icon - Fixed container */}
        <div className="flex justify-center h-32">
          <div className="relative">
            <img 
              src={microphoneIcon} 
              alt="Listening" 
              className={`h-32 w-32 object-contain drop-shadow-2xl transition-all duration-300 ${
                isListening || isSpeaking ? 'scale-110' : ''
              }`}
            />
            {(isListening || isSpeaking || isThinking) && (
              <div className="absolute inset-0 bg-muted-gold/20 blur-3xl rounded-full animate-pulse" />
            )}
          </div>
        </div>

        {/* Waveform Animation - Fixed height container */}
        <div className="flex items-center justify-center gap-1.5 h-16">
          {(isListening || isSpeaking) && (
            <>
              {[...Array(9)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-muted-gold rounded-full animate-wave"
                  style={{
                    animationDelay: `${i * 0.1}s`,
                    height: '8px'
                  }}
                />
              ))}
            </>
          )}
        </div>

        {/* Status Text - Fixed height container */}
        <div className="h-8 flex items-center justify-center">
          {(isListening || isSpeaking || isThinking) && (
            <p className="text-xl text-muted-gold font-medium">
              {getStatusText()}
            </p>
          )}
        </div>

        {/* Control Buttons - Fixed height container */}
        <div className="flex items-center justify-center gap-3 pt-4 h-12">
          {!isListening && !isSpeaking && !isThinking && (
            <Button 
              onClick={onStartListening}
              className="px-6 py-2 text-sm font-medium rounded-lg shadow-md hover:shadow-lg transition-all duration-300 bg-muted-gold hover:bg-gold-darker text-white"
            >
              <img src={microphoneIcon} alt="" className="h-4 w-4 mr-2 brightness-0 invert" />
              Answer
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          )}
          <Button 
            onClick={onStopTalking}
            variant="outline"
            className="px-4 py-2 text-sm font-medium rounded-lg border-2 border-red-300 text-red-600 hover:bg-red-50 hover:border-red-400 transition-all duration-300"
          >
            <MicOff className="h-4 w-4 mr-2" />
            Close Call
          </Button>
        </div>
      </div>
    </div>
  );
};
