import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import SlackWorkspace, SlackMessage, SlackUserMapping, SlackChannelMapping
from teams.models import TeamMember
from standups.models import Standup, StandupResponse

logger = logging.getLogger(__name__)


class SlackService:
    """Service for handling Slack API interactions"""
    
    def __init__(self, workspace_team_id: Optional[str] = None):
        """Initialize Slack service with optional workspace"""
        self.workspace = None
        self.client = None
        
        if workspace_team_id:
            try:
                self.workspace = SlackWorkspace.objects.get(
                    team_id=workspace_team_id,
                    is_active=True
                )
                self.client = WebClient(token=self.workspace.bot_access_token)
            except SlackWorkspace.DoesNotExist:
                logger.error(f"Workspace {workspace_team_id} not found")
        else:
            # Use default workspace if available
            self.workspace = SlackWorkspace.objects.filter(is_active=True).first()
            if self.workspace:
                self.client = WebClient(token=self.workspace.bot_access_token)
    
    def send_standup_reminder(self, slack_user_id: str, standup: Standup, reminder_type: str) -> Optional[str]:
        """Send a stand-up reminder to a user"""
        if not self.client:
            logger.error("No Slack client available")
            return None
        
        try:
            # Create reminder message based on type
            if reminder_type == 'initial':
                message = self._create_initial_reminder_message(standup)
            elif reminder_type == 'follow_up':
                message = self._create_follow_up_reminder_message(standup)
            else:
                message = self._create_final_reminder_message(standup)
            
            # Send DM to user
            response = self.client.chat_postMessage(
                channel=slack_user_id,
                **message
            )
            
            if response['ok']:
                # Log the message
                SlackMessage.objects.create(
                    workspace=self.workspace,
                    channel_id=slack_user_id,
                    user_id=slack_user_id,
                    message_ts=response['ts'],
                    message_type='reminder',
                    content=json.dumps(message),
                    standup=standup
                )
                
                return response['ts']
            else:
                logger.error(f"Failed to send reminder: {response.get('error')}")
                return None
                
        except SlackApiError as e:
            logger.error(f"Slack API error sending reminder: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return None
    
    def _create_initial_reminder_message(self, standup: Standup) -> Dict[str, Any]:
        """Create initial stand-up reminder message"""
        return {
            "text": f"⏰ Time for your daily stand-up with {standup.team.name}!",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🌅 Daily Stand-up - {standup.team.name}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Good morning! It's time for your daily stand-up on {standup.date.strftime('%B %d, %Y')}.\n\nPlease share your updates with the team:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Submit Stand-up"
                            },
                            "style": "primary",
                            "action_id": "submit_standup",
                            "value": str(standup.id)
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "⏭️ Skip Today"
                            },
                            "action_id": "skip_standup",
                            "value": str(standup.id)
                        }
                    ]
                }
            ]
        }
    
    def _create_follow_up_reminder_message(self, standup: Standup) -> Dict[str, Any]:
        """Create follow-up reminder message"""
        return {
            "text": f"🔔 Friendly reminder: Stand-up for {standup.team.name}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👋 Hey there! Just a friendly reminder that you haven't submitted your stand-up for *{standup.team.name}* yet.\n\nYour team is waiting for your updates!"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Submit Now"
                            },
                            "style": "primary",
                            "action_id": "submit_standup",
                            "value": str(standup.id)
                        }
                    ]
                }
            ]
        }
    
    def _create_final_reminder_message(self, standup: Standup) -> Dict[str, Any]:
        """Create final reminder message"""
        return {
            "text": f"⚠️ Final reminder: Stand-up for {standup.team.name}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Final reminder* - The stand-up window for *{standup.team.name}* is closing soon.\n\nIf you're unable to participate today, that's okay! Your team will understand."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📝 Quick Submit"
                            },
                            "style": "primary",
                            "action_id": "submit_standup",
                            "value": str(standup.id)
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🚫 Can't Participate"
                            },
                            "action_id": "skip_standup",
                            "value": str(standup.id)
                        }
                    ]
                }
            ]
        }
    
    def send_standup_summary(self, standup: Standup) -> Optional[str]:
        """Send stand-up summary to team channel"""
        if not self.client:
            logger.error("No Slack client available")
            return None
        
        try:
            # Get team channel
            channel_mapping = SlackChannelMapping.objects.filter(
                team=standup.team,
                workspace=self.workspace,
                is_active=True
            ).first()
            
            if not channel_mapping:
                logger.error(f"No channel mapping found for team {standup.team.name}")
                return None
            
            # Create summary message
            message = self._create_summary_message(standup)
            
            # Send to team channel
            response = self.client.chat_postMessage(
                channel=channel_mapping.channel_id,
                **message
            )
            
            if response['ok']:
                # Log the message
                SlackMessage.objects.create(
                    workspace=self.workspace,
                    channel_id=channel_mapping.channel_id,
                    message_ts=response['ts'],
                    message_type='summary',
                    content=json.dumps(message),
                    standup=standup
                )
                
                # Update standup with thread timestamp
                standup.slack_thread_ts = response['ts']
                standup.save()
                
                return response['ts']
            else:
                logger.error(f"Failed to send summary: {response.get('error')}")
                return None
                
        except SlackApiError as e:
            logger.error(f"Slack API error sending summary: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
            return None
    
    def _create_summary_message(self, standup: Standup) -> Dict[str, Any]:
        """Create stand-up summary message"""
        responses = standup.responses.all().order_by('submitted_at')
        total_members = standup.team.teammember_set.filter(is_active=True).count()
        completion_rate = standup.completion_rate
        
        # Header section
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Stand-up Summary - {standup.date.strftime('%B %d, %Y')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Team:* {standup.team.name}\n*Participation:* {len(responses)}/{total_members} members ({completion_rate:.1f}%)"
                }
            }
        ]
        
        # Add divider
        blocks.append({"type": "divider"})
        
        # Add individual responses
        for response in responses:
            mood_emoji = {
                'great': '😄',
                'good': '😊', 
                'okay': '😐',
                'stressed': '😰',
                'blocked': '😤'
            }.get(response.mood, '😊')
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{response.user.get_full_name() or response.user.username}* {mood_emoji}\n"
                            f"*Yesterday:* {response.yesterday_work}\n"
                            f"*Today:* {response.today_work}"
                            + (f"\n*Blockers:* {response.blockers}" if response.blockers else "")
                }
            })
        
        # Add missing members if any
        missing_members = standup.missing_members
        if missing_members.exists():
            missing_names = [m.user.get_full_name() or m.user.username for m in missing_members]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Missing:* {', '.join(missing_names)}"
                }
            })
        
        return {
            "text": f"Daily Stand-up Summary - {standup.team.name}",
            "blocks": blocks
        }
    
    def send_response_confirmation(self, user: User, standup: Standup, response: StandupResponse) -> Optional[str]:
        """Send confirmation message after stand-up submission"""
        if not self.client:
            return None
        
        try:
            # Get user's Slack ID
            user_mapping = SlackUserMapping.objects.filter(
                user=user,
                workspace=self.workspace,
                is_active=True
            ).first()
            
            if not user_mapping:
                return None
            
            message = {
                "text": "✅ Stand-up submitted successfully!",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Thank you!* Your stand-up for *{standup.team.name}* has been submitted successfully.\n\nYour team will see your updates in the summary."
                        }
                    }
                ]
            }
            
            response = self.client.chat_postMessage(
                channel=user_mapping.slack_user_id,
                **message
            )
            
            return response['ts'] if response['ok'] else None
            
        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")
            return None
    
    def open_standup_modal(self, trigger_id: str, standup_id: int) -> bool:
        """Open stand-up submission modal"""
        if not self.client:
            return False
        
        try:
            standup = Standup.objects.get(id=standup_id)
            
            modal = {
                "type": "modal",
                "callback_id": f"standup_submission_{standup_id}",
                "title": {
                    "type": "plain_text",
                    "text": "Daily Stand-up"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{standup.team.name}* - {standup.date.strftime('%B %d, %Y')}"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "yesterday_work",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "yesterday_input",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "What did you work on yesterday?"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Yesterday's Work"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "today_work",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "today_input", 
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "What will you work on today?"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Today's Work"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "blockers",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "blockers_input",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Any blockers or impediments?"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Blockers (Optional)"
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "mood",
                        "element": {
                            "type": "static_select",
                            "action_id": "mood_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "How are you feeling today?"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "😄 Great"
                                    },
                                    "value": "great"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "😊 Good"
                                    },
                                    "value": "good"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "😐 Okay"
                                    },
                                    "value": "okay"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "😰 Stressed"
                                    },
                                    "value": "stressed"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "😤 Blocked"
                                    },
                                    "value": "blocked"
                                }
                            ],
                            "initial_option": {
                                "text": {
                                    "type": "plain_text",
                                    "text": "😊 Good"
                                },
                                "value": "good"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "How are you feeling?"
                        }
                    }
                ]
            }
            
            response = self.client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            
            return response['ok']
            
        except Exception as e:
            logger.error(f"Error opening modal: {e}")
            return False