from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
from typing import Optional, List, Union
from pydantic import BaseModel
from datapizza.clients.openai import OpenAIClient
from datapizza.agents import Agent
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock
from datapizza.tools import tool
from elevenlabs import ElevenLabs
import ast
from recommendation_system import recommend_universities

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============== SHARED MEMORY ==============
memory = Memory()

# ============== CLIENT ==============
client = OpenAIClient(
    api_key="",                                             # INSERT YOUR OPENAI API KEY HERE
    model="gpt-5.1",
)

# ============== ELEVENLABS CLIENT ==============
elevenlabs_client = ElevenLabs(
    api_key=""                                              # INSERT YOUR ELEVENLABS API KEY HERE
)

# ============== STUDENT DATA MODEL ==============
class Info(BaseModel):
    academic_profile: Optional[str] = None
    aspiration_values: Optional[str] = None
    lifestyle_preferences: Optional[str] = None
    budget: Optional[int] = None
    origin: Optional[str] = None          # better None than '' for consistency checks
    location: Optional[str] = ''
    gpa: Optional[float] = None
    max_distance: Optional[float] = None
    far_from_home: Optional[bool] = None
    english_language: Optional[bool] = None
    dorms_nearby: Optional[bool] = None
    admission_test: Optional[bool] = None

# Message history for sidebar
class Message(BaseModel):
    id: int
    text: str
    sender: str  # "user" or "ai"

# Global state
current_info = Info()
message_history: List[Message] = []
message_counter = 0

# example text -- THIS IS JUST FOR PITCHING. SET IT TO AN EMPTY STRING TO START FRESH IN PRODUCTION
text_ =  ("I'm from Perugia, and after high school I'd like to move to another city, at maximum 400-500 km from home. The idea of staying in a dorm or a university residence appeals to me a lot. I don't mind taking an admission test if required, and I'm also fine with attending courses in English. My current GPA is around 8.0 out of 10. I would love to study in a lively city with a lot of energy and things to do.")

# ============== SYSTEM PROMPT FOR EXTRACTION ==============
EXTRACTION_SYSTEM_PROMPT = """
THE TEXT YOU ARE GOING TO INFERE DATA FROM, IS TRASCRIPTED FROM SPEECH, ACT ACCORDINGLY, TAKING YOUR TIME TO
TRY AND DISCARD NOISE AS A FIRST STEP, AND JUST THEN SEARCH FOR THE DATA YOU NEED
You are a university guidance agent.
You must remember that the context is only Italy. Do not ask about foreign countries.
Given a text (spoken or written) by a high school student,
you must FILL an object with the following fields (Pydantic model 'Info'):

- academic_profile: what the student is more inclined / interested to study. They MUST be school subjects
  (e.g. "Computer Science, Engineering" or "NO: Medicine, Law")
- aspiration_values: how motivated / serious / proactive the student is
  (e.g. "very motivated, disciplined" or "not very motivated, lazy")
- lifestyle_preferences: desired lifestyle
  (e.g. "party-oriented, sporty" or "calm, studious")

- budget: yearly budget in euros if explicitly stated or reasonably deducible (otherwise None)
- origin: city of origin (if never mentioned, leave as None)
- location: Italian city or area where they would like to study.
  If the student has NO preference, or says they are indifferent, or says that many cities are fine,
  then set location = "all".
  Use None ONLY if the text is unclear and it is not possible to deduce anything.
- gpa: school average on a 0–10 scale (if not specified, None)
- max_distance: maximum acceptable distance in km from the origin city, if deducible

- far_from_home: if the student wants to go far from home (live away from family),
                 or if they prefer to stay close; if no information is given in this instance, keep this as it is
- english_language: if they are open to English-taught courses (if stated explicitly),
                    or if they say they DO NOT want English; if no information is given in this instance, keep this as it is
- dorms_nearby: whether they care about university dorms / residences
- admission_test: whether they are available to take an admission test,
                  or if they reject tests; if no information is given in this instance, keep this as it is

VERY IMPORTANT:
- Do NOT make up values.
- Leave fields as they are if the text does NOT specify them or is not clear enough.
- You will receive multiple messages from the same person over time. Each time, fill in only
  what you can deduce from THAT specific message.
"""

QUESTION_PROMPT = """
You are an agent whose task is to generate questions about a student who is 
choosing which university to attend.
You will receive, through a class instance, the data collected so far from a 
high school student who is trying to understand which university to choose.
It is very important that you remember this is a conversation, so keep in mind the information
you already have, and do not ask again about things you already know.
Threat it as a continuous and fluent dialogue.

Your task is to ask questions related to the fields that are still None in the class,
so that another agent can finish filling the class.

Below you have the list of variables so you understand what to ask about.
The output MUST be a single question related to one or more missing categories,
where you also ask about how important that aspect is in the final decision.
Try to ask relevant but not boring questions,
that can lead to extracting the needed data without asking it in an overly direct/technical way.
Remember that this is a high-school student who probably does not know well what they want to study yet and does not know what questions to expect.
If to fill one field you need to ask about it more than once, try to completely rephrase the question without repeating yourself,
and do not obsess over precise numbers: a range is fine and later we can average.
You must try to create a chat where, by the end, you understand the relative importance 
of the different fields for the student and their strong priorities. If you try to ask and they cannot express
how important something is, it is not a problem; in that case, keep focusing on other missing categories.
You must remember the context is only Italy. Do not ask about studying abroad.

ATTENTION (VERY IMPORTANT RULES):
- You must ALWAYS and ONLY use the fields that are still None to decide what to ask about.
- Do NOT keep asking about the academic profile (academic_profile) if, in the dictionary you receive,
  this field is NOT None and already contains one or more subjects (e.g. "Drawing, Music").
  In that case, consider the academic profile SUFFICIENTLY COVERED and move on to other missing fields.
- Avoid repeatedly asking whether there are "other subjects" or "other options"
  when academic_profile is already filled: instead focus on values, lifestyle, budget, distance, etc.
- Do NOT ask questions that already know about.
- DO reply concisely and in a friendly way without unnecessary repetitions. Be friendly and agree on the last answer you received.
- You MUST always reply in ENGLISH.

# SEMANTIC FIELDS (to be filled based on the sentiment/content of the text)
1. ACADEMIC PROFILE:
   try to extract from the information given what the student is more inclined to study. This field must be prioritized if empty. This field must contain school subjects.
   "academic_profile": str
   EXAMPLE: "I like Computer Science, Engineering" or "I don't like Medicine, Law"

2. VALUES AND ASPIRATIONS:
   understand how motivated and willing the student is to commit seriously (or not) to university studies.
   "aspiration_values": str
   EXAMPLE: "proactive, motivated" or "unmotivated, lazy"

3. LIFESTYLE AND PREFERENCES:
   what kind of life the student aspires to; would they rather go out a lot or could they study many hours per day.
   "lifestyle_preferences": str
   EXAMPLE: "party-oriented, sporty" or "reserved, studious"

# QUANTITATIVE FIELDS (to be filled with numbers)
4. BUDGET: int
   yearly budget the student is willing to spend (in €). Try to estimate it if they do not say an exact figure 
   and answer vaguely.

5. ORIGIN: str
   the city where they currently live

6. location: Italian city or area where they would like to study.
   If the student has NO preference, or says they are indifferent, or that multiple cities are fine,
   then set location = "all".
   Use None ONLY if the text is not clear and it is not possible to deduce anything.

7. GPA: float
   current school average (0–10 scale)

8. MAX_DISTANCE: float
   maximum distance in km from ORIGIN

# BOOLEAN FIELDS (to be filled with True/False)
9.  far_from_home: bool (True if they are okay with going far from home or living away, False otherwise)
10. english_language: bool (True if open to English-taught courses, False if they say they do NOT want English)
11. dorms_nearby: bool (True if they are interested in dorms/housing, False if they do not want to live there)
12. admission_test: bool (True if they are willing to take it, False otherwise)

Remember: since you will be called several times,
you must ask ONE single question at a time to the student,
gradually touching on all topics.
Never ask everything at once to a student.
"""

WEIGHT_PROMPT = """You are an agent whose task is divided into two main tasks: first thing you have to do,
is to look at memory and at stored values to assign to the following attributes a BOOLEAN VALUE: far_from_home, english_language,
dorms_nearby, admission_test.
Only after having assigned a strictly boolean value to this attributes, you have the task to
generate an array of non-negative weights 
that sum to one, for various categories. You will receive a narrative provided by a high-school 
student who is trying to understand which university to choose. 
Based on this conversation, you must assign a value (weight) between 0 and 1 
to each of the topics listed below, according to how important that topic seems 
for the student in their final decision. Below you have the list of variables
for which you must provide weights and their description. The output MUST be
a list of non-negative weights between 0 and 1 that sum to 1 (i.e. normalized).
If there are features for which you cannot understand how important they are, distribute the weights 
equally among those features.
The maximum weight for a single feature can be 0.5.

            "academic_similarity": ,       # Match with academic profile, i.e. school subjects (most important)
            "aspiration_similarity": ,     # Match with values/aspirations
            "lifestyle_similarity": ,      # Match with lifestyle

            # QUANTITATIVE SCORES 
            "cost_affordability": ,        # Cost affordability
            "distance_proximity": ,        # Distance / proximity
            "prestige_ranking": ,          # Prestige / ranking
OUTPUT FORMAT (VERY IMPORTANT):
- You must return ONLY a valid Python LIST literal of 6 floats, in the order above.
- NO backticks, NO markdown, NO ```python, NO explanation.
- Example format (just an example, not actual values):

  [0.35, 0.20, 0.10, 0.15, 0.10, 0.10]
        """

PRO_CON_PROMPT = """
You MUST answer only in ENGLISH.
You are a university comparison agent.  
You receive as input THREE dictionaries, each corresponding to a degree program (A, B and C), 
each with metadata and already computed scores.

The most important metadata are:
- academic_similarity (≈0.45)  → academic fit, contents, intellectual fit
- aspiration_similarity (≈0.25) → motivations, effort, ambitions
- lifestyle_similarity (≈0.10)  → environment, pace, social life
- cost_affordability (≈0.08)    → economic sustainability
- distance_proximity (≈0.04)    → closeness/farness from home
- prestige_ranking (≈0.05)      → prestige and reputation
- employment_rate (≈0.02)       → job outcomes

Your task is:
1. Compare the three degree options A, B and C.
2. For EACH degree, generate a list with:
   - 3 PROS
   - 3 CONS
3. The pros/cons must be:
   • relevant to the data provided in the dictionaries  
   • coherent with the meaning of the metadata (without naming them technically)  
   • related to the REAL differences between A, B and C  
     (you CANNOT write identical pros/cons across all three options)  
   • truly comparative: each point must imply an advantage or disadvantage 
     with respect to the other two degrees.

────────────────────────────────────────
GENERATION RULES
────────────────────────────────────────

• Do NOT invent values that are not derived from the dictionaries.  
• Avoid vague or generic points: each pro/con must be based on a concrete difference.  
• The heaviest differences concern:  
   – academic profile fit (very important)  
   – aspirations/objectives (very important)  
   – lifestyle (relevant)  
• Cost, distance, job outcomes and ranking are important but secondary: use them only if they are actually distinctive.  
• Each list MUST be unique: if a point holds for two degrees, express it differently and in a comparative way.  
• Do not add text outside the required schema.

────────────────────────────────────────
MANDATORY OUTPUT
────────────────────────────────────────

You must return ONLY this JSON:

{
  "A": {
    "pro": ["...", "...", "..."],
    "con": ["...", "...", "..."]
  },
  "B": {
    "pro": ["...", "...", "..."],
    "con": ["...", "...", "..."]
  },
  "C": {
    "pro": ["...", "...", "..."],
    "con": ["...", "...", "..."]
  }
}

Each degree must have exactly 3 pros and 3 cons.  
Each pro/con must be truly comparative and consistent with the data and metadata.
"""

# ============== AGENT FOR FOLLOW-UP QUESTIONS ==============
question_agent = Agent(
    name="questions",
    client=client,
    system_prompt=QUESTION_PROMPT,
    memory=memory,  # use shared memory
)

@tool
def get_list(l):
    return l

pro_con = Agent(
    name='eval',
    client=client,
    tools=[get_list],
    system_prompt=PRO_CON_PROMPT
)

# ============== UTILS ==============

def extract_info(text: str, memory_obj: Union[Memory, None] = None) -> Info:
    response = client.structured_response(
        input=f"Student text: {text}",
        output_cls=Info,
        memory=memory_obj,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
    )

    if memory_obj is not None:
        memory_obj.add_turn(
            TextBlock(content=text, type="input_text"),
            role=ROLE.USER,
        )
        memory_obj.add_turn(TextBlock(content=response.text, type="output_text"), role=ROLE.ASSISTANT)

    return response.structured_data[0]

def has_none(model: BaseModel) -> bool:
    """Returns True if at least one field is None."""
    return any(value is None for value in model.model_dump().values())

def merge_info(base: Info, new: Info) -> Info:
    """Merges two Info objects"""
    base_d = base.model_dump()
    new_d = new.model_dump()
    merged = {
        key: (new_d[key] if new_d[key] is not None else base_d[key])
        for key in base_d.keys()
    }
    return Info(**merged)

@app.route('/api/get_question', methods=['POST'])
def get_question():
    """Get the next question from the AI agent"""
    global current_info, message_history, message_counter
    
    try:
        data = request.json
        user_response = data.get('response', '')
    
        # If there's a user response, process it
        if user_response:
            # Add user message to history
            message_counter += 1
            message_history.append(Message(
                id=message_counter,
                text=user_response,
                sender="user"
            ))
            
            new_info = extract_info(
                f"Student's answer: {user_response}\nCurrent state: {current_info.model_dump()}",
                memory_obj=memory
            )
            current_info = merge_info(current_info, new_info)
            
            print("\n" + "="*50)
            print("CURRENT INFO AFTER UPDATE:")
            print("="*50)
            for field, value in current_info.model_dump().items():
                print(f"{field}: {value}")
            print("="*50 + "\n")
        
        # Check if we're done
        if not has_none(current_info):
            print("\n" + "="*50)
            print("PROFILE COMPLETE - GENERATING RECOMMENDATIONS")
            print("="*50)
            
            # Send early response to trigger loading screen
            message_counter += 1
            message_history.append(Message(
                id=message_counter,
                text="Perfect! Let me analyze your profile and find the best universities for you...",
                sender="ai"
            ))
            
            return jsonify({
                'question': "Perfect! Let me analyze your profile and find the best universities for you...",
                'messages': [msg.model_dump() for msg in message_history],
                'complete': False,
                'generating_results': True
            })
        
        # Get next question (this code runs if profile is NOT complete)
        q_resp = question_agent.run(
            f"Current state of Info object: {current_info.model_dump()}"
        )
        question = q_resp.text
        
        # Add AI question to history
        message_counter += 1
        message_history.append(Message(
            id=message_counter,
            text=question,
            sender="ai"
        ))
        
        return jsonify({
            'question': question,
            'complete': False,
            'profile': current_info.model_dump(),
            'messages': [msg.model_dump() for msg in message_history]
        })
        
    except Exception as e:
        print(f"\nERROR IN GET_QUESTION: {repr(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Separate endpoint to generate results (called automatically by frontend after loading screen)
@app.route('/api/generate_results', methods=['POST'])
def generate_results():
    global current_info, message_history, message_counter
    
    if has_none(current_info):
        return jsonify({'error': 'Profile not complete'}), 400
    
    try:
        # Generate weights
        weights_agent = Agent(
            name="weighter",
            client=client,
            system_prompt=WEIGHT_PROMPT,
            memory=memory,
        )
        
        weights_response = weights_agent.run(
            f"Final student profile (Info): {current_info.model_dump()}"
        )
        
        print("\nWEIGHTS ESTIMATED BY THE MODEL:")
        print(weights_response.text)
        
        # Parse weights
        raw_weights = weights_response.text.strip()
        weights_list = ast.literal_eval(raw_weights)
        
        if not isinstance(weights_list, list) or len(weights_list) != 6:
            raise ValueError(f"Unexpected weights format: {weights_list}")
        
        weights_dict = {
            "academic_similarity":  weights_list[0],
            "aspiration_similarity": weights_list[1],
            "lifestyle_similarity":  weights_list[2],
            "budget_score":          weights_list[3],
            "geography_fit":         weights_list[4],
            "bool":                  weights_list[5],
        }
        
        # Build student profile
        student_profile = current_info.model_dump()
        student_profile["weights"] = weights_dict
        
        print("\nSTUDENT PROFILE:")
        print(student_profile)
        
        # Get university recommendations
        print("\nCALLING RECOMMENDER...")
        list_dict = recommend_universities(student_profile)
        
        print("\nRECOMMENDATIONS:")
        print(list_dict)
        
        # Generate pros/cons
        print("\nGENERATING PROS/CONS...")
        pro_con_response = pro_con.run(f"Degree options: {list_dict}")
        
        print("\nPROS/CONS ANALYSIS:")
        print(pro_con_response.text)
        
        # Parse pro_con response
        import json
        try:
            pros_cons = json.loads(pro_con_response.text)
        except:
            pros_cons = pro_con_response.text
        
        final_message = 'Thank you! I have all the information I need. Here are your personalized university recommendations!'
        message_counter += 1
        message_history.append(Message(
            id=message_counter,
            text=final_message,
            sender="ai"
        ))
        
        return jsonify({
            'question': final_message,
            'complete': True,
            'profile': current_info.model_dump(),
            'recommendations': list_dict,
            'pros_cons': pros_cons,
            'weights': weights_dict,
            'messages': [msg.model_dump() for msg in message_history]
        })
        
    except Exception as e:
        print(f"\nERROR DURING RECOMMENDATION: {repr(e)}")
        import traceback
        traceback.print_exc()
        
        final_message = 'Thank you! I have all the information I need. Your profile is complete!'
        message_counter += 1
        message_history.append(Message(
            id=message_counter,
            text=final_message,
            sender="ai"
        ))
        
        return jsonify({
            'question': final_message,
            'complete': True,
            'profile': current_info.model_dump(),
            'error': str(e),
            'messages': [msg.model_dump() for msg in message_history]
        })
    
    # Get next question (this code runs if profile is NOT complete)
    q_resp = question_agent.run(
        f"Current state of Info object: {current_info.model_dump()}"
    )
    question = q_resp.text
    
    # Add AI question to history
    message_counter += 1
    message_history.append(Message(
        id=message_counter,
        text=question,
        sender="ai"
    ))
    
@app.route('/api/text_to_speech', methods=['POST'])
def text_to_speech_api():
    """Convert text to speech using ElevenLabs"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Use the correct ElevenLabs SDK method: text_to_speech.convert()
        audio_generator = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id="cgSgspJ2msm6clMCkdW9",  # Jessica voice
            model_id="eleven_turbo_v2_5"  # Free tier model (turbo v2.5)
        )
        
        # Convert generator to bytes
        audio_bytes = b"".join(audio_generator)
        
        # Return audio file
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/mpeg',
            as_attachment=False
        )
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation"""
    global current_info, memory, message_history, message_counter
    current_info = Info()
    memory = Memory()
    message_history = []
    message_counter = 0
    return jsonify({'success': True})

@app.route('/api/initialize', methods=['POST'])
def initialize():
    global current_info, message_history, message_counter
    try:
        # Extract initial information from test data
        new_info = extract_info(text_, memory)
        current_info = merge_info(current_info, new_info)
        
        print("\n" + "="*50)
        print("INITIALIZATION - INFO EXTRACTED:")
        print("="*50)
        for field, value in current_info.model_dump().items():
            print(f"{field}: {value}")
        print("="*50 + "\n")
        
        return jsonify({"status": "initialized"})
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all messages in the conversation"""
    return jsonify({
        'messages': [msg.model_dump() for msg in message_history]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
