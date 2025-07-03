# Daily Stand Up App

A comprehensive Django-based application for managing daily stand-ups with Slack integration, automated reminders, and team analytics.

## Features

- **Automated Stand-up Management**: Schedule and manage daily stand-ups for multiple teams
- **Slack Integration**: Send reminders, collect responses, and post summaries via Slack
- **Team Management**: Organize users into teams with role-based permissions
- **Analytics & Metrics**: Track participation rates, response times, and team mood trends
- **REST API**: Full API for integration with other tools and frontend applications
- **Real-time Notifications**: Automated reminders and follow-ups using Celery
- **Dashboard**: Visual overview of team performance and individual statistics

## Architecture

### Backend Components

- **Django**: Web framework and API
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Asynchronous task processing
- **Slack SDK**: Slack bot integration

### Key Apps

- **authentication**: User login/logout and profile management
- **teams**: Team and member management with schedules
- **standups**: Stand-up sessions, responses, and metrics
- **slack_integration**: Slack bot, interactions, and messaging

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Pipenv (for dependency management)

### Installation

1. **Clone and navigate to the project**:

```bash
cd /path/to/stand-app-up
```

2. **Install dependencies**:

```bash
pipenv install
pipenv shell
```

3. **Start database services**:

```bash
docker-compose up -d db redis
```

4. **Run database migrations**:

```bash
python manage.py migrate
```

5. **Create a superuser**:

```bash
python manage.py createsuperuser
```

6. **Start the development server**:

```bash
python manage.py runserver
```

7. **Start Celery worker (in another terminal)**:

```bash
celery -A standapp worker -l info
```

8. **Start Celery beat scheduler (in another terminal)**:

```bash
celery -A standapp beat -l info
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DB_NAME=standapp_db
DB_USER=standapp_user
DB_PASSWORD=standapp_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# Security
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

> **Note**: Stand-up timing is configured per team through the web interface via the StandupSchedule model, not through environment variables. Each team can have its own reminder times, end times, and timezone settings.

### Slack Setup

1. **Create a Slack App**:
   - Go to https://api.slack.com/apps
   - Create a new app for your workspace
   - Enable Socket Mode and generate App Token

2. **Configure Bot Permissions**:
   - Add OAuth scopes: `chat:write`, `users:read`, `channels:read`, `im:write`
   - Install app to workspace and get Bot Token

3. **Set up Slash Commands**:
   - `/standup` - Open stand-up submission form
   - `/standup-status` - Check stand-up status

4. **Configure Event Subscriptions**:
   - Enable events and set Request URL to your app's `/api/slack/events/`
   - Subscribe to `app_mention` and `message.im` events

5. **Set up Interactive Components**:
   - Set Request URL to your app's `/api/slack/interactions/`

## API Endpoints

### Authentication

- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Get current user profile

### Teams

- `GET /api/teams/teams/` - List teams
- `POST /api/teams/teams/` - Create team
- `GET /api/teams/teams/{id}/members/` - Get team members
- `POST /api/teams/teams/{id}/add_member/` - Add team member

### Stand-ups

- `GET /api/standups/standups/` - List stand-ups
- `GET /api/standups/standups/{id}/responses/` - Get stand-up responses
- `POST /api/standups/responses/` - Submit stand-up response
- `GET /api/standups/dashboard/` - Get dashboard data

### Metrics

- `GET /api/standups/metrics/` - Get team metrics
- `GET /api/standups/metrics/team_summary/` - Get team summaries

## Usage

### Setting Up a Team

1. **Create a Team**:

```bash
curl -X POST http://localhost:8000/api/teams/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Development Team",
    "description": "Main development team",
    "slack_channel_id": "C1234567890"
  }'
```

2. **Add Team Members**:

```bash
curl -X POST http://localhost:8000/api/teams/teams/1/add_member/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "slack_user_id": "U1234567890",
    "role": "member"
  }'
```

3. **Create Stand-up Schedule**:

```bash
curl -X POST http://localhost:8000/api/teams/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "team": 1,
    "weekdays": [1, 2, 3, 4, 5],
    "reminder_time": "09:00",
    "end_time": "17:00",
    "timezone": "UTC"
  }'
```

### Automated Stand-up Flow

1. **Daily Reminder**: At scheduled time, Celery sends Slack reminders to team members
2. **Response Collection**: Users click button to open modal and submit responses
3. **Follow-up Reminders**: Sent to users who haven't responded after 30 minutes
4. **Summary Generation**: At end time, summary posted to team channel
5. **Metrics Calculation**: Participation rates and mood data calculated

## Development

### Project Structure

```plaintext
stand-app-up/
├── authentication/          # User authentication
├── teams/                  # Team management
├── standups/              # Stand-up functionality
├── slack_integration/     # Slack bot integration
├── standapp/             # Django settings and config
├── static/               # Static files
├── docs/                 # Documentation
├── frontend/             # React frontend (optional)
└── docker-compose.yml    # Docker services
```

### Key Models

**Team**: Represents a team with Slack channel integration
**TeamMember**: User membership in teams with roles
**StandupSchedule**: Configures when stand-ups occur
**Standup**: Daily stand-up session instance
**StandupResponse**: Individual user responses
**StandupMetrics**: Calculated analytics data

### Celery Tasks

- `send_standup_reminders`: Check schedules and send initial reminders
- `send_follow_up_reminders`: Send follow-up reminders to non-responders
- `end_standups`: End stand-ups and generate summaries
- `generate_daily_metrics`: Calculate participation and mood metrics

## Deployment

### Production Setup

1. **Use Docker Compose**:

```bash
docker-compose up -d
```

2. **Configure Environment**:

- Set `DEBUG=False`
- Use secure `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`

3. **Set up SSL**:

- Configure Nginx with SSL certificates
- Update Slack app URLs to use HTTPS

4. **Monitor Services**:

- Set up logging for Django, Celery, and PostgreSQL
- Monitor Redis and database performance

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure PostgreSQL is running: `docker-compose up -d db`
   - Check database credentials in settings

2. **Slack Integration Issues**:
   - Verify bot token and signing secret
   - Check Slack app configuration
   - Ensure request URLs are accessible

3. **Celery Not Running**:
   - Start worker: `celery -A standapp worker -l info`
   - Start beat: `celery -A standapp beat -l info`
   - Check Redis connection

## Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Review Django admin interface at `/admin/`
3. Use Django shell for debugging: `python manage.py shell`

## License

This project is licensed under the MIT License.
