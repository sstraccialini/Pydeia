import { useNavigate, useLocation } from "react-router-dom";
import { mockRecommendations, mockProsCons, mockWeights } from "@/data/mockResults";

export const Results = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Use location state if available, otherwise fall back to mock data
  const recommendations = location.state?.recommendations || mockRecommendations;
  const prosCons = location.state?.prosCons || mockProsCons;
  const weights = location.state?.weights || mockWeights;

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-serif text-midnight-navy mb-4">No recommendations available</h2>
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3 bg-midnight-navy text-white rounded-lg hover:bg-midnight-navy/90 transition-colors"
          >
            Start New Conversation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
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
                      <h2 className="text-3xl font-serif text-midnight-navy mb-2">{uniInfo.nome}</h2>
                      <p className="text-xl text-muted-gold font-medium mb-1">{uniInfo.corso}</p>
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

                {/* Aspirations */}
                <div className="mb-6">
                  <h3 className="font-semibold text-midnight-navy mb-2 flex items-center">
                    <span className="text-2xl mr-2">🎯</span>
                    Career Aspirations
                  </h3>
                  <p className="text-gray-700 ml-8">{uniInfo.aspiration_values}</p>
                </div>

                {/* Key Info Grid */}
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Annual Cost</div>
                    <div className="text-lg font-semibold text-midnight-navy">
                      €{uniInfo.annual_cost?.toLocaleString() || '0'}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Distance</div>
                    <div className="text-lg font-semibold text-midnight-navy">
                    {Number.isFinite(Number(uniScores.distance_km)) ? Number(uniScores.distance_km).toFixed(1) : 'N/A'} km
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Min GPA</div>
                    <div className="text-lg font-semibold text-midnight-navy">
                      {uniInfo.min_gpa || 'N/A'}/10
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Employment</div>
                    <div className="text-lg font-semibold text-midnight-navy">
                      {uniInfo.employment_rate || 'N/A'}%
                    </div>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div className="flex items-center text-sm">
                  <span className={`mr-2 ${uniInfo.admission_test_required ? 'text-amber-600' : 'text-green-600'}`}>
                    {uniInfo.admission_test_required ? '⚠️' : '✓'}
                  </span>
                  <span className="text-gray-700">
                    {uniInfo.admission_test_required ? 'Admission test required' : 'No admission test'}
                  </span>
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
                        <span className="text-gray-500">Academic Match:</span>
                        <span className="ml-2 font-semibold">{((uniScores.academic || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">Aspiration Match:</span>
                        <span className="ml-2 font-semibold">{((uniScores.aspiration || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">Lifestyle Match:</span>
                        <span className="ml-2 font-semibold">{((uniScores.lifestyle || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">Budget Fit:</span>
                        <span className="ml-2 font-semibold">{((uniScores.budget || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">Geography Score:</span>
                        <span className="ml-2 font-semibold">{((uniScores.geography || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">Prestige Rank:</span>
                        <span className="ml-2 font-semibold">#{uniInfo.prestige_ranking || 'N/A'}</span>
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
            onClick={() => navigate('/')}
            className="px-12 py-4 bg-midnight-navy text-white rounded-xl hover:bg-midnight-navy/90 transition-all duration-300 shadow-lg hover:shadow-xl text-lg font-medium"
          >
            Start New Conversation
          </button>
        </div>
      </div>
    </div>
  );
};
