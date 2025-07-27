import streamlit as st
import datetime
from datetime import timedelta
import pandas as pd
import openai
import json
import re

# Page configuration
st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for elegant styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #2E4057;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5A6C7D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2E4057;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #E8F4FD;
        padding-bottom: 0.5rem;
    }
    .preference-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .result-card {
        background: #F8FFFE;
        border: 1px solid #E1F5FE;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .recommendation-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1976D2;
        margin-bottom: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .activity-item {
        background: #E3F2FD;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1976D2;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'preferences_collected' not in st.session_state:
    st.session_state.preferences_collected = False
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None

# OpenAI Configuration
def setup_openai():
    """Setup OpenAI API key from user input or environment"""
    openai_api_key = st.sidebar.text_input(
        "🔑 OpenAI API Key", 
        type="password",
        help="Enter your OpenAI API key to generate AI-powered recommendations"
    )
    
    if openai_api_key:
        openai.api_key = openai_api_key
        return True
    else:
        st.sidebar.warning("⚠️ Please enter your OpenAI API key to use AI recommendations")
        return False

def generate_travel_itinerary(preferences, model="gpt-3.5-turbo", temperature=0.7):
    """Generate travel itinerary using OpenAI"""
    try:
        # Create detailed prompt
        interests_str = ", ".join(preferences['interests']) if preferences['interests'] else "general sightseeing"
        
        prompt = f"""
        You are a professional travel assistant with extensive knowledge of global destinations, flight routes, hotels, and local attractions. Create a detailed and realistic travel itinerary based on these preferences:

        **Trip Details:**
        - Destination: {preferences['destination']}
        - Origin: {preferences['origin']}
        - Duration: {preferences['duration']} days
        - Dates: {preferences['start_date']} to {preferences['end_date']}
        - Travelers: {preferences['travelers']}

        **Budget & Accommodation:**
        - Flight budget: ${preferences['flight_budget']} total
        - Hotel budget: ${preferences['hotel_budget']} per night
        - Accommodation type: {preferences['accommodation_type']}
        - Location preference: {preferences['location_preference'] or 'city center'}

        **Interests & Activities:**
        - Primary interests: {interests_str}

        **Additional Requirements:**
        {'No special requirements'}

        **IMPORTANT INSTRUCTIONS:**
        1. Provide realistic and current pricing (consider 2024/2025 market rates)
        2. Suggest actual airlines that operate on this route
        3. Recommend real hotels/accommodations with accurate location info  
        4. Create day-by-day activities that match the user's interests
        5. Stay within the specified budgets
        6. Include practical tips and money-saving advice

        Please provide recommendations in this exact JSON format:
        {{
            "user_preferences_summary": "Concise summary of key user requirements and constraints",
            "analysis_reasoning": "Detailed 3-4 sentence explanation of your recommendation strategy, why you chose these specific options, and how they meet the user's needs and budget",
            "flights": {{
                "airline": "Specific airline name (e.g., Delta, American Airlines)",
                "route": "{preferences['origin']} to {preferences['destination']}",
                "departure_date": "{preferences['start_date']}",
                "return_date": "{preferences['end_date']}", 
                "departure_time": "Realistic departure time",
                "arrival_time": "Realistic arrival time",
                "price": "Realistic price in USD format (e.g., $650)",
                "type": "Direct, 1 stop, or 2+ stops",
                "duration": "Total travel time",
                "booking_tips": "Specific actionable booking advice"
            }},
            "hotel": {{
                "name": "Specific hotel name or type of accommodation",
                "location": "Specific area/district in {preferences['destination']}",
                "address": "General area description",
                "price_per_night": "Price in USD format (e.g., $120)",
                "total_cost": "Total cost for {preferences['duration']} nights",
                "star_rating": "Hotel star rating or quality level",
                "amenities": "Key amenities (WiFi, breakfast, gym, etc.)",
                "booking_tips": "Best booking platforms or timing advice"
            }},
            "activities": [
                {{
                    "day": 1,
                    "activity": "Specific activity name",
                    "description": "Detailed description of the activity",
                    "location": "Where in the city",
                    "estimated_cost": "Cost estimate per person",
                    "duration": "How long to spend",
                    "tips": "Insider tips and recommendations"
                }},
                {{
                    "day": 2,
                    "activity": "Different activity for day 2",
                    "description": "Detailed description",
                    "location": "Location details",
                    "estimated_cost": "Cost estimate",
                    "duration": "Time needed",
                    "tips": "Helpful advice"
                }}
            ],
            "additional_suggestions": [
                "Money-saving tip with specific actionable advice",
                "Transportation recommendation with costs",
                "Local dining suggestion with price ranges",
                "Weather/packing advice for the dates",
                "Cultural etiquette or local customs tip",
                "Emergency contact or safety advice"
            ],
            "cost_breakdown": {{
                "flights_total": "Total flight cost in USD (multiply by number of travelers)",
                "accommodation_total": "Total hotel cost for all nights", 
                "activities_estimated": "Total estimated activity costs",
                "daily_food_budget": "Suggested daily food budget per person",
                "transportation_local": "Local transportation estimate",
                "total_estimated": "Grand total trip estimate"
            }}
        }}

        Ensure all recommendations are:
        - Realistic and achievable within the specified budget
        - Tailored to the user's specific interests
        - Include actual places, realistic prices, and actionable advice
        - Consider the travel dates and seasonality
        - Provide genuine value and insights beyond generic suggestions
        """

        # Call OpenAI API with user-selected model and creativity
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional travel advisor with deep expertise in global travel, current pricing, and destination-specific recommendations. Provide accurate, helpful, and budget-conscious advice."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=temperature
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            recommendations = json.loads(json_str)
            return recommendations
        else:
            # Fallback if JSON parsing fails
            return {"error": "Could not parse AI response", "raw_response": content}
            
    except Exception as e:
        return {"error": f"Error generating recommendations: {str(e)}"}

# Header
st.markdown('<h1 class="main-header">✈️ AI Travel Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Find affordable flights, hotels, and create optimal travel itineraries</p>', unsafe_allow_html=True)

# Sidebar for user preferences
with st.sidebar:
    st.markdown('<h2 class="section-header">🎯 Travel Preferences</h2>', unsafe_allow_html=True)
    
    # OpenAI API Key setup
    api_key_available = setup_openai()
    
    st.markdown("---")
    
    # Destination
    destination = st.text_input("🌍 Destination", placeholder="e.g., Paris, London, Tokyo")
    
    # Origin
    origin = st.text_input("🏠 Departure City", placeholder="e.g., New York, Los Angeles")
    
    # Travel dates
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Start Date", 
                                 value=datetime.date.today() + timedelta(days=30),
                                 min_value=datetime.date.today())
    with col2:
        end_date = st.date_input("📅 End Date",
                               value=datetime.date.today() + timedelta(days=35),
                               min_value=start_date if start_date else datetime.date.today())
    
    # Budget
    st.markdown("💰 **Budget Range**")
    flight_budget = st.slider("Flight Budget (USD)", 100, 3000, 800, 50)
    hotel_budget = st.slider("Hotel Budget per night (USD)", 50, 500, 150, 25)
    
    # Travelers
    travelers = st.number_input("👥 Number of Travelers", min_value=1, max_value=10, value=1)
    
    # Accommodation preferences
    accommodation_type = st.selectbox("🏨 Accommodation Type", 
                                    ["Hotel", "Hostel", "Apartment/Airbnb", "Resort", "Boutique Hotel"])
    
    location_preference = st.text_input("📍 Preferred Location/Area", 
                                      placeholder="e.g., near city center, beach area")
    
    # Travel interests
    st.markdown("🎨 **Travel Interests** (Select all that apply)")
    interests = []
    if st.checkbox("Art & Museums"):
        interests.append("Art & Museums")
    if st.checkbox("Food & Dining"):
        interests.append("Food & Dining")
    if st.checkbox("Historical Sites"):
        interests.append("Historical Sites")
    if st.checkbox("Nature & Outdoors"):
        interests.append("Nature & Outdoors")
    if st.checkbox("Nightlife & Entertainment"):
        interests.append("Nightlife & Entertainment")
    if st.checkbox("Shopping"):
        interests.append("Shopping")
    if st.checkbox("Adventure Sports"):
        interests.append("Adventure Sports")
    if st.checkbox("Local Culture"):
        interests.append("Local Culture")
    
    # Add reset button and export functionality
    if st.session_state.preferences_collected:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 New Trip", help="Start planning a new trip"):
                st.session_state.preferences_collected = False
                st.session_state.ai_recommendations = None
                st.rerun()
        
        with col2:
            if st.session_state.ai_recommendations and "error" not in st.session_state.ai_recommendations:
                if st.button("📄 Export PDF", help="Export itinerary as PDF"):
                    st.info("💡 PDF export feature coming soon! For now, you can copy the itinerary text.")
    
    st.markdown("---")

# Main content area
if st.sidebar.button("🔍 Generate Travel Plan", type="primary"):
    # Check if API key is available
    if not api_key_available:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar to generate AI recommendations.")
    else:
        # Validate inputs
        missing_fields = []
        if not destination:
            missing_fields.append("Destination")
        if not origin:
            missing_fields.append("Departure City")
        if not start_date or not end_date:
            missing_fields.append("Travel Dates")
        
        if missing_fields:
            st.error(f"⚠️ Please fill in the following required fields: {', '.join(missing_fields)}")
        else:
            # Store preferences
            st.session_state.user_preferences = {
                'destination': destination,
                'origin': origin,
                'start_date': start_date,
                'end_date': end_date,
                'duration': (end_date - start_date).days,
                'flight_budget': flight_budget,
                'hotel_budget': hotel_budget,
                'travelers': travelers,
                'accommodation_type': accommodation_type,
                'location_preference': location_preference,
                'interests': interests,
                'model_choice': "gpt-4.1-mini",
                'creativity_level': 0.7
            }
            
            # Generate AI recommendations
            with st.spinner("🤖 AI is crafting your perfect travel itinerary... Please wait!"):
                st.session_state.ai_recommendations = generate_travel_itinerary(
                    st.session_state.user_preferences, 
                    model="gpt-4.1-mini", 
                    temperature=0.7
                )
            
            st.session_state.preferences_collected = True

# Display results if preferences are collected
if st.session_state.preferences_collected and st.session_state.ai_recommendations:
    prefs = st.session_state.user_preferences
    recommendations = st.session_state.ai_recommendations
    
    # Check if there was an error
    if "error" in recommendations:
        st.error(f"❌ {recommendations['error']}")
        if "raw_response" in recommendations:
            st.code(recommendations['raw_response'])
        st.stop()
    
    # Display user preferences summary
    st.markdown('<div class="preference-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Your Travel Preferences Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**🌍 Destination:** {prefs['destination']}")
        st.write(f"**🏠 From:** {prefs['origin']}")
        st.write(f"**📅 Duration:** {prefs['duration']} days")
    
    with col2:
        st.write(f"**💰 Flight Budget:** ${prefs['flight_budget']}")
        st.write(f"**🏨 Hotel Budget:** ${prefs['hotel_budget']}/night")
        st.write(f"**👥 Travelers:** {prefs['travelers']}")
    
    with col3:
        st.write(f"**🏨 Accommodation:** {prefs['accommodation_type']}")
        if prefs['location_preference']:
            st.write(f"**📍 Location:** {prefs['location_preference']}")
        if prefs['interests']:
            st.write(f"**🎨 Interests:** {', '.join(prefs['interests'])}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate and display recommendations
    st.markdown('<h2 class="section-header">🎯 AI Travel Recommendations</h2>', unsafe_allow_html=True)
    
    # Analysis and Reasoning
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown('<div class="recommendation-header">🧠 Analysis and Reasoning</div>', unsafe_allow_html=True)
    st.write(recommendations.get('analysis_reasoning', 'AI analysis not available'))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommended Itinerary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="recommendation-header">✈️ AI-Recommended Flight</div>', unsafe_allow_html=True)
        
        flight_info = recommendations.get('flights', {})
        st.write(f"**Airline:** {flight_info.get('airline', 'N/A')}")
        st.write(f"**Route:** {flight_info.get('route', 'N/A')}")
        st.write(f"**Dates:** {flight_info.get('departure_date', 'N/A')} to {flight_info.get('return_date', 'N/A')}")
        st.write(f"**Departure:** {flight_info.get('departure_time', 'N/A')}")
        st.write(f"**Arrival:** {flight_info.get('arrival_time', 'N/A')}")
        st.write(f"**Duration:** {flight_info.get('duration', 'N/A')}")
        st.write(f"**Price:** {flight_info.get('price', 'N/A')}")
        st.write(f"**Type:** {flight_info.get('type', 'N/A')}")
        
        if flight_info.get('booking_tips'):
            st.info(f"💡 {flight_info['booking_tips']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="recommendation-header">🏨 AI-Recommended Hotel</div>', unsafe_allow_html=True)
        
        hotel_info = recommendations.get('hotel', {})
        st.write(f"**Name:** {hotel_info.get('name', 'N/A')}")
        st.write(f"**Location:** {hotel_info.get('location', 'N/A')}")
        st.write(f"**Address:** {hotel_info.get('address', 'N/A')}")
        st.write(f"**Rating:** {hotel_info.get('star_rating', 'N/A')}")
        st.write(f"**Price/Night:** {hotel_info.get('price_per_night', 'N/A')}")
        st.write(f"**Total Cost:** {hotel_info.get('total_cost', 'N/A')}")
        st.write(f"**Amenities:** {hotel_info.get('amenities', 'N/A')}")
        
        if hotel_info.get('booking_tips'):
            st.info(f"💡 {hotel_info['booking_tips']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Activities
    activities = recommendations.get('activities', [])
    if activities:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="recommendation-header">🎨 AI-Recommended Daily Activities</div>', unsafe_allow_html=True)
        
        for activity in activities:
            day = activity.get('day', 'N/A')
            name = activity.get('activity', 'N/A')
            description = activity.get('description', 'N/A')
            location = activity.get('location', 'N/A')
            cost = activity.get('estimated_cost', 'N/A')
            duration = activity.get('duration', 'N/A')
            tips = activity.get('tips', '')
            
            st.markdown(f'<div class="activity-item">', unsafe_allow_html=True)
            st.write(f"**Day {day}: {name}**")
            st.write(f"📍 {location}")
            st.write(f"{description}")
            st.write(f"⏱️ Duration: {duration} | 💰 Cost: {cost}")
            if tips:
                st.write(f"💡 {tips}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Suggestions
    additional_suggestions = recommendations.get('additional_suggestions', [])
    if additional_suggestions:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="recommendation-header">💡 AI Additional Suggestions</div>', unsafe_allow_html=True)
        
        for suggestion in additional_suggestions:
            st.write(f"• {suggestion}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Total estimated cost
    cost_breakdown = recommendations.get('cost_breakdown', {})
    if cost_breakdown:
        st.markdown('<div class="preference-card">', unsafe_allow_html=True)
        st.markdown("### 💰 AI Cost Breakdown")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Flights", cost_breakdown.get('flights_total', 'N/A'))
        with col2:
            st.metric("Hotels", cost_breakdown.get('accommodation_total', 'N/A'))
        with col3:
            st.metric("Activities", cost_breakdown.get('activities_estimated', 'N/A'))
        with col4:
            st.metric("Food & Transport", f"{cost_breakdown.get('daily_food_budget', 'N/A')}/day + {cost_breakdown.get('transportation_local', 'N/A')}")
        with col5:
            st.metric("**Total Estimate**", f"**{cost_breakdown.get('total_estimated', 'N/A')}**")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Welcome message when no preferences are set or show loading state
    if st.session_state.preferences_collected and not st.session_state.ai_recommendations:
        st.info("🤖 Processing your travel preferences... Please wait while AI generates your itinerary!")
    else:
        # Welcome message when no preferences are set
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h2>🌟 Welcome to Your AI-Powered Travel Assistant!</h2>
            <p style="font-size: 1.1rem; color: #5A6C7D; margin: 2rem 0;">
                Get personalized travel recommendations powered by OpenAI's GPT! Fill in your preferences to get started.
            </p>
            <div style="background: linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%); 
                        border-radius: 15px; padding: 2rem; margin: 2rem auto; max-width: 600px;">
                <h3>✨ AI-Powered Features:</h3>
                <div style="text-align: left; display: inline-block;">
                    • 🤖 Real AI analysis of your travel preferences<br>
                    • 🔍 Intelligent flight and hotel recommendations<br>
                    • 🗺️ Personalized day-by-day activity planning<br>
                    • 💡 Smart money-saving tips and insider advice<br>
                    • 🎯 Optimized itineraries based on your interests<br>
                    • 📊 Detailed cost breakdowns and budgeting
                </div>
            </div>
            <div style="background: #FFF3E0; border-radius: 10px; padding: 1.5rem; margin: 1rem auto; max-width: 500px;">
                <p style="color: #F57C00; font-weight: 600;">🔑 API Key Required</p>
                <p style="font-size: 0.9rem; color: #BF360C;">
                    You'll need an OpenAI API key to use the AI features. 
                    Get one at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>
                </p>
            </div>
            <p style="font-style: italic; color: #7B1FA2;">
                👈 Start by entering your API key and travel preferences in the sidebar!
            </p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #5A6C7D; font-size: 0.9rem;">🤖 Powered by AI • Made for travelers who love great deals</p>',
    unsafe_allow_html=True
)