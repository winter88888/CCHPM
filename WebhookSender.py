import requests
import json
import queue
import threading
import time



class WebhookSender:
    def __init__(self, max_queue_size=100):
        """
        Initialize the webhook sender with async processing capabilities.

        Args:
            max_queue_size: Maximum number of messages to queue before dropping new ones
         """
        self.message_queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._process_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def clear_queue(self):
        """Clear all pending messages from the queue in a thread-safe manner."""
        try:
            while True:
                # Remove all items from the queue without blocking
                self.message_queue.get_nowait()
                self.message_queue.task_done()  # Mark each removed item as processed
        except queue.Empty:
            pass  # Queue is now empty
        finally:
            self.logErrorMessage("Webhook message queue cleared", "INFO")

    def _process_queue(self):
        """Worker thread that processes messages from the queue."""
        while not self.stop_event.is_set():
            try:
                # Get message with timeout to allow checking stop_event
                message = self.message_queue.get(timeout=1)
                self._send_message_sync(message)
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logErrorMessage(f"Error processing message: {str(e)}", "error")

    def _send_message_sync(self, message_data: dict):
        """
        Synchronously send a message to Discord webhook.

        Args:
            message_data: Dictionary containing:
                - webhook_url: Decrypted webhook URL
                - content: Message content
                - user_name: Name of the user (for logging)
        """
        webhook_url = message_data['webhook_url']
        content = message_data['content']
        user_name = message_data.get('user_name', 'unknown')

        if not webhook_url or not webhook_url.startswith('https://discord.com/api/webhooks/'):
            self.logErrorMessage(f"Invalid webhook URL for command {user_name}", "error")
            return

        data = {
            "content": content,
            "username": user_name  # Custom username for webhook messages
        }

        headers = {
            "Content-Type": "application/json"
        }

        start_time = time.time()

        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(data),
                headers=headers,
                verify=False,  # Explicitly use certifi's certificate bundle
                timeout=5      # 5 second timeout
            )

            if response.status_code == 204:
                self.logErrorMessage(f"Successfully sent command from {user_name}", "info")
            else:
                self.logErrorMessage(
                    f"Failed to send the message for {user_name}. "
                    f"Status: {response.status_code}, Response: {response.text}",
                    "error"
                )
        except Exception as e:
            self.logErrorMessage(f"Error sending message {user_name}: {str(e)}", "error")
        finally:
            # Ensure we don't flood the system
            elapsed = time.time() - start_time
            if elapsed < 0.1:  # Minimum delay between requests
                time.sleep(0.1 - elapsed)

    def enqueue_message(self, webhook_url: str, content: str, user_name: str = "unknown") -> bool:
        """
        Enqueue a message for async sending.

        Args:
            webhook_url: Decrypted webhook URL
            content: Message content to send
            user_name: Name of the user (for logging)

        Returns:
            bool: True if message was queued, False if queue was full
        """
        message_data = {
            'webhook_url': webhook_url,
            'content': content,
            'user_name': user_name
        }

        try:
            self.message_queue.put_nowait(message_data)
            return True
        except queue.Full:
            self.logErrorMessage(f"Message queue full, dropping message from {user_name}", "error")
            return False

    def shutdown(self):
        """Cleanly shutdown the sender."""
        self.stop_event.set()
        self.worker_thread.join()

    def logErrorMessage(self, message: str, type: str):
        """Log messages with specified type."""
        if hasattr(self, 'logHandler'):
            self.logHandler(message, type)
        else:
            print(f"[{type.upper()}] {message}")  # Fallback to console if no logHandler
