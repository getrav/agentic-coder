#!/usr/bin/env python3
"""
GitHub Webhook Integration

Handles GitHub webhook events for issues.opened and issue_comment events.
Integrates with the SupervisorAgent workflow system.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from flask import Flask, request, jsonify
from langgraph_supervisor import LangGraphSupervisorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class GitHubWebhookHandler:
    """Handles GitHub webhook events and integrates with SupervisorAgent."""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self.supervisor = LangGraphSupervisorAgent()
        self._setup_agents()
    
    def _setup_agents(self):
        """Setup agents for handling different webhook events."""
        # Issue processing agent
        def issue_processor_agent(data: Dict[str, Any]) -> Dict[str, Any]:
            """Process GitHub issue events."""
            issue = data.get('issue', {})
            action = data.get('action')
            
            processed_data = {
                'event_type': 'issue',
                'action': action,
                'issue_id': issue.get('id'),
                'issue_number': issue.get('number'),
                'title': issue.get('title'),
                'body': issue.get('body'),
                'state': issue.get('state'),
                'user': issue.get('user', {}).get('login'),
                'created_at': issue.get('created_at'),
                'updated_at': issue.get('updated_at'),
                'url': issue.get('html_url'),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed issue {issue.get('number')}: {action}")
            return processed_data
        
        # Issue comment processing agent  
        def comment_processor_agent(data: Dict[str, Any]) -> Dict[str, Any]:
            """Process GitHub issue comment events."""
            comment = data.get('comment', {})
            issue = data.get('issue', {})
            action = data.get('action')
            
            processed_data = {
                'event_type': 'issue_comment',
                'action': action,
                'comment_id': comment.get('id'),
                'issue_id': issue.get('id'),
                'issue_number': issue.get('number'),
                'comment_body': comment.get('body'),
                'user': comment.get('user', {}).get('login'),
                'created_at': comment.get('created_at'),
                'updated_at': comment.get('updated_at'),
                'issue_url': issue.get('html_url'),
                'comment_url': comment.get('html_url'),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed comment on issue {issue.get('number')}: {action}")
            return processed_data
        
        # Register agents with supervisor
        self.supervisor.register_agent('issue_processor', issue_processor_agent)
        self.supervisor.register_agent('comment_processor', comment_processor_agent)
        
        # Create workflow
        self.supervisor.create_workflow()
    
    def verify_signature(self, payload: bytes, signature_header: str) -> bool:
        """Verify GitHub webhook signature."""
        if not self.secret:
            logger.warning("No webhook secret configured - skipping verification")
            return True
            
        expected_signature = 'sha256=' + hmac.new(
            self.secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature_header, expected_signature)
    
    def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook events."""
        try:
            if event_type == 'issues':
                return self._handle_issue_event(payload)
            elif event_type == 'issue_comment':
                return self._handle_issue_comment_event(payload)
            else:
                logger.warning(f"Unsupported event type: {event_type}")
                return {'error': f'Unsupported event type: {event_type}'}
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
            return {'error': str(e)}
    
    def _handle_issue_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue events."""
        action = payload.get('action')
        
        # Only process opened events as per requirements
        if action != 'opened':
            logger.info(f"Ignoring issue action: {action}")
            return {'message': f'Ignored issue action: {action}'}
        
        # Process through supervisor workflow
        result = self.supervisor.run_workflow({
            'event_type': 'issue',
            'data': payload
        })
        
        return {
            'status': 'success',
            'event': 'issue_opened',
            'result': result
        }
    
    def _handle_issue_comment_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue comment events."""
        action = payload.get('action')
        
        # Process comment events
        if action not in ['created', 'edited', 'deleted']:
            logger.info(f"Ignoring comment action: {action}")
            return {'message': f'Ignored comment action: {action}'}
        
        # Process through supervisor workflow
        result = self.supervisor.run_workflow({
            'event_type': 'issue_comment',
            'data': payload
        })
        
        return {
            'status': 'success',
            'event': f'issue_comment_{action}',
            'result': result
        }

# Initialize webhook handler
webhook_secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
webhook_handler = GitHubWebhookHandler(webhook_secret)

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """GitHub webhook endpoint."""
    try:
        # Get signature from headers
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Verify signature if secret is configured
        if webhook_secret and not webhook_handler.verify_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Get event type from headers
        event_type = request.headers.get('X-GitHub-Event', '')
        
        if not event_type:
            logger.warning("Missing X-GitHub-Event header")
            return jsonify({'error': 'Missing event type'}), 400
        
        # Parse payload
        try:
            payload = request.get_json()
        except Exception as e:
            logger.error(f"Failed to parse JSON payload: {e}")
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Handle the webhook event
        result = webhook_handler.handle_webhook(event_type, payload)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'github-webhook',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

def run_webhook_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the webhook server."""
    logger.info(f"Starting GitHub webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Configuration from environment variables
    host = os.environ.get('WEBHOOK_HOST', '0.0.0.0')
    port = int(os.environ.get('WEBHOOK_PORT', 5000))
    debug = os.environ.get('WEBHOOK_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Starting GitHub Webhook Server")
    print(f"📡 Listening on: {host}:{port}")
    print(f"🔐 Secret: {'Configured' if webhook_secret else 'Not configured'}")
    print(f"🎯 Events: issues.opened, issue_comment")
    print()
    
    run_webhook_server(host=host, port=port, debug=debug)