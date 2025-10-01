
I need python best AI structure & Related API's

Voice Senarios:

Voice ----- (Its's comes voice call or vioce messgae) -----> OPEN AI Whishper ---------(Extract the STT) ------->(If the tamil, malayalam language)Google Translation (convert to english) (Else skip the translation)----> AWS Bedrock Agent (Use model Claude 3 haiku) ---- Agent attached action group (Lambda function) ---- (Explain What is inside the code in the lambda function)----
(In the code- If Pickup/Drop location comes call thr Google auto complete API get the value pickupCoordinates.lat, pickupCoordinates.lng, dropCoordinates.lat, dropCoordinates.lng, pickupLocation, dropLocation and get the phone number once get the all detauils call the API, 
URL - http://192.168.1.2:8000/map/admin/create-admin-ride 
Payload - {
    "phone_code": "+91",
    "phone_number": "1234567890",
    "origin_latitude": 10.9902127,
    "origin_longitude": 76.96286580000002,
    "destination_latitude": 11.0175845,
    "destination_longitude": 76.9674075,
    "pickup_location": "Ukkadam, Coimbatore, Tamil Nadu 641001, India",
    "drop_location": "Gandhipuram, Tamil Nadu 641012, India",
    "distance": "N/A",
    "duration": "N/A"
}
Response - {
    "ride_id": 123456,
    "message": "Ride created successfully"
}

) -----> In the lambda based agent response --> (If the tamil, malayalam language)Google Translation (convert english to which language tamil or malayalam) (Else skip the translation) ---> (Google TTS) ---> Voice call (Replay voice) or voice message (replay text only)

Chat Senarios:
User chat -----> (If the tamil, malayalam language)Google Translation (convert to english) (Else skip the translation)----> AWS Bedrock Agent (Use model Claude 3 haiku) ---- Agent attached action group (Lambda function) ---- (Explain What is inside the code in the lambda function)----
(In the code- If Pickup/Drop location comes call thr Google auto complete API get the value pickupCoordinates.lat, pickupCoordinates.lng, dropCoordinates.lat, dropCoordinates.lng, pickupLocation, dropLocation and get the phone number once get the all detauils call the API, 
URL - http://192.168.1.2:8000/map/admin/create-admin-ride 
Payload - {
    "phone_code": "+91",
    "phone_number": "1234567890",
    "origin_latitude": 10.9902127,
    "origin_longitude": 76.96286580000002,
    "destination_latitude": 11.0175845,
    "destination_longitude": 76.9674075,
    "pickup_location": "Ukkadam, Coimbatore, Tamil Nadu 641001, India",
    "drop_location": "Gandhipuram, Tamil Nadu 641012, India",
    "distance": "N/A",
    "duration": "N/A"
}
Response - {
    "ride_id": 123456,
    "message": "Ride created successfully"
}

) -----> In the lambda based agent response --> (If the tamil, malayalam language)Google Translation (convert english to which language tamil or malayalam) (Else skip the translation) -- send the response in user query

Use Model explantion:
Speech-to-Text (STT) → OpenAI Whisper

Converts user voice (English/Tamil/Malayalam) → text.

✅ Great for Indian languages (handles accents well).

Text-to-Speech (TTS) → Google TTS

Converts bot’s text response → natural Tamil/Malayalam/English voice.

Dialog Manager → Rasa

Controls conversation flow (pickup → drop → phone → confirm).

Ensures no steps are skipped.

Main Bot Brain (LLM) → Claude 3 Haiku (via AWS Bedrock)

Fast, cost-efficient reasoning.

Keeps all ride-booking logic in English.

Translation Layer → Google Cloud Translation (Basic)

Tamil/Malayalam ↔ English bridge.

User speaks Tamil/Malayalam → translated → Claude (English).

Claude replies (English) → translated → Tamil/Malayalam → TTS → voice.

Example with Dialog Manager:

User: "Hello"

Manager says: Go to Step 1 → Greeting

Bot: "Hello, I help with auto ride booking. What is your pickup location?"

User: "Ukkadam"

Manager says: Go to Step 2 → Ask drop

Bot: "What is your drop location?"

User: "Gandhipuram"

Manager says: Go to Step 3 → Ask phone

Bot: "Please give your phone number."

User: "1234567890"

Manager says: Go to Step 4 → Confirm ride

Bot: "Ride request sent. Driver will call in 5 minutes."

Example conversation flow:
human chat: Hello
AI chat : Hello, i help to auto ride booking, What is your pickup location?
human chat: ukkaddam coimbatore
AI chat: What is your drop location?
human chat: Gamdhiburam
AI chat: Please give your phone number, Driver will connect soon
human chat: 1234567890

AI chat : Ride requst sened, Driver call in 5min
(If accept the ride - Driver)
AI chat: Driver Name: Raja, Phone number: 3698521470
(If not accept the ride - Driver)
AI chat: You ride canceled
(Request again ) button - click the button again send the ride request & change location ( button) - click the button - ASK gain pickup drop location
