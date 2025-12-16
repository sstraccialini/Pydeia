export const mockRecommendations = [
  {
    academic_profile: 'Fisica teorica, matematica, ricerca di base',
    admission_test_required: true,
    annual_cost: 0,
    aspiration_values: 'Ricerca accademica internazionale, dottorato',
    city: 'Pisa',
    degree_name: 'Laurea in Fisica - Corso Ordinario',
    employment_rate: 100,
    extracurricular_available: true,
    lifestyle_city: 'Studioso, universitario tradizionale',
    min_gpa: 9.8,
    prestige_ranking: 1,
    university_name: 'Scuola Normale Superiore di Pisa'
  },
  {
    academic: 0.7776165165098645,
    aspiration: 0.5646596374223098,
    budget: 1,
    clubs: 1,
    distance_km: 200,
    employment: 1,
    final_score: 0.7234567890123456,
    geography: 0.8,
    lifestyle: 0.65,
    prestige: 1
  },
  {
    academic_profile: 'Matematica Pura e Applicata, Statistica',
    admission_test_required: false,
    annual_cost: 2100,
    aspiration_values: 'Ricerca, data science, ruoli analitici ad alta specializzazione',
    city: 'Trieste',
    degree_name: 'Laurea Magistrale in Matematica',
    employment_rate: 85,
    extracurricular_available: true,
    lifestyle_city: 'Internazionale, vivace culturalmente',
    min_gpa: 7.5,
    prestige_ranking: 15,
    university_name: 'Università degli Studi di Trieste'
  },
  {
    academic: 0.7096122627014275,
    aspiration: 0.5711174066587278,
    budget: 0.9744099364565829,
    clubs: 1,
    distance_km: 200,
    employment: 0.85,
    final_score: 0.6890123456789012,
    geography: 0.75,
    lifestyle: 0.7,
    prestige: 0.8
  },
  {
    academic_profile: 'Fisica Teorica e Sperimentale, Astrofisica',
    admission_test_required: false,
    annual_cost: 2300,
    aspiration_values: 'Ricerca in fisica fondamentale, dottorati internazionali',
    city: 'Pisa',
    degree_name: 'Laurea Magistrale in Fisica',
    employment_rate: 85,
    extracurricular_available: true,
    lifestyle_city: 'Accademico, storico',
    min_gpa: 7.0,
    prestige_ranking: 30,
    university_name: 'Università di Pisa'
  },
  {
    academic: 0.6985025524448137,
    aspiration: 0.5564709078168542,
    budget: 0.9716262320774295,
    clubs: 1,
    distance_km: 200,
    employment: 0.85,
    final_score: 0.6678901234567890,
    geography: 0.8,
    lifestyle: 0.68,
    prestige: 0.75
  }
];

export const mockProsCons = {
  "A": {
    "pro": [
      "Offers a top-tier academic experience in theoretical physics, which is unmatched by the other options.",
      "Guaranteed 100% employment rate highlights its effectiveness in preparing students for prestigious academic positions.",
      "Located in a prestigious and elite environment that fosters high-level academic research and networking."
    ],
    "con": [
      "Requires an exceptionally high minimum GPA of 9.8, which could limit accessibility compared to the other programs.",
      "The hyper-selective admission process might discourage many potential applicants who are not academically elite.",
      "Lack of flexibility in lifestyle choices due to its exclusive and intense collegiate atmosphere."
    ]
  },
  "B": {
    "pro": [
      "Provides a balanced approach between theory and application in mathematics, appealing to those interested in diverse career options.",
      "Lower minimum GPA of 7.5 allows more applicants from varied academic backgrounds compared to the other programs.",
      "Resides in a vibrant city environment with an international atmosphere, enriching the student experience beyond academics."
    ],
    "con": [
      "Employment rate of 85% is lower than A, potentially indicating more competitive job outcomes in the field of data science.",
      "Higher annual cost compared to A, which may deter students seeking more affordable tuition options.",
      "Lacks the same level of academic prestige as A, which could impact future opportunities and networking."
    ]
  },
  "C": {
    "pro": [
      "Focus on both theoretical and experimental physics, offering a broader spectrum of knowledge than B's mathematics program.",
      "The active academic community enables passionate engagement, enhancing the overall learning experience compared to A's elite structure.",
      "Similar city location to A enhances accessibility while being less exclusive, fostering a more inclusive educational environment."
    ],
    "con": [
      "Higher annual cost than B, which may be less appealing for budget-conscious students.",
      "An employment rate of 85% aligns with B but does not meet the exceptional standards set by A.",
      "While it offers a good academic foundation, its prestige ranking at 30 is notably less competitive than A's top ranking."
    ]
  }
};

export const mockWeights = {
  academic_similarity: 0.51,
  aspiration_similarity: 0.15,
  bool: 0.05,
  budget_score: 0.12,
  geography_fit: 0.07,
  lifestyle_similarity: 0.1
};
