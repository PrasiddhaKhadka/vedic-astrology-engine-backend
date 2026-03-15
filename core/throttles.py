from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ChartThrottle(AnonRateThrottle):
    """
    Strict limit for heavy computation endpoints:
    /chart/, /antardasha/, /ashtakavarga/
    """
    scope = 'chart'


class CompatibilityThrottle(AnonRateThrottle):
    """
    Limit for compatibility endpoints:
    /compatibility/guna/, /compatibility/dosha/
    """
    scope = 'compatibility'


class TransitThrottle(AnonRateThrottle):
    """
    Limit for transit endpoints:
    /transits/current/, /transits/date/, /transits/moon/
    """
    scope = 'transits'