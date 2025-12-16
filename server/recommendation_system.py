from openai import OpenAI
from datapizza.tools import tool
import numpy as np
from typing import List, Dict, Any, Optional
import json
import csv
import math


#IMPORT ONLY RECOMMEND_UNIVERSITIES and run
# from Reccomend_Universities import recommend_universities
#recommend_universities(student_profile)


# ============= DATASET UNIVERSITÀ =============
def load_universities_from_csv(filename=r"data\universities.csv"):
    universities = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert types
                row['id'] = int(row['id'])
                row['annual_cost'] = int(row['annual_cost'])
                row['coordinates'] = json.loads(row['coordinates'])
                row['min_gpa'] = float(row['min_gpa'])
                row['prestige_rank'] = int(row['prestige_rank'])
                row['duration_years'] = int(row.get('duration_years', 3))
                row['employment_rate'] = int(row.get('employment_rate', 0))
                
                # Convert booleans
                row['english_courses'] = row['english_courses'].lower() == 'true'
                row['dorms_available'] = row['dorms_available'].lower() == 'true'
                row['admission_test_required'] = row['admission_test_required'].lower() == 'true'
                
                universities.append(row)
        print(f"Caricate {len(universities)} università da {filename}")
        return universities
    except FileNotFoundError:
        print(f"File {filename} non trovato. Uso dataset mock.")
        return []

UNIVERSITY_DATASET = load_universities_from_csv()
if not UNIVERSITY_DATASET:
    raise RuntimeError("Nessuna università caricata. Assicurarsi che 'data/universities.csv' esista.")
# ============= TOOLS PER L'AGENTE =============

@tool
def create_student_embedding(student_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea 3 EMBEDDINGS SEPARATI del profilo studente (coordinate-wise).
    Ogni campo semantico ha il suo embedding per maggiore granularità.
    Usa Ollama granite-embedding:30m per embeddings locali.
    """
    academic_text = student_profile.get('academic_profile', '') or ''
    aspiration_text = student_profile.get('aspiration_values', '') or ''
    lifestyle_text = student_profile.get('lifestyle_preferences', '') or ''

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # qualsiasi stringa
    )
    
    academic_embedding = client.embeddings.create(
        input=academic_text,
        model="granite-embedding:30m"
    ).data[0].embedding

    aspiration_embedding = client.embeddings.create(
        input=aspiration_text,
        model="granite-embedding:30m"
    ).data[0].embedding

    lifestyle_embedding = client.embeddings.create(
        input=lifestyle_text,
        model="granite-embedding:30m"
    ).data[0].embedding
    
    return {
        "student_profile": student_profile,
        "embeddings": {
            "academic": academic_embedding,
            "aspiration": aspiration_embedding,
            "lifestyle": lifestyle_embedding
        },
        "texts": {
            "academic": academic_text,
            "aspiration": aspiration_text,
            "lifestyle": lifestyle_text
        }
    }

@tool
def create_universities_embeddings(universities: List[Dict]) -> List[Dict]:
    """
    Crea 3 EMBEDDINGS SEPARATI per ogni università (coordinate-wise).
    Usa Ollama granite-embedding:30m per embeddings locali.
    """
    enriched_universities = []
    
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # qualsiasi stringa
    )
    
    for uni in universities:
        academic_text = uni.get('academic_profile', '') or ''
        aspiration_text = uni.get('aspiration_values', '') or ''
        lifestyle_text = uni.get('lifestyle_preferences', '') or ''
        
        academic_embedding = client.embeddings.create(
            input=academic_text,
            model="granite-embedding:30m"
        ).data[0].embedding

        aspiration_embedding = client.embeddings.create(
            input=aspiration_text,
            model="granite-embedding:30m"
        ).data[0].embedding

        lifestyle_embedding = client.embeddings.create(
            input=lifestyle_text,
            model="granite-embedding:30m"
        ).data[0].embedding
                
        enriched_universities.append({
            **uni,
            "embeddings": {
                "academic": academic_embedding,
                "aspiration": aspiration_embedding,
                "lifestyle": lifestyle_embedding
            },
            "texts": {
                "academic": academic_text,
                "aspiration": aspiration_text,
                "lifestyle": lifestyle_text
            }
        })
    
    return enriched_universities


@tool
def calculate_cosine_similarity(student_embeddings: Dict[str, List[float]], university_embeddings: List[Dict]) -> List[Dict]:
    """
    Calcola 3 COSINE SIMILARITIES separate (coordinate-wise):
    1. Academic similarity
    2. Aspiration similarity  
    3. Lifestyle similarity
    
    Restituisce università rankate con i 3 score separati.
    """
    student_academic = np.array(student_embeddings["academic"])
    student_aspiration = np.array(student_embeddings["aspiration"])
    student_lifestyle = np.array(student_embeddings["lifestyle"])
    
    results = []
    for uni in university_embeddings:
        uni_emb = uni["embeddings"]
        
        # 3 COSINE SIMILARITIES SEPARATE
        # 1. Academic
        uni_academic = np.array(uni_emb["academic"])
        academic_sim = np.dot(student_academic, uni_academic) / (
            np.linalg.norm(student_academic) * np.linalg.norm(uni_academic)
        )
        
        # 2. Aspiration
        uni_aspiration = np.array(uni_emb["aspiration"])
        aspiration_sim = np.dot(student_aspiration, uni_aspiration) / (
            np.linalg.norm(student_aspiration) * np.linalg.norm(uni_aspiration)
        )
        
        # 3. Lifestyle
        uni_lifestyle = np.array(uni_emb["lifestyle"])
        lifestyle_sim = np.dot(student_lifestyle, uni_lifestyle) / (
            np.linalg.norm(student_lifestyle) * np.linalg.norm(uni_lifestyle)
        )
        
        # Score aggregato (media pesata - configurabile)
        # Puoi cambiare i pesi: academic più importante?
        semantic_score_aggregated = (
            0.5 * academic_sim +      # Academic: peso maggiore
            0.3 * aspiration_sim +    # Aspiration: medio
            0.2 * lifestyle_sim       # Lifestyle: minore
        )
        
        results.append({
            "university": uni["nome"],
            "corso": uni["corso"],
            "semantic_scores": {
                "academic": float(academic_sim),
                "aspiration": float(aspiration_sim),
                "lifestyle": float(lifestyle_sim),
                "aggregated": float(semantic_score_aggregated)
            },
            "semantic_score": float(semantic_score_aggregated),  # Per compatibilità
            "details": uni
        })
    
    # Ordina per score aggregato
    results.sort(key=lambda x: x["semantic_score"], reverse=True)
    return results

@tool
def multimodal_scoring(
    filtered_universities: List[Dict], 
    student_profile: Dict[str, Any] = None,
    weights: Dict[str, float] = None
) -> List[Dict]:
    """
    MODELLO MULTIMODALE: Combina 3 score semantici + budget + geografia + booleani.
    """

    
    # PESI OTTIMIZZATI
    if weights is None:
        weights = {
            # SEMANTIC (50%)
            "academic_similarity": 0.25,
            "aspiration_similarity": 0.15,
            "lifestyle_similarity": 0.10,
            
            # QUANTITATIVE (30%)
            "budget_score": 0.15,
            "geography_fit": 0.15,
            
            # BOOLEANS (20%)
            "bool": 0.20
        }
    
    print(weights)

    scored = []
    
    for uni in filtered_universities:
        details = uni["details"]
        
        # Dati Università
        annual_cost = details.get("annual_cost", 0)
        city = details.get("city", "")
        coords = details.get("coordinates", {})
        
        # Booleani Università
        has_english = details.get("english_courses", False)
        has_dorms = details.get("dorms_available", False)
        req_test_uni = details.get("admission_test_required", False)
        
        # ==================== SEMANTIC SCORES ====================
        semantic_scores = uni.get("semantic_scores", {})
        academic_score = semantic_scores.get("academic", 0.0)
        aspiration_score = semantic_scores.get("aspiration", 0.0)
        lifestyle_score = semantic_scores.get("lifestyle", 0.0)
        
        # ==================== QUANTITATIVE SCORES ====================
        
        # 1. BUDGET
        student_budget = student_profile.get("budget", 0) if student_profile else 0
        budget_score = calculate_budget_score(student_budget, annual_cost)
        
        # 2. GEOGRAPHY
        geography_score = calculate_geography_fit(
            student_profile.get("origin", "") if student_profile else "",
            student_profile.get("location", "") if student_profile else "",
            student_profile.get("max_distance") if student_profile else None,
            student_profile.get("far_from_home", True) if student_profile else True,
            city,
            coords
        )
        
        # ==================== BOOLEAN SCORES ====================
        
        # English
        req_eng = student_profile.get("english_language", False) if student_profile else False
        english_score = 1.0 if (not req_eng or has_english) else 0.0
        
        # Dorms
        req_dorms = student_profile.get("dorms_nearby", False) if student_profile else False
        dorms_score = 1.0 if (not req_dorms or has_dorms) else 0.0
        
        # Admission Test (Se studente NON vuole test e università lo richiede -> 0)
        willing_test = student_profile.get("admission_test", True) if student_profile else True
        if willing_test:
            test_score = 1.0
        else:
            test_score = 0.0 if req_test_uni else 1.0
        
        # ==================== EQUAZIONE LINEARE ====================
        final_score = (
            weights["academic_similarity"] * academic_score +
            weights["aspiration_similarity"] * aspiration_score +
            weights["lifestyle_similarity"] * lifestyle_score +
            weights["budget_score"] * budget_score +
            weights["geography_fit"] * geography_score +
            weights["bool"]/3 * english_score +
            weights["bool"]/3 * dorms_score +
            weights["bool"]/3 * test_score
        )
        
        # Calcolo distanza per display
        distance_km = calculate_distance(
            student_profile.get("origin", "") if student_profile else "",
            city,
            coords
        )
        
        scored.append({
            **uni,
            **details, # Flatten details so all CSV columns are top-level
            "final_score": final_score,
            "score_breakdown": {
                "academic": academic_score,
                "aspiration": aspiration_score,
                "lifestyle": lifestyle_score,
                "budget": budget_score,
                "geography": geography_score,
                "english": english_score,
                "dorms": dorms_score,
                "test": test_score
            },
            "distance_km": distance_km
        })
    
    # Ranking finale
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored

# ============= HELPER FUNCTIONS =============

def calculate_distance(origin: str, city: str, coords: Dict[str, float]) -> float:
    """Calcola distanza in km tra origine studente e università"""
    # Se città coincidono, distanza 0
    if origin and city and origin.lower() == city.lower():
        return 0.0
        
    # Se abbiamo coordinate università e mock coordinate studente
    if coords:
        # Mock coordinates per città principali (in prod usare geocoding)
        city_coords_map = {
            "Milano": {"lat": 45.4773, "lon": 9.2282},
            "Bologna": {"lat": 44.4938, "lon": 11.3387},
            "Roma": {"lat": 41.8547, "lon": 12.6043},
            "Trento": {"lat": 46.0664, "lon": 11.1257},
            "Torino": {"lat": 45.0703, "lon": 7.6869},
            "Firenze": {"lat": 43.7696, "lon": 11.2558},
            "Pisa": {"lat": 43.716, "lon": 10.3966},
            "Siena": {"lat": 43.3188, "lon": 11.3308},
            "Padova": {"lat": 45.4064, "lon": 11.8768},
            "Venezia": {"lat": 45.4408, "lon": 12.3155},
            "Verona": {"lat": 45.4384, "lon": 10.9916},
            "Genova": {"lat": 44.4056, "lon": 8.9463},
            "Pavia": {"lat": 45.1847, "lon": 9.1582},
            "Bari": {"lat": 41.1171, "lon": 16.8719},
            "Lecce": {"lat": 40.352, "lon": 18.169},
            "Napoli": {"lat": 40.8518, "lon": 14.2681},
            "Salerno": {"lat": 40.6824, "lon": 14.7681},
            "Catania": {"lat": 37.5079, "lon": 15.083},
            "Palermo": {"lat": 38.1157, "lon": 13.3615},
            "Cagliari": {"lat": 39.2238, "lon": 9.1217},
            "Trieste": {"lat": 45.6495, "lon": 13.7768},
            "Perugia": {"lat": 43.1107, "lon": 12.3908},
            "L'Aquila": {"lat": 42.351, "lon": 13.3984},
            "Teramo": {"lat": 42.6612, "lon": 13.699},
            "Potenza": {"lat": 40.6395, "lon": 15.8051},
            "Rende": {"lat": 39.3579, "lon": 16.227},
            "Catanzaro": {"lat": 38.905, "lon": 16.589},
            "Reggio Calabria": {"lat": 38.1113, "lon": 15.6473},
            "Bergamo": {"lat": 45.6983, "lon": 9.6773},
            "Brescia": {"lat": 45.5416, "lon": 10.2118},
            "Bolzano": {"lat": 46.4983, "lon": 11.3548},
            "Udine": {"lat": 46.0626, "lon": 13.2349},
            "Ferrara": {"lat": 44.8381, "lon": 11.6198},
            "Modena": {"lat": 44.646, "lon": 10.9252},
            "Parma": {"lat": 44.8015, "lon": 10.3279},
            "Ancona": {"lat": 43.6158, "lon": 13.5189},
            "Urbino": {"lat": 43.7262, "lon": 12.6366},
            "Macerata": {"lat": 43.2991, "lon": 13.453},
            "Camerino": {"lat": 43.1372, "lon": 13.068},
            "Cassino": {"lat": 41.4925, "lon": 13.8281},
            "Viterbo": {"lat": 42.4207, "lon": 12.1077},
            "Campobasso": {"lat": 41.56, "lon": 14.659},
            "Benevento": {"lat": 41.129, "lon": 14.782},
            "Foggia": {"lat": 41.4622, "lon": 15.5446},
            "Messina": {"lat": 38.1938, "lon": 15.554},
            "Sassari": {"lat": 40.7275, "lon": 8.559},
            "Enna": {"lat": 37.5667, "lon": 14.2833},
            "Aversa": {"lat": 40.9722, "lon": 14.2077},
            "Novedrate": {"lat": 45.72, "lon": 9.116},
            "Rozzano": {"lat": 45.382, "lon": 9.16},
            "Castellanza": {"lat": 45.613, "lon": 8.897},
            "Bra (Pollenzo)": {"lat": 44.694, "lon": 7.935}
        }
        
        student_coords = city_coords_map.get(origin)
        
        if student_coords:
            # Formula Haversine
            from math import radians, sin, cos, sqrt, atan2
            R = 6371  # Raggio Terra in km
            
            lat1, lon1 = radians(student_coords["lat"]), radians(student_coords["lon"])
            lat2, lon2 = radians(coords["lat"]), radians(coords["lon"])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a_dist = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a_dist), sqrt(1 - a_dist))
            return R * c
            
    # Fallback se non calcolabile
    return 200.0

def calculate_geography_fit(
    origin: str, 
    target_location: str, 
    max_dist: float, 
    far_from_home: bool, 
    uni_city: str, 
    uni_coords: Dict[str, float]
) -> float:
    """Calcola score geografico (0-1)"""

    dmax = 1045.75

    dist = calculate_distance(origin, uni_city, uni_coords) / dmax
    
    if target_location:
        if target_location.lower() in uni_city.lower():
            return 1.2
    
    if max_dist and dist > max_dist:
        return 0.0
    
    if far_from_home:
        return dist
    # Score distanza standard (logaritmico)
    # Più vicino è meglio, ma decrescita lenta
    return max(0, 1 - (dist**(1/4)))

def calculate_budget_score(student_budget: int, uni_cost: int) -> float:
    """Calcola score budget (0-1)"""
    if not student_budget:
        return 1.0 # Se non ha budget limit, va bene tutto
        
    if uni_cost <= student_budget:
        return math.log(abs(student_budget - uni_cost) + 1) / math.log(student_budget + 1)
    
    else: 
        return -math.exp((uni_cost - student_budget) / student_budget)

def recommend_universities(student_profile : Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Pipeline completa con branching agentic.
    """

    
    
    # # ESEMPIO con NUOVO SCHEMA FLAT (StudentInfo)
    # student_profile = {
    #     # Campi semantici (Hardcoded per demo, idealmente estratti da student_description)
    #     "academic_profile": "Informatica, Tecnologia, Ingegneria Software",
    #     "aspiration_values": "Innovativo, imprenditoriale, orientato al futuro, voglio fondare startup",
    #     "lifestyle_preferences": "Moderato - voglio tempo per progetti personali ma anche studiare seriamente",
        
    #     # Campi quantitativi
    #     "budget": budget,
    #     "origin": "Roma",
    #     "location": None,  # Nessuna città specifica richiesta
    #     "gpa": 8.5,  # Convertito da 0-10
    #     "max_distance": max_distance,
        
    #     # Campi booleani
    #     "far_from_home": True, # Assumiamo True per demo
    #     "english_language": need_english,
    #     "dorms_nearby": need_housing,
    #     "admission_test": True,
    #     "extracurricular_activities": True
    # }
    
    # STEP 1: Crea embedding studente
    print("\n🔧 STEP 1: Creazione embedding studente...")
    student_data = create_student_embedding(student_profile)
    
    # STEP 2: Crea embeddings università
    print("\n🔧 STEP 2: Creazione embeddings università...")
    universities_data = create_universities_embeddings(UNIVERSITY_DATASET)
    
    # STEP 3: Calcola similarità semantica
    print("\n🔧 STEP 3: Calcolo similarità semantica...")
    semantic_ranking = calculate_cosine_similarity(
        student_data["embeddings"],
        universities_data
    )
    
    # STEP 4: Scoring multimodale finale (include penalizzazioni)
    final_recommendations = multimodal_scoring(
        filtered_universities=semantic_ranking,
        student_profile=student_profile,
        weights=student_profile.get("weights", None)
    )
    
    print("\n" + "="*60)
    print("🏆 TOP 3 RACCOMANDAZIONI")
    print("="*60)
    for i, uni in enumerate(final_recommendations[:3], 1):
        print(f"\n{i}. {uni['university']} - {uni['corso']}")
        print(f"   📍 Città: {uni['details']['city']}")
        print(f"   💰 Costo: €{uni['details']['annual_cost']}/anno")
        print(f"   📏 Distanza: {uni['distance_km']:.0f} km")
        print(f"   ⭐ Score finale: {uni['final_score']:.3f}")
        breakdown = uni['score_breakdown']
        print(f"   📊 Academic: {breakdown['academic']:.3f} | "
              f"Aspiration: {breakdown['aspiration']:.3f} | "
              f"Lifestyle: {breakdown['lifestyle']:.3f}")
        print(f"   💰 Budget: {breakdown['budget']:.3f} | "
              f"🌍 Geo: {breakdown['geography']:.3f}")
        print(f"   ✅ English: {breakdown['english']:.1f} | "
              f"Dorms: {breakdown['dorms']:.1f} | "
              f"Test: {breakdown['test']:.1f} | "
)
    
    print("\n" + "="*60)
    print("⚠️  FLOP 3 (Meno Consigliate)")
    print("="*60)
    for i, uni in enumerate(final_recommendations[-3:][::-1], 1):
        print(f"\n{i}. {uni['university']} - {uni['corso']}")
        print(f"   📍 Città: {uni['details']['city']}")
        print(f"   ⭐ Score finale: {uni['final_score']:.3f}")
        breakdown = uni['score_breakdown']
        print(f"   📊 Academic: {breakdown['academic']:.3f} | "
              f"Aspiration: {breakdown['aspiration']:.3f} | "
              f"Lifestyle: {breakdown['lifestyle']:.3f}")
        print(f"   💰 Budget: {breakdown['budget']:.3f} | "
              f"🌍 Geo: {breakdown['geography']:.3f}")
        print(f"   ✅ English: {breakdown['english']:.1f} | "
              f"Dorms: {breakdown['dorms']:.1f} | "
              f"Test: {breakdown['test']:.1f} | "
)
    
    result_list = []
    for uni in final_recommendations[:3]:
        # 1. Clean University details
        clean_uni = {
            "id": uni.get("id"),
            "nome": uni.get("nome"),
            "corso": uni.get("corso"),
            "city": uni.get("city"),
            "annual_cost": uni.get("annual_cost"),
            "academic_profile": uni.get("academic_profile"),
            "aspiration_values": uni.get("aspiration_values"),
            "lifestyle_preferences": uni.get("lifestyle_preferences"),
            "min_gpa": uni.get("min_gpa"),
            "prestige_rank": uni.get("prestige_rank"),
            "duration_years": uni.get("duration_years"),
            "employment_rate": uni.get("employment_rate"),
            "english_courses": uni.get("english_courses"),
            "dorms_available": uni.get("dorms_available"),
            "admission_test_required": uni.get("admission_test_required"),
            "coordinates": uni.get("coordinates")
        }
        result_list.append(clean_uni)
        
        # 2. Scores breakdown (plus final score and distance)
        scores = uni['score_breakdown'].copy()
        scores['final_score'] = uni['final_score']
        scores['distance_km'] = uni['distance_km']
        
        result_list.append(scores)
        
    return result_list



