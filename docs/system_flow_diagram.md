# System Flow Diagram - Daily Stand Up App

This document provides comprehensive flow diagrams for the Daily Stand Up App using Mermaid syntax. The diagrams illustrate the complete system architecture, user interactions, and automated processes.

## 0. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    %% Core Django User Model
    User {
        int id PK
        string username
        string email
        string first_name
        string last_name
        boolean is_active
        datetime date_joined
        datetime last_login
    }

    %% Teams App Models
    Team {
        int id PK
        string name UK
        text description
        string slack_channel_id UK
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    TeamMember {
        int id PK
        int user_id FK
        int team_id FK
        string role
        string slack_user_id
        boolean is_active
        datetime joined_at
    }

    StandupSchedule {
        int id PK
        int team_id FK
        json weekdays
        time reminder_time
        time end_time
        string timezone
        boolean is_active
        datetime created_at
    }

    %% Standups App Models
    Standup {
        int id PK
        int team_id FK
        date date
        string status
        datetime started_at
        datetime ended_at
        string slack_thread_ts
        datetime created_at
        datetime updated_at
    }

    StandupResponse {
        int id PK
        int standup_id FK
        int user_id FK
        text yesterday_work
        text today_work
        text blockers
        string mood
        datetime submitted_at
        datetime updated_at
        string slack_message_ts
    }

    StandupReminder {
        int id PK
        int standup_id FK
        int user_id FK
        string reminder_type
        datetime sent_at
        string slack_message_ts
        boolean responded
    }

    StandupMetrics {
        int id PK
        int team_id FK
        date date
        int total_members
        int responses_count
        float completion_rate
        duration average_response_time
        time first_response_time
        time last_response_time
        json mood_distribution
        datetime created_at
    }

    %% Slack Integration App Models
    SlackWorkspace {
        int id PK
        string team_id UK
        string team_name
        string bot_user_id
        text bot_access_token
        boolean is_active
        datetime installed_at
        datetime updated_at
    }

    SlackMessage {
        int id PK
        int workspace_id FK
        string channel_id
        string user_id
        string message_ts UK
        string thread_ts
        string message_type
        text content
        int standup_id FK
        datetime sent_at
    }

    SlackInteraction {
        int id PK
        int workspace_id FK
        string user_id
        string interaction_type
        string trigger_id
        string callback_id
        json payload
        json response_data
        int standup_id FK
        datetime created_at
    }

    SlackUserMapping {
        int id PK
        int user_id FK
        string slack_user_id UK
        string slack_username
        string slack_email
        int workspace_id FK
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    SlackChannelMapping {
        int id PK
        int team_id FK
        int workspace_id FK
        string channel_id
        string channel_name
        boolean is_private
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% Relationships
    %% User relationships
    User ||--o{ TeamMember : "belongs to"
    User ||--o{ StandupResponse : "submits"
    User ||--o{ StandupReminder : "receives"
    User ||--|| SlackUserMapping : "maps to"

    %% Team relationships
    Team ||--o{ TeamMember : "has members"
    Team ||--o{ StandupSchedule : "has schedules"
    Team ||--o{ Standup : "conducts"
    Team ||--o{ StandupMetrics : "generates"
    Team ||--|| SlackChannelMapping : "maps to"

    %% Standup relationships
    Standup ||--o{ StandupResponse : "receives"
    Standup ||--o{ StandupReminder : "triggers"
    Standup ||--o{ SlackMessage : "generates"
    Standup ||--o{ SlackInteraction : "involves"

    %% Slack Workspace relationships
    SlackWorkspace ||--o{ SlackMessage : "hosts"
    SlackWorkspace ||--o{ SlackInteraction : "handles"
    SlackWorkspace ||--o{ SlackUserMapping : "contains"
    SlackWorkspace ||--o{ SlackChannelMapping : "includes"

    %% Unique constraints and indexes (shown as comments)
    %% TeamMember: unique(user_id, team_id)
    %% Standup: unique(team_id, date)
    %% StandupResponse: unique(standup_id, user_id)
    %% StandupMetrics: unique(team_id, date)
    %% SlackUserMapping: unique(slack_user_id, workspace_id)
    %% SlackChannelMapping: unique(channel_id, workspace_id)
```

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Dashboard]
        API[REST API]
    end
    
    subgraph "Backend Services"
        Django[Django Application]
        Celery[Celery Workers]
        Beat[Celery Beat Scheduler]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL Database)]
        Redis[(Redis Cache/Broker)]
    end
    
    subgraph "External Services"
        Slack[Slack API]
        SlackBot[Slack Bot]
    end
    
    UI --> API
    API --> Django
    Django --> DB
    Django --> Redis
    Celery --> Redis
    Beat --> Redis
    Django <--> Slack
    SlackBot <--> Slack
    Celery --> SlackBot
```

## 2. User Authentication and Team Setup Flow

```mermaid
flowchart TD
    Start([User Visits App]) --> Login{Already Registered?}
    Login -->|No| Register[Register Account]
    Login -->|Yes| Auth[Login]
    Register --> Auth
    Auth --> Dashboard[Access Dashboard]
    
    Dashboard --> TeamSetup{Is Scrum Master?}
    TeamSetup -->|Yes| CreateTeam[Create/Manage Team]
    TeamSetup -->|No| JoinTeam[Join Existing Team]
    
    CreateTeam --> AddMembers[Add Team Members]
    AddMembers --> SlackConfig[Configure Slack Integration]
    SlackConfig --> SetSchedule[Set Reminder Schedule]
    SetSchedule --> SetQuestions[Configure Questions]
    SetQuestions --> TeamReady[Team Ready for Stand-ups]
    
    JoinTeam --> WaitApproval[Wait for Approval]
    WaitApproval --> TeamReady
    
    TeamReady --> End([Ready to Use])
```

## 3. Daily Stand-up Automated Flow

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Worker as Celery Worker
    participant DB as Database
    participant Slack as Slack API
    participant User as Team Member
    participant Dashboard as Web Dashboard
    
    Note over Beat: Daily at configured time
    Beat->>Worker: Trigger send_standup_reminders
    Worker->>DB: Get active teams & schedules
    DB-->>Worker: Return team data
    
    loop For each team member
        Worker->>Slack: Send reminder message
        Slack->>User: Deliver reminder
        User->>Slack: Click "Start Stand-up"
        Slack->>Worker: Send interaction webhook
        Worker->>DB: Create standup session
        
        loop For each question
            Worker->>Slack: Send question
            Slack->>User: Display question
            User->>Slack: Submit answer
            Slack->>Worker: Send response webhook
            Worker->>DB: Store response
        end
        
        Worker->>Slack: Send completion confirmation
        Worker->>DB: Mark standup complete
    end
    
    Worker->>Dashboard: Update real-time status
```

## 4. Follow-up Reminder System

```mermaid
flowchart TD
    Start([Hourly Check]) --> GetPending[Get Pending Stand-ups]
    GetPending --> CheckTime{Before End Time?}
    CheckTime -->|No| StopReminders[Stop Reminders]
    CheckTime -->|Yes| HasPending{Any Pending?}
    
    HasPending -->|No| Wait[Wait Next Hour]
    HasPending -->|Yes| SendFollowUp[Send Follow-up Reminders]
    
    SendFollowUp --> CheckResponse{User Responded?}
    CheckResponse -->|Yes| MarkComplete[Mark Complete]
    CheckResponse -->|No| ScheduleNext[Schedule Next Follow-up]
    
    MarkComplete --> UpdateStatus[Update Dashboard]
    ScheduleNext --> Wait
    UpdateStatus --> Wait
    StopReminders --> GenerateSummary[Generate Daily Summary]
    Wait --> Start
```

## 5. Slack Bot Interaction Flow

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> ReceiveReminder: Daily reminder sent
    ReceiveReminder --> WaitingStart: User sees reminder
    
    WaitingStart --> StartStandup: User clicks "Start Stand-up"
    WaitingStart --> ReceiveFollowup: Follow-up reminder
    ReceiveFollowup --> WaitingStart
    
    StartStandup --> Question1: Send first question
    Question1 --> WaitAnswer1: Wait for response
    WaitAnswer1 --> Question2: Answer received
    
    Question2 --> WaitAnswer2: Wait for response
    WaitAnswer2 --> Question3: Answer received
    
    Question3 --> WaitAnswer3: Wait for response
    WaitAnswer3 --> Complete: Final answer received
    
    Complete --> Confirmation: Send completion message
    Confirmation --> Idle: Reset for next day
    
    WaitAnswer1 --> Timeout1: No response (5min)
    WaitAnswer2 --> Timeout2: No response (5min)
    WaitAnswer3 --> Timeout3: No response (5min)
    
    Timeout1 --> Question1: Resend question
    Timeout2 --> Question2: Resend question
    Timeout3 --> Question3: Resend question
```

## 6. Data Flow and Storage

```mermaid
flowchart LR
    subgraph "Input Sources"
        SlackResp[Slack Responses]
        WebInput[Web Dashboard Input]
        APICall[API Calls]
    end
    
    subgraph "Processing Layer"
        Validation[Data Validation]
        Transform[Data Transformation]
        Business[Business Logic]
    end
    
    subgraph "Storage Layer"
        Users[(Users Table)]
        Teams[(Teams Table)]
        Standups[(Standups Table)]
        Responses[(Responses Table)]
        Metrics[(Metrics Table)]
    end
    
    subgraph "Output Destinations"
        Dashboard[Web Dashboard]
        SlackSummary[Slack Summary]
        Reports[Generated Reports]
        Analytics[Analytics Data]
    end
    
    SlackResp --> Validation
    WebInput --> Validation
    APICall --> Validation
    
    Validation --> Transform
    Transform --> Business
    
    Business --> Users
    Business --> Teams
    Business --> Standups
    Business --> Responses
    Business --> Metrics
    
    Users --> Dashboard
    Teams --> Dashboard
    Standups --> SlackSummary
    Responses --> Reports
    Metrics --> Analytics
```

## 7. Summary Generation and Reporting Flow

```mermaid
flowchart TD
    Trigger([End of Day Trigger]) --> CollectData[Collect Daily Data]
    CollectData --> CalcMetrics[Calculate Metrics]
    
    CalcMetrics --> ParticipationRate[Calculate Participation Rate]
    CalcMetrics --> ResponseTimes[Analyze Response Times]
    CalcMetrics --> MoodAnalysis[Analyze Team Mood]
    
    ParticipationRate --> GenerateReport[Generate Summary Report]
    ResponseTimes --> GenerateReport
    MoodAnalysis --> GenerateReport
    
    GenerateReport --> FormatSlack[Format for Slack]
    GenerateReport --> FormatWeb[Format for Web Dashboard]
    GenerateReport --> FormatEmail[Format for Email]
    
    FormatSlack --> SendSlack[Send to Slack Channel]
    FormatWeb --> UpdateDashboard[Update Web Dashboard]
    FormatEmail --> SendEmail[Send Email Notifications]
    
    SendSlack --> StoreMetrics[Store Daily Metrics]
    UpdateDashboard --> StoreMetrics
    SendEmail --> StoreMetrics
    
    StoreMetrics --> ArchiveData[Archive Old Data]
    ArchiveData --> End([Process Complete])
```

## 8. Error Handling and Recovery Flow

```mermaid
flowchart TD
    Process[Normal Process] --> Error{Error Occurred?}
    Error -->|No| Success[Process Complete]
    Error -->|Yes| ErrorType{Error Type?}
    
    ErrorType -->|Slack API| SlackRetry[Retry Slack Request]
    ErrorType -->|Database| DBRetry[Retry Database Operation]
    ErrorType -->|Network| NetworkRetry[Retry Network Call]
    ErrorType -->|Validation| ValidationError[Log Validation Error]
    
    SlackRetry --> RetryCount{Retry < 3?}
    DBRetry --> RetryCount
    NetworkRetry --> RetryCount
    
    RetryCount -->|Yes| Wait[Wait & Retry]
    RetryCount -->|No| LogError[Log Critical Error]
    
    Wait --> Process
    LogError --> Fallback[Execute Fallback]
    ValidationError --> NotifyAdmin[Notify Administrator]
    
    Fallback --> Success
    NotifyAdmin --> Success
```

## 9. User Permission and Role Flow

```mermaid
flowchart TD
    UserLogin[User Login] --> CheckRole{User Role?}
    
    CheckRole -->|Admin| AdminAccess[Full System Access]
    CheckRole -->|Scrum Master| SMAccess[Team Management Access]
    CheckRole -->|Team Member| MemberAccess[Limited Access]
    
    AdminAccess --> ManageUsers[Manage All Users]
    AdminAccess --> ManageTeams[Manage All Teams]
    AdminAccess --> SystemConfig[System Configuration]
    AdminAccess --> ViewAllReports[View All Reports]
    
    SMAccess --> ManageOwnTeam[Manage Own Team]
    SMAccess --> ConfigSchedule[Configure Schedule]
    SMAccess --> ViewTeamReports[View Team Reports]
    SMAccess --> ManageQuestions[Manage Questions]
    
    MemberAccess --> ViewProfile[View Own Profile]
    MemberAccess --> SubmitStandup[Submit Stand-up]
    MemberAccess --> ViewOwnHistory[View Own History]
    
    ManageUsers --> AuditLog[Record in Audit Log]
    ManageTeams --> AuditLog
    SystemConfig --> AuditLog
    ManageOwnTeam --> AuditLog
    ConfigSchedule --> AuditLog
```

## 10. Notification and Communication Flow

```mermaid
sequenceDiagram
    participant System as System Scheduler
    participant Queue as Message Queue
    participant Worker as Background Worker
    participant Slack as Slack API
    participant Channel as Slack Channel
    participant DM as Direct Message
    participant Dashboard as Web Dashboard
    
    System->>Queue: Schedule notifications
    Queue->>Worker: Process notification job
    
    alt Daily Reminder
        Worker->>Slack: Send to channel
        Slack->>Channel: Post reminder message
        Worker->>Slack: Send DMs to individuals
        Slack->>DM: Deliver personal reminders
    end
    
    alt Follow-up Reminder
        Worker->>Slack: Send follow-up DM
        Slack->>DM: Deliver follow-up
    end
    
    alt Daily Summary
        Worker->>Slack: Send summary to channel
        Slack->>Channel: Post summary
        Worker->>Dashboard: Update dashboard
        Dashboard->>Dashboard: Refresh data
    end
    
    alt Error Notifications
        Worker->>Slack: Send error alert
        Slack->>DM: Alert administrators
    end
```

## Technical Implementation Notes

### Key Components

- **Django Apps**: authentication, teams, standups, slack_integration
- **Celery Tasks**: Automated scheduling and background processing
- **Slack Integration**: Bot framework with webhook handling
- **Database Models**: User, Team, Standup, Response, Metrics
- **API Endpoints**: RESTful design for frontend communication

### Data Flow Security

- All API communications use HTTPS
- Slack webhooks include signature verification
- Database operations use parameterized queries
- User authentication required for all operations
- Role-based access control implemented

### Scalability Considerations

- Horizontal scaling support for Celery workers
- Database indexing for performance
- Redis caching for frequently accessed data
- Async processing for Slack interactions
- Load balancing for web requests

This flow diagram provides a comprehensive view of the Daily Stand Up App's architecture and operational flows, supporting both technical implementation and user understanding of the system's behavior.
