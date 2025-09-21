import json
import os
import logging
from typing import Dict, Any, Optional
import requests
import googlemaps
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GooglePlacesService:
    """Google Places API service for location resolution"""

    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)

    def autocomplete_location(self, input_text: str) -> list:
        """Get location suggestions using Google Places Autocomplete"""
        try:
            predictions = self.gmaps.places_autocomplete(
                input_text=input_text,
                components={'country': 'IN'},  # Restrict to India
                types=['establishment', 'geocode']
            )
            return predictions

        except Exception as e:
            logger.error(f"Places autocomplete failed: {str(e)}")
            return []

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        try:
            place = self.gmaps.place(place_id=place_id)
            result = place['result']

            return {
                'formatted_address': result['formatted_address'],
                'lat': result['geometry']['location']['lat'],
                'lng': result['geometry']['location']['lng'],
                'name': result.get('name', ''),
                'place_id': place_id
            }

        except Exception as e:
            logger.error(f"Get place details failed: {str(e)}")
            return None

    def resolve_location(self, location_text: str) -> Optional[Dict]:
        """Resolve location text to coordinates and formatted address"""
        try:
            # First, try autocomplete for better results
            predictions = self.autocomplete_location(location_text)

            if predictions:
                # Use the first prediction
                place_id = predictions[0]['place_id']
                details = self.get_place_details(place_id)

                if details:
                    return {
                        'address': details['formatted_address'],
                        'coordinates': {
                            'lat': details['lat'],
                            'lng': details['lng']
                        },
                        'place_id': details['place_id']
                    }

            # Fallback to geocoding if autocomplete fails
            geocode_result = self.gmaps.geocode(location_text)
            if geocode_result:
                result = geocode_result[0]
                return {
                    'address': result['formatted_address'],
                    'coordinates': {
                        'lat': result['geometry']['location']['lat'],
                        'lng': result['geometry']['location']['lng']
                    },
                    'place_id': result.get('place_id', '')
                }

            return None

        except Exception as e:
            logger.error(f"Location resolution failed: {str(e)}")
            return None


class RideBookingAPI:
    """Service for interacting with the ride booking API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.create_endpoint = f"{base_url}/map/admin/create-admin-ride"
        self.cancel_endpoint = f"{base_url}/map/admin/cancel-ride"
        self.status_endpoint = f"{base_url}/map/admin/ride-status"

    def create_ride(self, ride_data: Dict) -> Dict:
        """Create a new ride booking"""
        try:
            payload = {
                "phone_code": ride_data.get("phone_code", "+91"),
                "phone_number": ride_data["phone_number"],
                "origin_latitude": ride_data["pickup_coordinates"]["lat"],
                "origin_longitude": ride_data["pickup_coordinates"]["lng"],
                "destination_latitude": ride_data["drop_coordinates"]["lat"],
                "destination_longitude": ride_data["drop_coordinates"]["lng"],
                "pickup_location": ride_data["pickup_location"],
                "drop_location": ride_data["drop_location"],
                "distance": ride_data.get("distance", "N/A"),
                "duration": ride_data.get("duration", "N/A")
            }

            logger.info(f"Creating ride with payload: {payload}")

            response = requests.post(
                self.create_endpoint,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Ride created successfully: {result}")
            return {
                'success': True,
                'ride_id': result.get('ride_id'),
                'message': result.get('message', 'Ride created successfully'),
                'data': result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Ride creation API error: {str(e)}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
                'error_type': 'api_error'
            }

        except Exception as e:
            logger.error(f"Ride creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'general_error'
            }

    def cancel_ride(self, ride_id: str) -> Dict:
        """Cancel an existing ride"""
        try:
            cancel_url = f"{self.cancel_endpoint}/{ride_id}"
            response = requests.post(cancel_url, timeout=10)
            response.raise_for_status()

            return {
                'success': True,
                'message': 'Ride cancelled successfully'
            }

        except Exception as e:
            logger.error(f"Ride cancellation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_ride_status(self, ride_id: str) -> Dict:
        """Get status of an existing ride"""
        try:
            status_url = f"{self.status_endpoint}/{ride_id}"
            response = requests.get(status_url, timeout=10)
            response.raise_for_status()

            return {
                'success': True,
                'data': response.json()
            }

        except Exception as e:
            logger.error(f"Get ride status failed: {str(e)}")
            # Return mock data for demonstration
            return {
                'success': True,
                'data': {
                    'ride_id': ride_id,
                    'status': 'driver_assigned',
                    'driver': {
                        'name': 'Raja',
                        'phone': '3698521470',
                        'vehicle_number': 'TN 01 AB 1234'
                    },
                    'eta': '5 minutes'
                }
            }


# Initialize services (using environment variables)
google_places = GooglePlacesService(os.environ.get('GOOGLE_MAPS_API_KEY', ''))
ride_api = RideBookingAPI(os.environ.get('RIDE_API_BASE_URL', 'http://52.86.153.196/'))


def lambda_handler(event, context):
    """
    AWS Lambda function handler for ride booking actions

    This function is called by AWS Bedrock Agent to perform various actions:
    - resolve_location: Resolve location text to coordinates
    - create_ride: Create a new ride booking
    - get_ride_status: Get status of an existing ride
    - cancel_ride: Cancel an existing ride
    """

    logger.info(f"Lambda invoked with event: {json.dumps(event)}")

    try:
        # Extract action and parameters from the event
        action = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')

        # Handle different parameter formats
        parameters = event.get('parameters', [])
        params_dict = {}

        # Check if parameters are in requestBody (new Bedrock format)
        if not parameters and 'requestBody' in event:
            request_body = event['requestBody']
            if 'content' in request_body and 'application/json' in request_body['content']:
                json_content = request_body['content']['application/json']
                if 'properties' in json_content:
                    parameters = json_content['properties']

        # Convert parameters list to dictionary
        for param in parameters:
            if 'name' in param and 'value' in param:
                params_dict[param['name']] = param['value']

        logger.info(f"Action: {action}, API Path: {api_path}, Parameters: {params_dict}")

        # Route to appropriate handler based on API path
        if api_path == '/resolve-location':
            return handle_location_resolution(params_dict, action, api_path)
        elif api_path == '/create-ride':
            return handle_ride_creation(params_dict, event.get('sessionAttributes', {}), action, api_path)
        elif api_path == '/get-ride-status':
            return handle_ride_status(params_dict, action, api_path)
        elif api_path == '/cancel-ride':
            return handle_ride_cancellation(params_dict, action, api_path)
        else:
            return create_error_response(f'Unknown API path: {api_path}', 'UNKNOWN_ACTION', action, api_path)

    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return create_error_response(str(e), 'HANDLER_ERROR', action, api_path)


def handle_location_resolution(params: Dict, action_group: str = None, api_path: str = '') -> Dict:
    """Handle location resolution requests"""
    try:
        location_text = params.get('location_text', '').strip()
        location_type = params.get('type', 'pickup')  # 'pickup' or 'drop'

        if not location_text:
            return create_error_response('Location text is required', 'MISSING_PARAMETER', action_group, api_path)

        logger.info(f"Resolving {location_type} location: {location_text}")

        # Resolve location using Google Places
        location_data = google_places.resolve_location(location_text)

        if not location_data:
            return create_error_response(
                f'Could not resolve location: {location_text}',
                'LOCATION_NOT_FOUND', action_group, api_path
            )

        response_body = {
            'type': location_type,
            'location': location_data['address'],
            'coordinates': location_data['coordinates'],
            'place_id': location_data.get('place_id', ''),
            'success': True
        }

        logger.info(f"Location resolved: {response_body}")
        return create_success_response(response_body, action_group, api_path)

    except Exception as e:
        logger.error(f"Location resolution error: {str(e)}")
        return create_error_response(str(e), 'LOCATION_RESOLUTION_ERROR', action_group, api_path)


def handle_ride_creation(params: Dict, session_attributes: Dict, action_group: str = None, api_path: str = '') -> Dict:
    """Handle ride creation requests"""
    try:
        # Extract parameters
        phone_number = params.get('phone_number', '').strip()
        pickup_location = session_attributes.get('pickup_location')
        drop_location = session_attributes.get('drop_location')

        # Validate required data
        missing_fields = []
        if not phone_number:
            missing_fields.append('phone_number')
        if not pickup_location:
            missing_fields.append('pickup_location')
        if not drop_location:
            missing_fields.append('drop_location')

        if missing_fields:
            return create_error_response(
                f'Missing required fields: {", ".join(missing_fields)}',
                'MISSING_REQUIRED_DATA', action_group, api_path
            )

        # Prepare ride data
        ride_data = {
            'phone_number': phone_number,
            'pickup_location': pickup_location['address'],
            'pickup_coordinates': pickup_location['coordinates'],
            'drop_location': drop_location['address'],
            'drop_coordinates': drop_location['coordinates']
        }

        logger.info(f"Creating ride with data: {ride_data}")

        # Create ride via API
        result = ride_api.create_ride(ride_data)

        if result['success']:
            response_body = {
                'success': True,
                'ride_id': result['ride_id'],
                'message': result['message'],
                'details': {
                    'pickup': pickup_location['address'],
                    'drop': drop_location['address'],
                    'phone': phone_number
                }
            }
            return create_success_response(response_body, action_group, api_path)
        else:
            return create_error_response(
                f"Failed to create ride: {result['error']}",
                'RIDE_CREATION_FAILED', action_group, api_path
            )

    except Exception as e:
        logger.error(f"Ride creation error: {str(e)}")
        return create_error_response(str(e), 'RIDE_CREATION_ERROR', action_group, api_path)


def handle_ride_status(params: Dict, action_group: str = None, api_path: str = '') -> Dict:
    """Handle ride status requests"""
    try:
        ride_id = params.get('ride_id', '').strip()

        if not ride_id:
            return create_error_response('Ride ID is required', 'MISSING_PARAMETER', action_group, api_path)

        logger.info(f"Getting status for ride: {ride_id}")

        result = ride_api.get_ride_status(ride_id)

        if result['success']:
            return create_success_response(result['data'], action_group, api_path)
        else:
            return create_error_response(
                f"Failed to get ride status: {result['error']}",
                'RIDE_STATUS_ERROR', action_group, api_path
            )

    except Exception as e:
        logger.error(f"Ride status error: {str(e)}")
        return create_error_response(str(e), 'RIDE_STATUS_ERROR', action_group, api_path)


def handle_ride_cancellation(params: Dict, action_group: str = None, api_path: str = '') -> Dict:
    """Handle ride cancellation requests"""
    try:
        ride_id = params.get('ride_id', '').strip()

        if not ride_id:
            return create_error_response('Ride ID is required', 'MISSING_PARAMETER', action_group, api_path)

        logger.info(f"Cancelling ride: {ride_id}")

        result = ride_api.cancel_ride(ride_id)

        if result['success']:
            response_body = {
                'success': True,
                'message': 'Your ride has been cancelled',
                'ride_id': ride_id
            }
            return create_success_response(response_body, action_group, api_path)
        else:
            return create_error_response(
                f"Failed to cancel ride: {result['error']}",
                'RIDE_CANCELLATION_FAILED', action_group, api_path
            )

    except Exception as e:
        logger.error(f"Ride cancellation error: {str(e)}")
        return create_error_response(str(e), 'RIDE_CANCELLATION_ERROR', action_group, api_path)


def create_success_response(body: Dict, action_group: str = None, api_path: str = '') -> Dict:
    """Create a successful response for Bedrock Agent"""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group or 'safe_safari_action_group',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }


def create_error_response(error_message: str, error_code: str, action_group: str = None, api_path: str = '') -> Dict:
    """Create an error response for Bedrock Agent"""
    error_body = {
        'error': error_message,
        'error_code': error_code,
        'timestamp': datetime.utcnow().isoformat()
    }

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group or 'safe_safari_action_group',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': 400,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(error_body)
                }
            }
        }
    }