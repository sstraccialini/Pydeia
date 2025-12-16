import microphoneIcon from "@/assets/microphone-icon.png";
import { Button } from "./ui/button";
import { ArrowRight } from "lucide-react";

interface EmptyStateProps {
  onStartTalking: () => void;
}

export const EmptyState = ({ onStartTalking }: EmptyStateProps) => {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center space-y-12 animate-in fade-in duration-700">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <img 
              src={microphoneIcon} 
              alt="Pydeia" 
              className="h-32 w-32 object-contain drop-shadow-2xl"
            />
            <div className="absolute inset-0 bg-muted-gold/10 blur-3xl rounded-full" />
          </div>
        </div>

        {/* Headline */}
        <div className="space-y-6">
          <h1 className="text-5xl md:text-6xl font-serif font-bold text-foreground leading-tight">
            Where should your wisdom lead you?
          </h1>
          <p className="text-xl text-muted-foreground max-w-xl mx-auto font-light">
            Share your aspirations, and I will guide your university path.
          </p>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-center pt-4">
          <Button 
            size="lg"
            onClick={onStartTalking}
            className="bg-midnight-navy hover:bg-midnight-navy/90 text-parchment px-12 py-6 text-lg font-medium rounded-2xl shadow-elegant hover:shadow-floating transition-all duration-300 hover:scale-105"
          >
            Start Talking
            <ArrowRight className="h-6 w-6 ml-3" />
          </Button>
        </div>
      </div>
    </div>
  );
};
