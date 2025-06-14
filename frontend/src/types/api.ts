// API Types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  teams: TeamMembership[];
}

export interface Team {
  id: number;
  name: string;
  description: string;
  slack_channel_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  member_count: number;
}

export interface TeamMembership {
  id: number;
  team: Team;
  team_name: string;
  role: 'member' | 'lead' | 'admin';
  slack_user_id: string;
  is_active: boolean;
  joined_at: string;
}

export interface StandupSchedule {
  id: number;
  team: number;
  team_name: string;
  weekdays: number[];
  weekday_names: string[];
  reminder_time: string;
  end_time: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface Standup {
  id: number;
  team: Team;
  date: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  started_at: string | null;
  ended_at: string | null;
  completion_rate: number;
  response_count: number;
  missing_count: number;
  created_at: string;
}

export interface StandupResponse {
  id: number;
  user: User;
  standup: number;
  standup_info: {
    team_name: string;
    date: string;
    status: string;
  };
  yesterday_work: string;
  today_work: string;
  blockers: string;
  mood: 'great' | 'good' | 'okay' | 'stressed' | 'blocked';
  submitted_at: string;
  updated_at: string;
}

export interface StandupMetrics {
  id: number;
  team: Team;
  date: string;
  total_members: number;
  responses_count: number;
  completion_rate: number;
  average_response_time: string | null;
  first_response_time: string | null;
  last_response_time: string | null;
  mood_distribution: Record<string, number>;
  created_at: string;
}

export interface DashboardData {
  user_stats: {
    teams_count: number;
    responses_this_week: number;
    current_streak: number;
    avg_mood_this_week: number;
  };
  team_stats: Array<{
    team: {
      id: number;
      name: string;
    };
    standups_this_week: number;
    avg_completion_rate: number;
    user_participation: number;
  }>;
  recent_standups: Standup[];
  recent_responses: StandupResponse[];
}

export interface ApiError {
  message: string;
  details?: Record<string, string[]>;
}