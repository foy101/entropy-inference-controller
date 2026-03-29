import json
from app import config

_publisher = None  # lazy init


def _get_publisher():
    """
    Create the Pub/Sub publisher only when we actually need it.
    This prevents local dev from requiring GCP credentials.
    """
    global _publisher
    if _publisher is not None:
        return _publisher

    # If we're not configured for GCP, never create a client.
    if not config.GCP_PROJECT_ID:
        return None

    from google.cloud import pubsub_v1
    _publisher = pubsub_v1.PublisherClient()
    return _publisher


def publish_inference_event(event: dict) -> None:
    # allow local dev without Pub/Sub
    if not config.GCP_PROJECT_ID:
        return

    publisher = _get_publisher()
    if publisher is None:
        return

    topic_path = publisher.topic_path(config.GCP_PROJECT_ID, config.PUBSUB_TOPIC)
    data = json.dumps(event).encode("utf-8")
    publisher.publish(topic_path, data=data)
