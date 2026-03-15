class SecurityHeadersMiddleware:
    """
    Adds HTTP security headers to every response.
    Equivalent to Helmet.js in Node/Express.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._add_security_headers(response)
        return response

    def _add_security_headers(self, response):
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Block clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Force HTTPS (enable in production)
        # response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # XSS protection for older browsers
        response['X-XSS-Protection'] = '1; mode=block'

        # Don't send referrer info to other domains
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Restrict browser features / APIs
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=()'
        )

        # Cache control for API responses — don't cache sensitive data
        if '/api/' in response.get('Content-Type', '') or hasattr(response, 'data'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma']        = 'no-cache'

        # Remove server identification header
        if 'Server' in response:
            del response['Server']

        # Remove Django version leakage
        if 'X-Powered-By' in response:
            del response['X-Powered-By']