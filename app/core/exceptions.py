class AIRideBookingException(Exception):
    """Base exception for AI Ride Booking System"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TranslationException(AIRideBookingException):
    """Exception raised for translation errors"""
    pass


class SpeechProcessingException(AIRideBookingException):
    """Exception raised for speech processing errors"""
    pass


class BedrockAgentException(AIRideBookingException):
    """Exception raised for AWS Bedrock Agent errors"""
    pass


class LocationResolutionException(AIRideBookingException):
    """Exception raised for location resolution errors"""
    pass


class RideBookingAPIException(AIRideBookingException):
    """Exception raised for ride booking API errors"""
    pass


class SessionException(AIRideBookingException):
    """Exception raised for session management errors"""
    pass


class ValidationException(AIRideBookingException):
    """Exception raised for validation errors"""
    pass


class ConfigurationException(AIRideBookingException):
    """Exception raised for configuration errors"""
    pass