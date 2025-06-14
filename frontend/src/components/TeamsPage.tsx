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
  Tabs,
  Tab,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  FormGroup,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  People,
  Schedule as ScheduleIcon,
  PersonAdd,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { Team, TeamMembership, StandupSchedule } from '../types/api';
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

const TeamsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [teams, setTeams] = useState<Team[]>([]);
  const [schedules, setSchedules] = useState<StandupSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Team dialogs
  const [teamDialogOpen, setTeamDialogOpen] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamForm, setTeamForm] = useState({
    name: '',
    description: '',
    slack_channel_id: '',
  });

  // Member dialogs
  const [memberDialogOpen, setMemberDialogOpen] = useState(false);
  const [teamMembers, setTeamMembers] = useState<TeamMembership[]>([]);
  const [memberForm, setMemberForm] = useState({
    username: '',
    slack_user_id: '',
    role: 'member',
  });

  // Schedule dialogs
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<StandupSchedule | null>(null);
  const [scheduleForm, setScheduleForm] = useState({
    team: '',
    weekdays: [] as number[],
    reminder_time: '09:00',
    end_time: '17:00',
    timezone: 'UTC',
  });

  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [teamsData, schedulesData] = await Promise.all([
        apiService.getTeams(),
        apiService.getTeamSchedules(),
      ]);
      setTeams(teamsData);
      setSchedules(schedulesData);
      setError(null);
    } catch (err: any) {
      setError('Failed to load teams data');
      console.error('Teams error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeam = async () => {
    try {
      await apiService.createTeam(teamForm);
      await loadData();
      setTeamDialogOpen(false);
      setTeamForm({ name: '', description: '', slack_channel_id: '' });
    } catch (err: any) {
      setError('Failed to create team');
    }
  };

  const handleUpdateTeam = async () => {
    if (!selectedTeam) return;
    try {
      await apiService.updateTeam(selectedTeam.id, teamForm);
      await loadData();
      setTeamDialogOpen(false);
      setSelectedTeam(null);
      setTeamForm({ name: '', description: '', slack_channel_id: '' });
    } catch (err: any) {
      setError('Failed to update team');
    }
  };

  const handleDeleteTeam = async (teamId: number) => {
    if (!window.confirm('Are you sure you want to delete this team?')) return;
    try {
      await apiService.deleteTeam(teamId);
      await loadData();
    } catch (err: any) {
      setError('Failed to delete team');
    }
  };

  const openTeamDialog = (team?: Team) => {
    if (team) {
      setSelectedTeam(team);
      setTeamForm({
        name: team.name,
        description: team.description,
        slack_channel_id: team.slack_channel_id,
      });
    } else {
      setSelectedTeam(null);
      setTeamForm({ name: '', description: '', slack_channel_id: '' });
    }
    setTeamDialogOpen(true);
  };

  const openMemberDialog = async (team: Team) => {
    try {
      const members = await apiService.getTeamMembers(team.id);
      setTeamMembers(members);
      setSelectedTeam(team);
      setMemberForm({ username: '', slack_user_id: '', role: 'member' });
      setMemberDialogOpen(true);
    } catch (err: any) {
      setError('Failed to load team members');
    }
  };

  const handleAddMember = async () => {
    if (!selectedTeam) return;
    try {
      await apiService.addTeamMember(selectedTeam.id, memberForm);
      const members = await apiService.getTeamMembers(selectedTeam.id);
      setTeamMembers(members);
      setMemberForm({ username: '', slack_user_id: '', role: 'member' });
    } catch (err: any) {
      setError('Failed to add team member');
    }
  };

  const openScheduleDialog = (schedule?: StandupSchedule) => {
    if (schedule) {
      setSelectedSchedule(schedule);
      setScheduleForm({
        team: schedule.team.toString(),
        weekdays: schedule.weekdays,
        reminder_time: schedule.reminder_time,
        end_time: schedule.end_time,
        timezone: schedule.timezone,
      });
    } else {
      setSelectedSchedule(null);
      setScheduleForm({
        team: '',
        weekdays: [1, 2, 3, 4, 5], // Monday to Friday
        reminder_time: '09:00',
        end_time: '17:00',
        timezone: 'UTC',
      });
    }
    setScheduleDialogOpen(true);
  };

  const handleCreateSchedule = async () => {
    try {
      const scheduleData = {
        ...scheduleForm,
        team: parseInt(scheduleForm.team),
      };
      await apiService.createSchedule(scheduleData);
      await loadData();
      setScheduleDialogOpen(false);
    } catch (err: any) {
      setError('Failed to create schedule');
    }
  };

  const handleUpdateSchedule = async () => {
    if (!selectedSchedule) return;
    try {
      const scheduleData = {
        ...scheduleForm,
        team: parseInt(scheduleForm.team),
      };
      await apiService.updateSchedule(selectedSchedule.id, scheduleData);
      await loadData();
      setScheduleDialogOpen(false);
      setSelectedSchedule(null);
    } catch (err: any) {
      setError('Failed to update schedule');
    }
  };

  const handleDeleteSchedule = async (scheduleId: number) => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) return;
    try {
      await apiService.deleteSchedule(scheduleId);
      await loadData();
    } catch (err: any) {
      setError('Failed to delete schedule');
    }
  };

  const weekdayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const handleWeekdayChange = (day: number) => {
    const newWeekdays = scheduleForm.weekdays.includes(day)
      ? scheduleForm.weekdays.filter(d => d !== day)
      : [...scheduleForm.weekdays, day].sort();
    setScheduleForm({ ...scheduleForm, weekdays: newWeekdays });
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
        Teams Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Teams" />
          <Tab label="Schedules" />
        </Tabs>
      </Box>

      {/* Teams Tab */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6">Teams</Typography>
          {(user?.is_staff || user?.is_superuser) && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => openTeamDialog()}
            >
              Create Team
            </Button>
          )}
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Slack Channel</TableCell>
                <TableCell>Members</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {teams.map((team) => (
                <TableRow key={team.id}>
                  <TableCell>{team.name}</TableCell>
                  <TableCell>{team.description}</TableCell>
                  <TableCell>{team.slack_channel_id || 'Not set'}</TableCell>
                  <TableCell>{team.member_count}</TableCell>
                  <TableCell>
                    <Chip
                      label={team.is_active ? 'Active' : 'Inactive'}
                      color={team.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton onClick={() => openMemberDialog(team)} title="Manage Members">
                      <People />
                    </IconButton>
                    {(user?.is_staff || user?.is_superuser) && (
                      <>
                        <IconButton onClick={() => openTeamDialog(team)} title="Edit Team">
                          <Edit />
                        </IconButton>
                        <IconButton onClick={() => handleDeleteTeam(team.id)} title="Delete Team">
                          <Delete />
                        </IconButton>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Schedules Tab */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6">Stand-up Schedules</Typography>
          {(user?.is_staff || user?.is_superuser) && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => openScheduleDialog()}
            >
              Create Schedule
            </Button>
          )}
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Team</TableCell>
                <TableCell>Weekdays</TableCell>
                <TableCell>Reminder Time</TableCell>
                <TableCell>End Time</TableCell>
                <TableCell>Timezone</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell>{schedule.team_name}</TableCell>
                  <TableCell>
                    {schedule.weekday_names.join(', ')}
                  </TableCell>
                  <TableCell>{schedule.reminder_time}</TableCell>
                  <TableCell>{schedule.end_time}</TableCell>
                  <TableCell>{schedule.timezone}</TableCell>
                  <TableCell>
                    <Chip
                      label={schedule.is_active ? 'Active' : 'Inactive'}
                      color={schedule.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {(user?.is_staff || user?.is_superuser) && (
                      <>
                        <IconButton onClick={() => openScheduleDialog(schedule)} title="Edit Schedule">
                          <Edit />
                        </IconButton>
                        <IconButton onClick={() => handleDeleteSchedule(schedule.id)} title="Delete Schedule">
                          <Delete />
                        </IconButton>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Team Dialog */}
      <Dialog open={teamDialogOpen} onClose={() => setTeamDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedTeam ? 'Edit Team' : 'Create Team'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Team Name"
            fullWidth
            variant="outlined"
            value={teamForm.name}
            onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={teamForm.description}
            onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Slack Channel ID"
            fullWidth
            variant="outlined"
            value={teamForm.slack_channel_id}
            onChange={(e) => setTeamForm({ ...teamForm, slack_channel_id: e.target.value })}
            helperText="Optional: Slack channel ID for notifications"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTeamDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={selectedTeam ? handleUpdateTeam : handleCreateTeam}
            variant="contained"
          >
            {selectedTeam ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Member Dialog */}
      <Dialog open={memberDialogOpen} onClose={() => setMemberDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Manage Team Members - {selectedTeam?.name}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Username"
                fullWidth
                variant="outlined"
                size="small"
                value={memberForm.username}
                onChange={(e) => setMemberForm({ ...memberForm, username: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Slack User ID"
                fullWidth
                variant="outlined"
                size="small"
                value={memberForm.slack_user_id}
                onChange={(e) => setMemberForm({ ...memberForm, slack_user_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Role</InputLabel>
                <Select
                  value={memberForm.role}
                  onChange={(e) => setMemberForm({ ...memberForm, role: e.target.value })}
                >
                  <MenuItem value="member">Member</MenuItem>
                  <MenuItem value="lead">Lead</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleAddMember}
                startIcon={<PersonAdd />}
              >
                Add
              </Button>
            </Grid>
          </Grid>

          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Slack ID</TableCell>
                  <TableCell>Joined</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {teamMembers.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>{member.user?.full_name || member.user?.username || 'Unknown'}</TableCell>
                    <TableCell>
                      <Chip label={member.role} size="small" />
                    </TableCell>
                    <TableCell>{member.slack_user_id || 'Not set'}</TableCell>
                    <TableCell>{format(new Date(member.joined_at), 'MMM dd, yyyy')}</TableCell>
                    <TableCell>
                      <Chip
                        label={member.is_active ? 'Active' : 'Inactive'}
                        color={member.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMemberDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog open={scheduleDialogOpen} onClose={() => setScheduleDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedSchedule ? 'Edit Schedule' : 'Create Schedule'}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Team</InputLabel>
            <Select
              value={scheduleForm.team}
              onChange={(e) => setScheduleForm({ ...scheduleForm, team: e.target.value })}
            >
              {teams.map((team) => (
                <MenuItem key={team.id} value={team.id.toString()}>
                  {team.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Weekdays
          </Typography>
          <FormGroup row>
            {weekdayNames.map((day, index) => (
              <FormControlLabel
                key={index}
                control={
                  <Checkbox
                    checked={scheduleForm.weekdays.includes(index + 1)}
                    onChange={() => handleWeekdayChange(index + 1)}
                  />
                }
                label={day}
              />
            ))}
          </FormGroup>

          <TextField
            margin="dense"
            label="Reminder Time"
            type="time"
            fullWidth
            variant="outlined"
            value={scheduleForm.reminder_time}
            onChange={(e) => setScheduleForm({ ...scheduleForm, reminder_time: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            margin="dense"
            label="End Time"
            type="time"
            fullWidth
            variant="outlined"
            value={scheduleForm.end_time}
            onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            margin="dense"
            label="Timezone"
            fullWidth
            variant="outlined"
            value={scheduleForm.timezone}
            onChange={(e) => setScheduleForm({ ...scheduleForm, timezone: e.target.value })}
            helperText="e.g., UTC, America/New_York, Europe/London"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScheduleDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={selectedSchedule ? handleUpdateSchedule : handleCreateSchedule}
            variant="contained"
          >
            {selectedSchedule ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeamsPage;