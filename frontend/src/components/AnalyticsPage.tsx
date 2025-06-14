import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  People,
  Schedule,
  Mood,
} from '@mui/icons-material';
import { format, subDays, subWeeks, subMonths } from 'date-fns';
import { Team, AnalyticsData } from '../types/api';
import { apiService } from '../services/api';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactElement;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color = 'primary' }) => (
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
          {change !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {change >= 0 ? (
                <TrendingUp color="success" fontSize="small" />
              ) : (
                <TrendingDown color="error" fontSize="small" />
              )}
              <Typography
                variant="body2"
                color={change >= 0 ? 'success.main' : 'error.main'}
                sx={{ ml: 0.5 }}
              >
                {change > 0 ? '+' : ''}{change.toFixed(1)}%
              </Typography>
            </Box>
          )}
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

const AnalyticsPage: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [timeRange, setTimeRange] = useState('week');
  const [teamFilter, setTeamFilter] = useState('');

  useEffect(() => {
    loadData();
  }, [timeRange, teamFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params: any = { time_range: timeRange };
      if (teamFilter) params.team = teamFilter;

      const [analyticsResponse, teamsData] = await Promise.all([
        apiService.getAnalytics(params),
        apiService.getTeams(),
      ]);
      
      setAnalyticsData(analyticsResponse);
      setTeams(teamsData);
      setError(null);
    } catch (err: any) {
      setError('Failed to load analytics data');
      console.error('Analytics error:', err);
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

  if (!analyticsData) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No analytics data available
      </Alert>
    );
  }

  const { overview, participation_trends, team_performance, mood_analysis, response_patterns } = analyticsData;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics
      </Typography>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="week">Last Week</MenuItem>
              <MenuItem value="month">Last Month</MenuItem>
              <MenuItem value="quarter">Last Quarter</MenuItem>
              <MenuItem value="year">Last Year</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Team</InputLabel>
            <Select
              value={teamFilter}
              onChange={(e) => setTeamFilter(e.target.value)}
            >
              <MenuItem value="">All Teams</MenuItem>
              {teams.map((team) => (
                <MenuItem key={team.id} value={team.id.toString()}>
                  {team.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Overview Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Stand-ups"
            value={overview.total_standups}
            change={overview.standups_change}
            icon={<Schedule fontSize="large" />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Participation"
            value={`${overview.avg_participation_rate.toFixed(1)}%`}
            change={overview.participation_change}
            icon={<People fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Responses"
            value={overview.total_responses}
            change={overview.responses_change}
            icon={<Assessment fontSize="large" />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Mood Score"
            value={overview.avg_mood_score.toFixed(1)}
            change={overview.mood_change}
            icon={<Mood fontSize="large" />}
            color="warning"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Participation Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Participation Trends
              </Typography>
              {participation_trends.length === 0 ? (
                <Typography color="textSecondary">
                  No participation data available
                </Typography>
              ) : (
                <Box>
                  {participation_trends.map((trend, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">
                          {format(new Date(trend.date), 'MMM dd')}
                        </Typography>
                        <Typography variant="body2">
                          {trend.participation_rate.toFixed(1)}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={trend.participation_rate}
                        sx={{ height: 8, borderRadius: 4 }}
                        color={
                          trend.participation_rate >= 80 ? 'success' :
                          trend.participation_rate >= 60 ? 'warning' :
                          'error'
                        }
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Mood Distribution */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Mood Distribution
              </Typography>
              {mood_analysis.mood_distribution.length === 0 ? (
                <Typography color="textSecondary">
                  No mood data available
                </Typography>
              ) : (
                <Box>
                  {mood_analysis.mood_distribution.map((mood, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Chip
                            label={mood.mood}
                            color={getMoodColor(mood.mood) as any}
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        </Box>
                        <Typography variant="body2">
                          {mood.count} ({mood.percentage.toFixed(1)}%)
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={mood.percentage}
                        sx={{ height: 6, borderRadius: 3 }}
                        color={getMoodColor(mood.mood) as any}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Team Performance */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Team Performance
              </Typography>
              {team_performance.length === 0 ? (
                <Typography color="textSecondary">
                  No team performance data available
                </Typography>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Team</TableCell>
                        <TableCell>Stand-ups</TableCell>
                        <TableCell>Avg Participation</TableCell>
                        <TableCell>Total Responses</TableCell>
                        <TableCell>Avg Mood</TableCell>
                        <TableCell>Response Time</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {team_performance.map((team) => (
                        <TableRow key={team.team_name}>
                          <TableCell>{team.team_name}</TableCell>
                          <TableCell>{team.standups_count}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Typography variant="body2" sx={{ mr: 1 }}>
                                {team.avg_participation_rate.toFixed(1)}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={team.avg_participation_rate}
                                sx={{ width: 60, height: 4 }}
                                color={
                                  team.avg_participation_rate >= 80 ? 'success' :
                                  team.avg_participation_rate >= 60 ? 'warning' :
                                  'error'
                                }
                              />
                            </Box>
                          </TableCell>
                          <TableCell>{team.total_responses}</TableCell>
                          <TableCell>
                            <Chip
                              label={team.avg_mood_score.toFixed(1)}
                              size="small"
                              color={
                                team.avg_mood_score >= 4 ? 'success' :
                                team.avg_mood_score >= 3 ? 'warning' :
                                'error'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            {team.avg_response_time ? `${team.avg_response_time.toFixed(1)}h` : 'N/A'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={
                                team.avg_participation_rate >= 80 ? 'Excellent' :
                                team.avg_participation_rate >= 60 ? 'Good' :
                                'Needs Attention'
                              }
                              color={
                                team.avg_participation_rate >= 80 ? 'success' :
                                team.avg_participation_rate >= 60 ? 'warning' :
                                'error'
                              }
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Response Patterns */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Response Time Patterns
              </Typography>
              {response_patterns.hourly_distribution.length === 0 ? (
                <Typography color="textSecondary">
                  No response time data available
                </Typography>
              ) : (
                <Box>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Peak response hours
                  </Typography>
                  {response_patterns.hourly_distribution.slice(0, 5).map((pattern, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">
                          {pattern.hour}:00
                        </Typography>
                        <Typography variant="body2">
                          {pattern.count} responses
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(pattern.count / Math.max(...response_patterns.hourly_distribution.map(p => p.count))) * 100}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Weekly Patterns */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Weekly Patterns
              </Typography>
              {response_patterns.daily_distribution.length === 0 ? (
                <Typography color="textSecondary">
                  No weekly pattern data available
                </Typography>
              ) : (
                <Box>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Response distribution by day
                  </Typography>
                  {response_patterns.daily_distribution.map((pattern, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">
                          {pattern.day_name}
                        </Typography>
                        <Typography variant="body2">
                          {pattern.count} responses
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(pattern.count / Math.max(...response_patterns.daily_distribution.map(p => p.count))) * 100}
                        sx={{ height: 6, borderRadius: 3 }}
                        color={
                          pattern.day_name === 'Monday' || pattern.day_name === 'Friday' ? 'warning' : 'primary'
                        }
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AnalyticsPage;