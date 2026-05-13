import threading

# Global event to signal new violations for long polling
# Moving this here prevents circular imports between routes and monitoring service
new_violation_event = threading.Event()
