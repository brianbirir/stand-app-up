import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  User, 
  Team, 
  TeamMembership, 
  StandupSchedule, 
  Standup, 
  StandupResponse, 
  StandupMetrics, 
  DashboardData, 
  ApiError 
} from '../types/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(username: string, password: string): Promise<{ user: User; token?: string }> {
    const response = await this.api.post('/auth/login/', { username, password });
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    return response.data;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout/');
    localStorage.removeItem('auth_token');
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/user/');
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.api.put('/auth/user/', data);
    return response.data.user;
  }

  // Teams
  async getTeams(): Promise<Team[]> {
    const response = await this.api.get('/teams/teams/');
    return response.data.results || response.data;
  }

  async createTeam(team: Partial<Team>): Promise<Team> {
    const response = await this.api.post('/teams/teams/', team);
    return response.data;
  }

  async updateTeam(id: number, team: Partial<Team>): Promise<Team> {
    const response = await this.api.put(`/teams/teams/${id}/`, team);
    return response.data;
  }

  async deleteTeam(id: number): Promise<void> {
    await this.api.delete(`/teams/teams/${id}/`);
  }

  async getTeamMembers(teamId: number): Promise<TeamMembership[]> {
    const response = await this.api.get(`/teams/teams/${teamId}/members/`);
    return response.data;
  }

  async addTeamMember(teamId: number, member: {
    username: string;
    slack_user_id: string;
    role: string;
  }): Promise<TeamMembership> {
    const response = await this.api.post(`/teams/teams/${teamId}/add_member/`, member);
    return response.data;
  }

  async getTeamSchedules(): Promise<StandupSchedule[]> {
    const response = await this.api.get('/teams/schedules/');
    return response.data.results || response.data;
  }

  async createSchedule(schedule: Partial<StandupSchedule>): Promise<StandupSchedule> {
    const response = await this.api.post('/teams/schedules/', schedule);
    return response.data;
  }

  async updateSchedule(id: number, schedule: Partial<StandupSchedule>): Promise<StandupSchedule> {
    const response = await this.api.put(`/teams/schedules/${id}/`, schedule);
    return response.data;
  }

  async deleteSchedule(id: number): Promise<void> {
    await this.api.delete(`/teams/schedules/${id}/`);
  }

  // Stand-ups
  async getStandups(params?: { 
    team?: number; 
    date?: string; 
    status?: string;
    page?: number;
  }): Promise<{ results: Standup[]; count: number }> {
    const response = await this.api.get('/standups/standups/', { params });
    return response.data;
  }

  async getStandup(id: number): Promise<Standup> {
    const response = await this.api.get(`/standups/standups/${id}/`);
    return response.data;
  }

  async getStandupResponses(standupId: number): Promise<StandupResponse[]> {
    const response = await this.api.get(`/standups/standups/${standupId}/responses/`);
    return response.data;
  }

  async getMissingMembers(standupId: number): Promise<any[]> {
    const response = await this.api.get(`/standups/standups/${standupId}/missing_members/`);
    return response.data;
  }

  async endStandup(standupId: number): Promise<Standup> {
    const response = await this.api.post(`/standups/standups/${standupId}/end_standup/`);
    return response.data;
  }

  async submitStandupResponse(response: {
    standup: number;
    yesterday_work: string;
    today_work: string;
    blockers: string;
    mood: string;
  }): Promise<StandupResponse> {
    const apiResponse = await this.api.post('/standups/responses/', response);
    return apiResponse.data;
  }

  async getStandupResponses(): Promise<StandupResponse[]> {
    const response = await this.api.get('/standups/responses/');
    return response.data.results || response.data;
  }

  // Metrics
  async getMetrics(params?: { 
    team?: number; 
    date?: string;
    page?: number;
  }): Promise<{ results: StandupMetrics[]; count: number }> {
    const response = await this.api.get('/standups/metrics/', { params });
    return response.data;
  }

  async getTeamSummary(): Promise<any[]> {
    const response = await this.api.get('/standups/metrics/team_summary/');
    return response.data;
  }

  // Dashboard
  async getDashboardData(): Promise<DashboardData> {
    const response = await this.api.get('/standups/dashboard/');
    return response.data;
  }

  // Utility methods
  async handleApiError(error: any): Promise<ApiError> {
    if (error.response?.data) {
      return {
        message: error.response.data.message || error.response.data.detail || 'An error occurred',
        details: error.response.data.errors || error.response.data
      };
    }
    return { message: error.message || 'Network error occurred' };
  }
}

export const apiService = new ApiService();