import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  People,
  Schedule,
  EmojiEvents,
  CheckCircle,
  Cancel,
  AccessTime,
  Mood,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { DashboardData, Standup, StandupResponse } from '../types/api';
import { apiService } from '../services/api';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactElement;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color = 'primary' }) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        </Box>
        <Box sx={{ color: `${color}.main` }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const getMoodColor = (mood: string) => {
  switch (mood) {
    case 'great': return 'success';
    case 'good': return 'info';
    case 'okay': return 'warning';
    case 'stressed': return 'error';
    case 'blocked': return 'error';
    default: return 'default';
  }
};

const getMoodIcon = (mood: string) => {
  switch (mood) {
    case 'great': return '😄';
    case 'good': return '😊';
    case 'okay': return '😐';
    case 'stressed': return '😰';
    case 'blocked': return '😵';
    default: return '❓';
  }
};

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDashboardData();
      setDashboardData(data);
      setError(null);
    } catch (err: any) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No dashboard data available
      </Alert>
    );
  }

  const { user_stats, team_stats, recent_standups, recent_responses } = dashboardData;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* User Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Teams"
            value={user_stats.teams_count}
            icon={<People fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="This Week"
            value={user_stats.responses_this_week}
            icon={<Schedule fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Streak"
            value={user_stats.current_streak}
            icon={<EmojiEvents fontSize="large" />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Mood"
            value={user_stats.avg_mood_this_week.toFixed(1)}
            icon={<Mood fontSize="large" />}
            color="secondary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Team Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Team Performance This Week
              </Typography>
              {team_stats.length === 0 ? (
                <Typography color="textSecondary">
                  No team data available
                </Typography>
              ) : (
                <List>
                  {team_stats.map((team, index) => (
                    <ListItem key={index} divider>
                      <ListItemText
                        primary={team.team.name}
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="textSecondary">
                              {team.standups_this_week} stand-ups • {team.avg_completion_rate.toFixed(1)}% completion
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                              <Chip
                                size="small"
                                label={`Your participation: ${team.user_participation}/${team.standups_this_week}`}
                                color={team.user_participation === team.standups_this_week ? 'success' : 'warning'}
                              />
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemIcon>
                        {team.avg_completion_rate >= 80 ? (
                          <CheckCircle color="success" />
                        ) : team.avg_completion_rate >= 60 ? (
                          <AccessTime color="warning" />
                        ) : (
                          <Cancel color="error" />
                        )}
                      </ListItemIcon>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Stand-ups */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Stand-ups
              </Typography>
              {recent_standups.length === 0 ? (
                <Typography color="textSecondary">
                  No recent stand-ups
                </Typography>
              ) : (
                <List>
                  {recent_standups.slice(0, 5).map((standup) => (
                    <ListItem key={standup.id} divider>
                      <ListItemText
                        primary={standup.team.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {format(new Date(standup.date), 'MMM dd, yyyy')}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                              <Chip
                                size="small"
                                label={standup.status}
                                color={
                                  standup.status === 'completed' ? 'success' :
                                  standup.status === 'in_progress' ? 'warning' :
                                  'default'
                                }
                              />
                              <Chip
                                size="small"
                                label={`${standup.completion_rate.toFixed(0)}% complete`}
                                variant="outlined"
                              />
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Responses */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Responses
              </Typography>
              {recent_responses.length === 0 ? (
                <Typography color="textSecondary">
                  No recent responses
                </Typography>
              ) : (
                <List>
                  {recent_responses.slice(0, 8).map((response) => (
                    <ListItem key={response.id} divider>
                      <ListItemText
                        primary={`${response.user.full_name} - ${response.standup_info.team_name}`}
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="textSecondary" noWrap>
                              <strong>Today:</strong> {response.today_work.substring(0, 100)}
                              {response.today_work.length > 100 && '...'}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Typography variant="caption" color="textSecondary">
                                {format(new Date(response.submitted_at), 'MMM dd, HH:mm')}
                              </Typography>
                              <Tooltip title={`Mood: ${response.mood}`}>
                                <Chip
                                  size="small"
                                  label={getMoodIcon(response.mood)}
                                  color={getMoodColor(response.mood) as any}
                                />
                              </Tooltip>
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;