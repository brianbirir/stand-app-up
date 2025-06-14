import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tabs,
  Tab,
  Pagination,
} from '@mui/material';
import {
  Add,
  Visibility,
  Edit,
  Stop,
  Person,
  CheckCircle,
  Cancel,
  Schedule,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { Standup, StandupResponse, Team } from '../types/api';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`simple-tabpanel-${index}`}
    aria-labelledby={`simple-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
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

const StandupsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [standups, setStandups] = useState<Standup[]>([]);
  const [responses, setResponses] = useState<StandupResponse[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filters
  const [teamFilter, setTeamFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Stand-up details dialog
  const [standupDetailsOpen, setStandupDetailsOpen] = useState(false);
  const [selectedStandup, setSelectedStandup] = useState<Standup | null>(null);
  const [standupResponses, setStandupResponses] = useState<StandupResponse[]>([]);
  const [missingMembers, setMissingMembers] = useState<any[]>([]);
  
  // Response submission dialog
  const [responseDialogOpen, setResponseDialogOpen] = useState(false);
  const [responseForm, setResponseForm] = useState({
    standup: 0,
    yesterday_work: '',
    today_work: '',
    blockers: '',
    mood: 'good',
  });

  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, [page, teamFilter, statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params: any = { page };
      if (teamFilter) params.team = teamFilter;
      if (statusFilter) params.status = statusFilter;

      const [standupsData, responsesData, teamsData] = await Promise.all([
        apiService.getStandups(params),
        apiService.getStandupResponses(),
        apiService.getTeams(),
      ]);
      
      setStandups(standupsData.results);
      setTotalPages(Math.ceil(standupsData.count / 10));
      setResponses(responsesData);
      setTeams(teamsData);
      setError(null);
    } catch (err: any) {
      setError('Failed to load stand-ups data');
      console.error('Stand-ups error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewStandup = async (standup: Standup) => {
    try {
      setSelectedStandup(standup);
      const [responsesData, missingData] = await Promise.all([
        apiService.getStandupResponses(standup.id),
        apiService.getMissingMembers(standup.id),
      ]);
      setStandupResponses(responsesData);
      setMissingMembers(missingData);
      setStandupDetailsOpen(true);
    } catch (err: any) {
      setError('Failed to load stand-up details');
    }
  };

  const handleEndStandup = async (standupId: number) => {
    if (!window.confirm('Are you sure you want to end this stand-up?')) return;
    try {
      await apiService.endStandup(standupId);
      await loadData();
    } catch (err: any) {
      setError('Failed to end stand-up');
    }
  };

  const handleSubmitResponse = async () => {
    try {
      await apiService.submitStandupResponse(responseForm);
      setResponseDialogOpen(false);
      setResponseForm({
        standup: 0,
        yesterday_work: '',
        today_work: '',
        blockers: '',
        mood: 'good',
      });
      await loadData();
    } catch (err: any) {
      setError('Failed to submit response');
    }
  };

  const openResponseDialog = (standup: Standup) => {
    setResponseForm({
      standup: standup.id,
      yesterday_work: '',
      today_work: '',
      blockers: '',
      mood: 'good',
    });
    setResponseDialogOpen(true);
  };

  const canSubmitResponse = (standup: Standup) => {
    if (standup.status !== 'in_progress') return false;
    const userResponse = standupResponses.find(r => r.standup === standup.id);
    return !userResponse;
  };

  const canManageStandup = (standup: Standup) => {
    return user?.is_staff || user?.is_superuser || 
           user?.teams?.some(t => t.team.id === standup.team.id && (t.role === 'lead' || t.role === 'admin'));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Stand-ups
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="All Stand-ups" />
          <Tab label="My Responses" />
        </Tabs>
      </Box>

      {/* All Stand-ups Tab */}
      <TabPanel value={activeTab} index={0}>
        {/* Filters */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Filter by Team</InputLabel>
              <Select
                value={teamFilter}
                onChange={(e) => {
                  setTeamFilter(e.target.value);
                  setPage(1);
                }}
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
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Filter by Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Team</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Completion</TableCell>
                <TableCell>Responses</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {standups.map((standup) => (
                <TableRow key={standup.id}>
                  <TableCell>{standup.team.name}</TableCell>
                  <TableCell>{format(new Date(standup.date), 'MMM dd, yyyy')}</TableCell>
                  <TableCell>
                    <Chip
                      label={standup.status.replace('_', ' ')}
                      color={
                        standup.status === 'completed' ? 'success' :
                        standup.status === 'in_progress' ? 'warning' :
                        standup.status === 'cancelled' ? 'error' :
                        'default'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={`${standup.completion_rate.toFixed(0)}%`}
                      variant="outlined"
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {standup.response_count}/{standup.response_count + standup.missing_count}
                  </TableCell>
                  <TableCell>
                    {standup.started_at 
                      ? format(new Date(standup.started_at), 'HH:mm')
                      : 'Not started'
                    }
                  </TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleViewStandup(standup)} title="View Details">
                      <Visibility />
                    </IconButton>
                    {canSubmitResponse(standup) && (
                      <IconButton onClick={() => openResponseDialog(standup)} title="Submit Response">
                        <Edit />
                      </IconButton>
                    )}
                    {canManageStandup(standup) && standup.status === 'in_progress' && (
                      <IconButton onClick={() => handleEndStandup(standup.id)} title="End Stand-up">
                        <Stop />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, newPage) => setPage(newPage)}
              color="primary"
            />
          </Box>
        )}
      </TabPanel>

      {/* My Responses Tab */}
      <TabPanel value={activeTab} index={1}>
        <Typography variant="h6" gutterBottom>
          My Recent Responses
        </Typography>
        
        {responses.length === 0 ? (
          <Alert severity="info">
            You haven't submitted any responses yet.
          </Alert>
        ) : (
          <Grid container spacing={2}>
            {responses.slice(0, 12).map((response) => (
              <Grid item xs={12} md={6} lg={4} key={response.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" component="div">
                        {response.standup_info.team_name}
                      </Typography>
                      <Chip
                        label={getMoodIcon(response.mood)}
                        color={getMoodColor(response.mood) as any}
                        size="small"
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {format(new Date(response.standup_info.date), 'MMM dd, yyyy')}
                    </Typography>
                    
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Yesterday:
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {response.yesterday_work.substring(0, 100)}
                        {response.yesterday_work.length > 100 && '...'}
                      </Typography>
                      
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Today:
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {response.today_work.substring(0, 100)}
                        {response.today_work.length > 100 && '...'}
                      </Typography>
                      
                      {response.blockers && (
                        <>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            Blockers:
                          </Typography>
                          <Typography variant="body2" sx={{ mb: 2 }}>
                            {response.blockers.substring(0, 100)}
                            {response.blockers.length > 100 && '...'}
                          </Typography>
                        </>
                      )}
                      
                      <Typography variant="caption" color="text.secondary">
                        Submitted: {format(new Date(response.submitted_at), 'MMM dd, HH:mm')}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Stand-up Details Dialog */}
      <Dialog 
        open={standupDetailsOpen} 
        onClose={() => setStandupDetailsOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          Stand-up Details - {selectedStandup?.team.name} - {selectedStandup && format(new Date(selectedStandup.date), 'MMM dd, yyyy')}
        </DialogTitle>
        <DialogContent>
          {selectedStandup && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={3}>
                  <Typography variant="body2" color="text.secondary">Status</Typography>
                  <Chip
                    label={selectedStandup.status.replace('_', ' ')}
                    color={
                      selectedStandup.status === 'completed' ? 'success' :
                      selectedStandup.status === 'in_progress' ? 'warning' :
                      'default'
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="body2" color="text.secondary">Completion Rate</Typography>
                  <Typography variant="h6">{selectedStandup.completion_rate.toFixed(0)}%</Typography>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="body2" color="text.secondary">Responses</Typography>
                  <Typography variant="h6">{selectedStandup.response_count}</Typography>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Typography variant="body2" color="text.secondary">Missing</Typography>
                  <Typography variant="h6">{selectedStandup.missing_count}</Typography>
                </Grid>
              </Grid>

              <Typography variant="h6" gutterBottom>
                Responses ({standupResponses.length})
              </Typography>
              
              {standupResponses.length === 0 ? (
                <Alert severity="info">No responses yet.</Alert>
              ) : (
                <List>
                  {standupResponses.map((response) => (
                    <ListItem key={response.id} divider>
                      <ListItemIcon>
                        <Person />
                      </ListItemIcon>
                      <ListItemText
                        primary={response.user.full_name || response.user.username}
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2">
                              <strong>Today:</strong> {response.today_work}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              <strong>Yesterday:</strong> {response.yesterday_work}
                            </Typography>
                            {response.blockers && (
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                <strong>Blockers:</strong> {response.blockers}
                              </Typography>
                            )}
                            <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                              <Chip
                                label={getMoodIcon(response.mood)}
                                color={getMoodColor(response.mood) as any}
                                size="small"
                              />
                              <Typography variant="caption" color="text.secondary">
                                {format(new Date(response.submitted_at), 'HH:mm')}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}

              {missingMembers.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Missing Responses ({missingMembers.length})
                  </Typography>
                  <List>
                    {missingMembers.map((member, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Cancel color="error" />
                        </ListItemIcon>
                        <ListItemText
                          primary={member.user?.full_name || member.user?.username || 'Unknown User'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStandupDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Response Submission Dialog */}
      <Dialog 
        open={responseDialogOpen} 
        onClose={() => setResponseDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Submit Stand-up Response</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="What did you accomplish yesterday?"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={responseForm.yesterday_work}
            onChange={(e) => setResponseForm({ ...responseForm, yesterday_work: e.target.value })}
          />
          
          <TextField
            margin="dense"
            label="What will you work on today?"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={responseForm.today_work}
            onChange={(e) => setResponseForm({ ...responseForm, today_work: e.target.value })}
          />
          
          <TextField
            margin="dense"
            label="Any blockers or challenges?"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={responseForm.blockers}
            onChange={(e) => setResponseForm({ ...responseForm, blockers: e.target.value })}
            helperText="Optional: Mention any issues that are blocking your progress"
          />
          
          <FormControl fullWidth margin="dense">
            <InputLabel>How are you feeling today?</InputLabel>
            <Select
              value={responseForm.mood}
              onChange={(e) => setResponseForm({ ...responseForm, mood: e.target.value })}
            >
              <MenuItem value="great">😄 Great</MenuItem>
              <MenuItem value="good">😊 Good</MenuItem>
              <MenuItem value="okay">😐 Okay</MenuItem>
              <MenuItem value="stressed">😰 Stressed</MenuItem>
              <MenuItem value="blocked">😵 Blocked</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResponseDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitResponse}
            variant="contained"
            disabled={!responseForm.yesterday_work || !responseForm.today_work}
          >
            Submit Response
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StandupsPage;