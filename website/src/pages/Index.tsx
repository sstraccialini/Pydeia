import { Sidebar } from "@/components/Sidebar";
import { EmptyState } from "@/components/EmptyState";
import { ConversationView } from "@/components/ConversationView";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface Message {
  id: number;
  text: string;
  sender: "user" | "ai";
}

const API_BASE_URL = "http://localhost:5002/api";

const Index = () => {
  const navigate = useNavigate();
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isGeneratingResults, setIsGeneratingResults] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [prosCons, setProsCons] = useState<any>(null);
  
  const recognitionRef = useRef<any>(null);

  // Initialize speech recognition
  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
      };

      recognition.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log('Transcript:', transcript);
        setIsListening(false);
        
        await getNextQuestion(transcript);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        // Don't auto-restart on error, let the normal flow handle it
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      return true;
    }
    return false;
  };

  const startListening = () => {
    if (!isConversationActive || isSpeaking) return;
    
    try {
      recognitionRef.current?.start();
      console.log('Starting speech recognition...');
    } catch (e) {
      console.log('Recognition already started');
    }
  };

  const stopListening = () => {
    setIsListening(false);
    
    try {
      recognitionRef.current?.stop();
    } catch (e) {
      console.log('Recognition already stopped');
    }
  };

  const handleStartListening = () => {
    if (!isConversationActive || isSpeaking || isThinking) return;
    
    try {
      recognitionRef.current?.start();
      console.log('Starting to listen for answer...');
    } catch (e) {
      console.error('Failed to start listening:', e);
    }
  };

  const getNextQuestion = async (response: string = '') => {
    setIsThinking(true);
    
    try {
      const res = await fetch(`${API_BASE_URL}/get_question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response })
      });
      
      const data = await res.json();
      setCurrentQuestion(data.question);
      setMessages(data.messages || []);
      setIsThinking(false);
      setIsInitializing(false); // Deactivate loading state once question is loaded
      
      // Show loading screen when results generation starts
      if (data.generating_results) {
        setIsGeneratingResults(true);
        setIsConversationActive(false);
        stopListening();
        
        // Speak the transition message
        await speakText(data.question);
        
        // Call generate_results endpoint to get the actual results
        try {
          const resultsRes = await fetch(`${API_BASE_URL}/generate_results`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          
          const resultsData = await resultsRes.json();
          
          if (resultsData.complete) {
            setIsComplete(true);
            
            // Store recommendations and pros/cons
            let parsedProsCons = null;
            
            if (resultsData.recommendations) {
              setRecommendations(resultsData.recommendations);
              console.log('University Recommendations:', resultsData.recommendations);
            }
            if (resultsData.pros_cons) {
              // Handle both plain JSON and markdown-wrapped JSON
              parsedProsCons = resultsData.pros_cons;
              if (typeof resultsData.pros_cons === 'string') {
                // Remove markdown code blocks if present
                const cleanJson = resultsData.pros_cons.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
                try {
                  parsedProsCons = JSON.parse(cleanJson);
                } catch (e) {
                  console.error('Failed to parse pros_cons:', e);
                  parsedProsCons = resultsData.pros_cons;
                }
              }
              setProsCons(parsedProsCons);
              console.log('Pros & Cons Analysis:', parsedProsCons);
            }
            
            // Navigate to results page with data
            navigate('/results', {
              state: {
                recommendations: resultsData.recommendations,
                prosCons: parsedProsCons,
                weights: resultsData.weights
              }
            });
          }
        } catch (error) {
          console.error('Error generating results:', error);
          setIsGeneratingResults(false);
        }
        
        return;
      }
      
      if (data.complete) {
        setIsComplete(true);
        setIsConversationActive(false);
        stopListening();
        
        // Store recommendations and pros/cons
        let parsedProsCons = null;
        
        if (data.recommendations) {
          setRecommendations(data.recommendations);
          console.log('University Recommendations:', data.recommendations);
        }
        if (data.pros_cons) {
          // Handle both plain JSON and markdown-wrapped JSON
          parsedProsCons = data.pros_cons;
          if (typeof data.pros_cons === 'string') {
            // Remove markdown code blocks if present
            const cleanJson = data.pros_cons.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
            try {
              parsedProsCons = JSON.parse(cleanJson);
            } catch (e) {
              console.error('Failed to parse pros_cons:', e);
              parsedProsCons = data.pros_cons;
            }
          }
          setProsCons(parsedProsCons);
          console.log('Pros & Cons Analysis:', parsedProsCons);
        }
        
        // Navigate to results page with data
        navigate('/results', {
          state: {
            recommendations: data.recommendations,
            prosCons: parsedProsCons,
            weights: data.weights
          }
        });
        
        return;
      }
      
      // Speak the question
      await speakText(data.question);
      
    } catch (error) {
      console.error('Error:', error);
      setIsThinking(false);
      setIsConversationActive(false);
    }
  };

  const speakText = async (text: string) => {
    setIsSpeaking(true);
    
    try {
      const res = await fetch(`${API_BASE_URL}/text_to_speech`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      if (!res.ok) throw new Error('TTS failed');
      
      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      await audio.play();
      
      await new Promise(resolve => {
        audio.onended = resolve;
      });
      
      setIsSpeaking(false);
    } catch (error) {
      console.error('TTS Error:', error);
      setIsSpeaking(false);
    }
  };

  const handleStartTalking = async () => {
    if (!initializeSpeechRecognition()) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    setIsInitializing(true);

    // Reset conversation first
    try {
      await fetch(`${API_BASE_URL}/reset`, { method: 'POST' });
      setMessages([]);
    } catch (e) {
      console.error('Failed to reset:', e);
    }

    // Initialize with test data
    try {
      await fetch(`${API_BASE_URL}/initialize`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to initialize:', e);
    }

    setIsConversationActive(true);
    
    // Get the first question
    await getNextQuestion('');
  };

  const handleStopTalking = async () => {
    // Don't allow stopping if results are being generated
    if (isGeneratingResults) {
      return;
    }
    
    setIsConversationActive(false);
    stopListening();
    
    // Reset conversation
    try {
      await fetch(`${API_BASE_URL}/reset`, { method: 'POST' });
      setMessages([]);
      setCurrentQuestion('');
      setIsComplete(false);
      setRecommendations(null);
      setProsCons(null);
    } catch (error) {
      console.error('Reset error:', error);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <Sidebar messages={messages} />
      
      <main className="flex-1 flex flex-col">
        {!isConversationActive && !isComplete && !isGeneratingResults && !isInitializing ? (
          <EmptyState onStartTalking={handleStartTalking} />
        ) : isInitializing ? (
          <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-midnight-navy/5 via-parchment to-muted-gold/5">
            <div className="text-center space-y-6">
              <div className="relative w-20 h-20 mx-auto">
                <div className="absolute inset-0 border-4 border-muted-gold/20 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-muted-gold border-t-transparent rounded-full animate-spin"></div>
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-serif text-midnight-navy">
                  Preparing your session...
                </h2>
                <p className="text-muted-gold">
                  Just a moment
                </p>
              </div>
            </div>
          </div>
        ) : isGeneratingResults ? (
          <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-midnight-navy via-midnight-navy/95 to-muted-gold/20">
            <div className="text-center space-y-8 p-12">
              <div className="relative">
                {/* Animated building icon */}
                <div className="w-32 h-32 mx-auto mb-8 relative">
                  {/* Foundation */}
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-28 h-2 bg-muted-gold/30 rounded-full blur-sm"></div>
                  
                  {/* Building blocks animating upward */}
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-20 space-y-1">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="h-4 bg-muted-gold rounded animate-buildUp"
                        style={{
                          animationDelay: `${i * 0.2}s`,
                          opacity: 0,
                        }}
                      />
                    ))}
                  </div>
                  
                  {/* Sparkles */}
                  <div className="absolute top-0 left-0 w-full h-full">
                    {[...Array(6)].map((_, i) => (
                      <div
                        key={i}
                        className="absolute w-2 h-2 bg-white rounded-full animate-sparkle"
                        style={{
                          top: `${Math.random() * 100}%`,
                          left: `${Math.random() * 100}%`,
                          animationDelay: `${Math.random() * 2}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h2 className="text-4xl font-serif text-white">
                  Elaborating Your Results
                </h2>
                <p className="text-xl text-muted-gold/90">
                  Hold tight! We're crafting your personalized recommendations...
                </p>
                
                {/* Progress dots */}
                <div className="flex justify-center gap-2 pt-4">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-3 h-3 bg-muted-gold rounded-full animate-bounce"
                      style={{
                        animationDelay: `${i * 0.2}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : isComplete && recommendations ? (
          <div className="flex-1 overflow-auto p-8 bg-gray-50">
            <div className="max-w-6xl mx-auto space-y-8">
              <div className="text-center mb-12">
                <h1 className="text-5xl font-serif text-midnight-navy mb-4">Your University Recommendations</h1>
                <p className="text-gray-600">Based on your preferences and profile</p>
              </div>
              
              {/* Display universities - recommendations is array with pairs [info, scores] */}
              {Array.isArray(recommendations) && recommendations.reduce((acc: any[], item: any, index: number) => {
                if (index % 2 === 0 && recommendations[index + 1]) {
                  const uniInfo = item;
                  const uniScores = recommendations[index + 1];
                  const key = index === 0 ? 'A' : index === 2 ? 'B' : 'C';
                  
                  acc.push(
                    <div key={index} className="bg-white rounded-2xl shadow-xl p-8 border-2 border-muted-gold/30 hover:shadow-2xl transition-all duration-300">
                      {/* Header */}
                      <div className="border-b border-gray-200 pb-6 mb-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h2 className="text-3xl font-serif text-midnight-navy mb-2">{uniInfo.university_name}</h2>
                            <p className="text-xl text-muted-gold font-medium mb-1">{uniInfo.degree_name}</p>
                            <p className="text-gray-600">{uniInfo.city}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-4xl font-bold text-muted-gold mb-1">
                              {((uniScores.final_score || 0) * 100).toFixed(0)}%
                            </div>
                            <div className="text-sm text-gray-500">Match Score</div>
                          </div>
                        </div>
                      </div>

                      {/* Academic Profile */}
                      <div className="mb-6">
                        <h3 className="font-semibold text-midnight-navy mb-2 flex items-center">
                          <span className="text-2xl mr-2">🎓</span>
                          Academic Focus
                        </h3>
                        <p className="text-gray-700 ml-8">{uniInfo.academic_profile}</p>
                      </div>

                      {/* Key Info Grid */}
                      <div className="grid md:grid-cols-3 gap-4 mb-6">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500 mb-1">Annual Cost</div>
                          <div className="text-lg font-semibold text-midnight-navy">
                            €{uniInfo.annual_cost?.toLocaleString() || '0'}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500 mb-1">Distance</div>
                          <div className="text-lg font-semibold text-midnight-navy">
                            {uniScores.distance_km || 'N/A'} km
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500 mb-1">Admission Test</div>
                          <div className="text-lg font-semibold text-midnight-navy">
                            {uniInfo.admission_test_required ? 'Required' : 'Not Required'}
                          </div>
                        </div>
                      </div>

                      {/* Pros & Cons */}
                      {prosCons && prosCons[key] && (
                        <div className="grid md:grid-cols-2 gap-6 pt-6 border-t border-gray-200">
                          <div>
                            <h3 className="font-semibold text-green-700 mb-3 flex items-center text-lg">
                              <span className="mr-2">✓</span> Strengths
                            </h3>
                            <ul className="space-y-2">
                              {prosCons[key].pro.map((pro: string, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start">
                                  <span className="text-green-600 mr-2 mt-0.5">•</span>
                                  <span>{pro}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h3 className="font-semibold text-red-700 mb-3 flex items-center text-lg">
                              <span className="mr-2">✗</span> Considerations
                            </h3>
                            <ul className="space-y-2">
                              {prosCons[key].con.map((con: string, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700 flex items-start">
                                  <span className="text-red-600 mr-2 mt-0.5">•</span>
                                  <span>{con}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}

                      {/* Score Details */}
                      <div className="mt-6 pt-6 border-t border-gray-200">
                        <details className="cursor-pointer">
                          <summary className="font-semibold text-midnight-navy hover:text-muted-gold transition-colors">
                            View Detailed Scores
                          </summary>
                          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                            <div className="text-sm">
                              <span className="text-gray-500">Academic:</span>
                              <span className="ml-2 font-semibold">{((uniScores.academic || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">Aspiration:</span>
                              <span className="ml-2 font-semibold">{((uniScores.aspiration || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">Lifestyle:</span>
                              <span className="ml-2 font-semibold">{((uniScores.lifestyle || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">Budget:</span>
                              <span className="ml-2 font-semibold">{((uniScores.budget || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">Geography:</span>
                              <span className="ml-2 font-semibold">{((uniScores.geography || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="text-sm">
                              <span className="text-gray-500">Prestige:</span>
                              <span className="ml-2 font-semibold">{uniInfo.prestige_ranking || 'N/A'}</span>
                            </div>
                          </div>
                        </details>
                      </div>
                    </div>
                  );
                }
                return acc;
              }, [])}
              
              <div className="text-center pt-8">
                <button
                  onClick={handleStopTalking}
                  className="px-12 py-4 bg-midnight-navy text-white rounded-xl hover:bg-midnight-navy/90 transition-all duration-300 shadow-lg hover:shadow-xl text-lg font-medium"
                >
                  Start New Conversation
                </button>
              </div>
            </div>
          </div>
        ) : (
          <ConversationView 
            currentQuestion={currentQuestion}
            isListening={isListening}
            isSpeaking={isSpeaking}
            isThinking={isThinking}
            onStopTalking={handleStopTalking}
            onStartListening={handleStartListening}
          />
        )}
      </main>
    </div>
  );
};

export default Index;
