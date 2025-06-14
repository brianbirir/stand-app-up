from django.shortcuts import render
import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User
from slack_sdk.signature import SignatureVerifier
from django.conf import settings

from .models import SlackWorkspace, SlackInteraction, SlackUserMapping
from .services import SlackService
from standups.models import Standup
from standups.tasks import process_standup_response

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SlackInteractionsView(View):
    """Handle Slack interactive components (buttons, modals, etc.)"""
    
    def post(self, request):
        # Verify Slack signature
        if not self._verify_slack_signature(request):
            return HttpResponse(status=403)
        
        try:
            payload = json.loads(request.POST.get('payload', '{}'))
            
            # Handle different types of interactions
            interaction_type = payload.get('type')
            
            if interaction_type == 'block_actions':
                return self._handle_block_actions(payload)
            elif interaction_type == 'view_submission':
                return self._handle_view_submission(payload)
            elif interaction_type == 'view_closed':
                return self._handle_view_closed(payload)
            else:
                logger.warning(f"Unhandled interaction type: {interaction_type}")
                return HttpResponse(status=200)
                
        except Exception as e:
            logger.error(f"Error handling Slack interaction: {e}")
            return HttpResponse(status=500)
    
    def _verify_slack_signature(self, request):
        """Verify that the request came from Slack"""
        if not settings.SLACK_SIGNING_SECRET:
            logger.warning("SLACK_SIGNING_SECRET not configured")
            return True  # Skip verification in development
        
        try:
            verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
            return verifier.is_valid_request(request.body, request.headers)
        except Exception as e:
            logger.error(f"Error verifying Slack signature: {e}")
            return False
    
    def _handle_block_actions(self, payload):
        """Handle button clicks and other block actions"""
        try:
            team_id = payload['team']['id']
            user_id = payload['user']['id']
            trigger_id = payload['trigger_id']
            
            # Log the interaction
            workspace = SlackWorkspace.objects.get(team_id=team_id)
            SlackInteraction.objects.create(
                workspace=workspace,
                user_id=user_id,
                interaction_type='button_click',
                trigger_id=trigger_id,
                payload=payload
            )
            
            # Handle specific actions
            for action in payload['actions']:
                action_id = action['action_id']
                value = action.get('value')
                
                if action_id == 'submit_standup':
                    return self._handle_submit_standup_button(trigger_id, value, user_id, team_id)
                elif action_id == 'skip_standup':
                    return self._handle_skip_standup_button(value, user_id, team_id)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error handling block actions: {e}")
            return HttpResponse(status=500)
    
    def _handle_submit_standup_button(self, trigger_id, standup_id, slack_user_id, team_id):
        """Handle submit stand-up button click"""
        try:
            slack_service = SlackService(team_id)
            success = slack_service.open_standup_modal(trigger_id, int(standup_id))
            
            if success:
                return HttpResponse(status=200)
            else:
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": "Sorry, there was an error opening the stand-up form. Please try again."
                })
                
        except Exception as e:
            logger.error(f"Error opening standup modal: {e}")
            return JsonResponse({
                "response_type": "ephemeral", 
                "text": "Sorry, there was an error. Please try again later."
            })
    
    def _handle_skip_standup_button(self, standup_id, slack_user_id, team_id):
        """Handle skip stand-up button click"""
        try:
            # Find the user
            user_mapping = SlackUserMapping.objects.filter(
                slack_user_id=slack_user_id,
                workspace__team_id=team_id,
                is_active=True
            ).first()
            
            if not user_mapping:
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": "User mapping not found. Please contact your administrator."
                })
            
            # Create a "skip" response
            response_data = {
                'yesterday_work': 'Not available today',
                'today_work': 'Not available today', 
                'blockers': '',
                'mood': 'okay'
            }
            
            # Process the response asynchronously
            process_standup_response.delay(
                user_mapping.user.id,
                int(standup_id),
                response_data
            )
            
            return JsonResponse({
                "response_type": "ephemeral",
                "text": "✅ Thanks for letting us know you're not available today."
            })
            
        except Exception as e:
            logger.error(f"Error handling skip: {e}")
            return JsonResponse({
                "response_type": "ephemeral",
                "text": "Sorry, there was an error. Please try again."
            })
    
    def _handle_view_submission(self, payload):
        """Handle modal form submissions"""
        try:
            team_id = payload['team']['id']
            user_id = payload['user']['id']
            view = payload['view']
            callback_id = view['callback_id']
            
            # Log the interaction
            workspace = SlackWorkspace.objects.get(team_id=team_id)
            SlackInteraction.objects.create(
                workspace=workspace,
                user_id=user_id,
                interaction_type='modal_submission',
                callback_id=callback_id,
                payload=payload
            )
            
            # Handle stand-up submission
            if callback_id.startswith('standup_submission_'):
                standup_id = int(callback_id.replace('standup_submission_', ''))
                return self._handle_standup_submission(standup_id, user_id, team_id, view)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error handling view submission: {e}")
            return HttpResponse(status=500)
    
    def _handle_standup_submission(self, standup_id, slack_user_id, team_id, view):
        """Process stand-up form submission"""
        try:
            # Find the user
            user_mapping = SlackUserMapping.objects.filter(
                slack_user_id=slack_user_id,
                workspace__team_id=team_id,
                is_active=True
            ).first()
            
            if not user_mapping:
                return JsonResponse({
                    "response_action": "errors",
                    "errors": {
                        "yesterday_work": "User mapping not found. Please contact your administrator."
                    }
                })
            
            # Extract form values
            values = view['state']['values']
            
            response_data = {
                'yesterday_work': values['yesterday_work']['yesterday_input']['value'] or '',
                'today_work': values['today_work']['today_input']['value'] or '',
                'blockers': values['blockers']['blockers_input']['value'] or '',
                'mood': values['mood']['mood_select']['selected_option']['value'],
            }
            
            # Validate required fields
            errors = {}
            if not response_data['yesterday_work'].strip():
                errors['yesterday_work'] = "Please describe what you worked on yesterday."
            if not response_data['today_work'].strip():
                errors['today_work'] = "Please describe what you'll work on today."
            
            if errors:
                return JsonResponse({
                    "response_action": "errors",
                    "errors": errors
                })
            
            # Process the response asynchronously
            process_standup_response.delay(
                user_mapping.user.id,
                standup_id,
                response_data
            )
            
            # Close the modal successfully
            return JsonResponse({
                "response_action": "clear"
            })
            
        except Exception as e:
            logger.error(f"Error processing standup submission: {e}")
            return JsonResponse({
                "response_action": "errors",
                "errors": {
                    "yesterday_work": "Sorry, there was an error processing your submission. Please try again."
                }
            })
    
    def _handle_view_closed(self, payload):
        """Handle modal closed events"""
        # Log that the modal was closed without submission
        try:
            team_id = payload['team']['id']
            user_id = payload['user']['id']
            
            workspace = SlackWorkspace.objects.get(team_id=team_id)
            SlackInteraction.objects.create(
                workspace=workspace,
                user_id=user_id,
                interaction_type='modal_submission',
                payload=payload,
                response_data={'action': 'closed_without_submission'}
            )
        except Exception as e:
            logger.error(f"Error logging modal close: {e}")
        
        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class SlackEventsView(View):
    """Handle Slack Events API callbacks"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Handle URL verification challenge
            if data.get('type') == 'url_verification':
                return JsonResponse({'challenge': data.get('challenge')})
            
            # Handle actual events
            if data.get('type') == 'event_callback':
                return self._handle_event(data['event'])
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}")
            return HttpResponse(status=500)
    
    def _handle_event(self, event):
        """Handle specific Slack events"""
        event_type = event.get('type')
        
        if event_type == 'app_mention':
            return self._handle_app_mention(event)
        elif event_type == 'message':
            return self._handle_message(event)
        
        return HttpResponse(status=200)
    
    def _handle_app_mention(self, event):
        """Handle when the bot is mentioned"""
        # This could be used to provide help or status information
        return HttpResponse(status=200)
    
    def _handle_message(self, event):
        """Handle direct messages to the bot"""
        # This could be used for commands or help
        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class SlackSlashCommandView(View):
    """Handle Slack slash commands"""
    
    def post(self, request):
        # Verify Slack signature
        if not self._verify_slack_signature(request):
            return HttpResponse(status=403)
        
        try:
            command = request.POST.get('command')
            text = request.POST.get('text', '').strip()
            user_id = request.POST.get('user_id')
            team_id = request.POST.get('team_id')
            trigger_id = request.POST.get('trigger_id')
            
            # Log the command
            workspace = SlackWorkspace.objects.get(team_id=team_id)
            SlackInteraction.objects.create(
                workspace=workspace,
                user_id=user_id,
                interaction_type='slash_command',
                trigger_id=trigger_id,
                payload=request.POST.dict()
            )
            
            if command == '/standup':
                return self._handle_standup_command(text, user_id, team_id, trigger_id)
            elif command == '/standup-status':
                return self._handle_status_command(text, user_id, team_id)
            
            return JsonResponse({
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}"
            })
            
        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            return JsonResponse({
                "response_type": "ephemeral",
                "text": "Sorry, there was an error processing your command."
            })
    
    def _verify_slack_signature(self, request):
        """Verify that the request came from Slack"""
        if not settings.SLACK_SIGNING_SECRET:
            return True  # Skip verification in development
        
        try:
            verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
            return verifier.is_valid_request(request.body, request.headers)
        except Exception as e:
            logger.error(f"Error verifying Slack signature: {e}")
            return False
    
    def _handle_standup_command(self, text, slack_user_id, team_id, trigger_id):
        """Handle /standup command"""
        try:
            # Find user's teams
            user_mapping = SlackUserMapping.objects.filter(
                slack_user_id=slack_user_id,
                workspace__team_id=team_id,
                is_active=True
            ).first()
            
            if not user_mapping:
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": "You're not registered for stand-ups. Please contact your administrator."
                })
            
            # Get user's active stand-ups for today
            from django.utils import timezone
            today = timezone.now().date()
            
            active_standups = Standup.objects.filter(
                team__teammember__user=user_mapping.user,
                team__teammember__is_active=True,
                date=today,
                status='in_progress'
            )
            
            if not active_standups.exists():
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": "No active stand-ups found for today."
                })
            
            # If user specified a team or there's only one active standup
            if len(active_standups) == 1 or text:
                standup = active_standups.first()
                
                # Open the modal
                slack_service = SlackService(team_id)
                success = slack_service.open_standup_modal(trigger_id, standup.id)
                
                if success:
                    return JsonResponse({
                        "response_type": "ephemeral",
                        "text": "Opening stand-up form..."
                    })
                else:
                    return JsonResponse({
                        "response_type": "ephemeral",
                        "text": "Sorry, there was an error opening the form."
                    })
            else:
                # Show list of available stand-ups
                team_list = "\n".join([f"• {s.team.name}" for s in active_standups])
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": f"You have multiple active stand-ups today:\n{team_list}\n\nUse `/standup [team-name]` to specify which team."
                })
                
        except Exception as e:
            logger.error(f"Error handling standup command: {e}")
            return JsonResponse({
                "response_type": "ephemeral",
                "text": "Sorry, there was an error processing your request."
            })
    
    def _handle_status_command(self, text, slack_user_id, team_id):
        """Handle /standup-status command"""
        try:
            user_mapping = SlackUserMapping.objects.filter(
                slack_user_id=slack_user_id,
                workspace__team_id=team_id,
                is_active=True
            ).first()
            
            if not user_mapping:
                return JsonResponse({
                    "response_type": "ephemeral",
                    "text": "You're not registered for stand-ups."
                })
            
            # Get today's stand-up status
            from django.utils import timezone
            today = timezone.now().date()
            
            user_teams = user_mapping.user.teammember_set.filter(is_active=True)
            status_lines = []
            
            for team_member in user_teams:
                try:
                    standup = Standup.objects.get(team=team_member.team, date=today)
                    has_responded = standup.responses.filter(user=user_mapping.user).exists()
                    
                    status = "✅ Submitted" if has_responded else f"⏳ {standup.status.title()}"
                    status_lines.append(f"• {team_member.team.name}: {status}")
                except Standup.DoesNotExist:
                    status_lines.append(f"• {team_member.team.name}: No stand-up today")
            
            if status_lines:
                status_text = f"Your stand-up status for {today.strftime('%B %d, %Y')}:\n" + "\n".join(status_lines)
            else:
                status_text = "You're not part of any teams with stand-ups."
            
            return JsonResponse({
                "response_type": "ephemeral",
                "text": status_text
            })
            
        except Exception as e:
            logger.error(f"Error handling status command: {e}")
            return JsonResponse({
                "response_type": "ephemeral",
                "text": "Sorry, there was an error getting your status."
            })
