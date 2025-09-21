import asyncio
import json
from typing import Dict, Optional, Any
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from app.core.exceptions import BedrockAgentException
from app.core.logging import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class BedrockAgentService:
    """AWS Bedrock Agent service for conversation management"""

    def __init__(self):
        self.settings = get_settings()
        try:
            # Initialize Bedrock runtime client
            self.bedrock_runtime = boto3.client(
                'bedrock-agent-runtime',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )

            # Initialize Bedrock client for agent management
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )

            logger.info("Bedrock Agent service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock service: {str(e)}")
            raise BedrockAgentException(f"Bedrock service initialization failed: {str(e)}")

    async def invoke_agent(
        self,
        input_text: str,
        session_id: str,
        session_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke AWS Bedrock Agent with conversation context

        Args:
            input_text: User input text (in English)
            session_id: Session identifier
            session_attributes: Session context and attributes

        Returns:
            Agent response with action data
        """
        try:
            # Prepare session state
            session_state = {
                'sessionAttributes': session_attributes or {}
            }

            logger.info(f"Invoking Bedrock agent for session {session_id}")

            # Invoke the agent
            response = await asyncio.to_thread(
                self.bedrock_runtime.invoke_agent,
                agentId=self.settings.aws_bedrock_agent_id,
                agentAliasId=self.settings.aws_bedrock_agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                sessionState=session_state
            )

            # Process the response
            parsed_response = await self._parse_agent_response(response)

            logger.info(f"Bedrock agent response: {parsed_response}")
            return parsed_response

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Bedrock client error: {error_code} - {error_message}")
            raise BedrockAgentException(f"Bedrock agent error: {error_message}")

        except BotoCoreError as e:
            logger.error(f"AWS Bedrock boto core error: {str(e)}")
            raise BedrockAgentException(f"Bedrock connection error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock agent: {str(e)}")
            raise BedrockAgentException(f"Agent invocation failed: {str(e)}")

    async def _parse_agent_response(self, response: Dict) -> Dict[str, Any]:
        """Parse the raw Bedrock agent response"""
        try:
            # Extract completion from event stream
            completion = ""
            action_groups = []
            session_attributes = {}

            if 'completion' in response:
                # Handle streaming response
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            completion += chunk['bytes'].decode('utf-8')

                    elif 'trace' in event:
                        trace = event['trace']
                        # Extract action group invocations
                        if 'orchestrationTrace' in trace:
                            orchestration = trace['orchestrationTrace']
                            if 'observation' in orchestration:
                                observation = orchestration['observation']
                                if 'actionGroupInvocationOutput' in observation:
                                    action_output = observation['actionGroupInvocationOutput']
                                    action_groups.append(action_output)

            # Extract session attributes from final event
            if 'sessionState' in response:
                session_attributes = response['sessionState'].get('sessionAttributes', {})

            return {
                'text': completion.strip(),
                'action_groups': action_groups,
                'session_attributes': session_attributes,
                'raw_response': response
            }

        except Exception as e:
            logger.error(f"Failed to parse agent response: {str(e)}")
            raise BedrockAgentException(f"Response parsing failed: {str(e)}")

    async def create_agent(self, agent_name: str) -> str:
        """
        Create a new Bedrock agent for ride booking

        Args:
            agent_name: Name for the agent

        Returns:
            Agent ID
        """
        try:
            agent_instruction = """
            You are a ride booking assistant that helps users book auto rides in Tamil Nadu, India.
            Your role is to:

            1. Greet users and collect their pickup location
            2. Ask for their drop location
            3. Request their phone number
            4. Confirm all details and create the ride booking
            5. Provide ride status and driver information when available

            Guidelines:
            - Always be polite and helpful
            - Validate locations using the location resolution action
            - Ensure you have all required information before booking
            - Handle cancellations and modifications gracefully
            - Provide clear updates on ride status

            Conversation flow:
            1. Greeting → Ask for pickup location
            2. Pickup received → Ask for drop location
            3. Drop received → Ask for phone number
            4. All details received → Confirm and create ride
            5. Ride created → Provide booking confirmation
            """

            response = await asyncio.to_thread(
                self.bedrock_agent.create_agent,
                agentName=agent_name,
                foundationModel='anthropic.claude-3-haiku-20240307-v1:0',
                instruction=agent_instruction,
                idleSessionTTLInSeconds=self.settings.session_ttl,
                agentResourceRoleArn=self.settings.aws_lambda_function_arn
            )

            agent_id = response['agent']['agentId']
            logger.info(f"Created Bedrock agent: {agent_id}")
            return agent_id

        except Exception as e:
            logger.error(f"Failed to create Bedrock agent: {str(e)}")
            raise BedrockAgentException(f"Agent creation failed: {str(e)}")

    async def attach_action_group(
        self,
        agent_id: str,
        action_group_name: str,
        lambda_arn: str,
        api_schema_s3_uri: str
    ) -> str:
        """
        Attach Lambda function as action group to the agent

        Args:
            agent_id: The agent ID
            action_group_name: Name for the action group
            lambda_arn: Lambda function ARN
            api_schema_s3_uri: S3 URI for API schema

        Returns:
            Action group ID
        """
        try:
            response = await asyncio.to_thread(
                self.bedrock_agent.create_agent_action_group,
                agentId=agent_id,
                actionGroupName=action_group_name,
                actionGroupExecutor={
                    'lambda': lambda_arn
                },
                apiSchema={
                    's3': {
                        's3BucketName': api_schema_s3_uri.split('/')[2],
                        's3ObjectKey': '/'.join(api_schema_s3_uri.split('/')[3:])
                    }
                },
                description="Action group for ride booking operations"
            )

            action_group_id = response['agentActionGroup']['actionGroupId']
            logger.info(f"Attached action group {action_group_id} to agent {agent_id}")
            return action_group_id

        except Exception as e:
            logger.error(f"Failed to attach action group: {str(e)}")
            raise BedrockAgentException(f"Action group attachment failed: {str(e)}")

    async def prepare_agent(self, agent_id: str) -> None:
        """Prepare the agent for use"""
        try:
            await asyncio.to_thread(
                self.bedrock_agent.prepare_agent,
                agentId=agent_id
            )
            logger.info(f"Prepared agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to prepare agent: {str(e)}")
            raise BedrockAgentException(f"Agent preparation failed: {str(e)}")

    async def create_agent_alias(self, agent_id: str, alias_name: str) -> str:
        """Create an alias for the agent"""
        try:
            response = await asyncio.to_thread(
                self.bedrock_agent.create_agent_alias,
                agentId=agent_id,
                agentAliasName=alias_name,
                description="Production alias for ride booking agent"
            )

            alias_id = response['agentAlias']['agentAliasId']
            logger.info(f"Created agent alias {alias_id} for agent {agent_id}")
            return alias_id

        except Exception as e:
            logger.error(f"Failed to create agent alias: {str(e)}")
            raise BedrockAgentException(f"Agent alias creation failed: {str(e)}")

    def get_agent_status(self, agent_id: str) -> Dict:
        """Get the current status of the agent"""
        try:
            response = self.bedrock_agent.get_agent(agentId=agent_id)
            return {
                'agent_id': agent_id,
                'status': response['agent']['agentStatus'],
                'name': response['agent']['agentName'],
                'created_at': response['agent']['createdAt'],
                'updated_at': response['agent']['updatedAt']
            }

        except Exception as e:
            logger.error(f"Failed to get agent status: {str(e)}")
            raise BedrockAgentException(f"Get agent status failed: {str(e)}")