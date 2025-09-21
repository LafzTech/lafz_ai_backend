Act as a senior AI/prompt engineer specialized in enterprise agent development. 
I’m building a domain-specific conversational agent using AWS Bedrock, without integrating a knowledge base. 
This agent is tailored for the Ride Booking System, and once optimized, will serve as a scalable template for multiple Ride Booking companies.
Your objective is to guide me through designing, training, and refining this agent to meet enterprise-grade standards—focusing on dynamic instruction handling, robust response structures (via Lambda functions), and domain alignment.
Help ensure the agent is production-ready, adaptable across different clients, and capable of delivering high-quality, domain-relevant interactions without relying on vector databases or knowledge bases.

Now comes this type of conversation:

Human chat : hello
AI chat : Hello! I'm an expert virtual assistant for an auto ride booking service. How can I assist you with booking a ride today?
Human chat : yes
AI chat : Great! Let's get started with booking your ride. What is your pickup location?
Human chat : ukkadam
AI chat : Okay, your pickup location is set to Ukkadam. What is your drop location?
Human chat : ganthipuram
AI chat : Got it, your drop location is set to Gandhipuram. Could you please provide your phone number?
Human chat : 1234567893
AI chat : Ride request submitted successfully! Your Ride ID is 987654. The driver will call you in about 5 minutes. Let me know if you need anything else!
Human chat : Driver details
AI chat : Driver Name: Raj, Phone: 9876543210


But I need converstion flow ,

Human chat : Hello
AI chat : Hello!  Let's get started with booking your ride. What is your pickup location?
Human chat : ukkadam
AI chat : Okay, your pickup location is set to Ukkadam. What is your drop location?
Human chat : ganthipuram
AI chat : Got it, your drop location is set to Gandhipuram. Could you please provide your phone number?
Human chat : 1234567893
AI chat : Ride request submitted successfully! Your Ride ID is 987654. The driver will call you in about 5 minutes. Let me know if you need anything else!
(Once driver accept the ride i will send driver details automatically)
AI chat : Driver Name: Raj, Phone: 9876543210