import { EnrolledSubject, RecognitionEvent, CameraFeed, SystemMetrics, SecurityUser } from '../types';

export const INITIAL_SECURITY_USER: SecurityUser = {
  id: 'usr-00001',
  name: 'Security Operator',
  email: 'operator@sec.internal',
  badgeNumber: 'SEC-00001',
  role: 'Security Officer',
  department: 'Security Command Center',
  avatarUrl: '',
  isAuthenticated: true,
  loginMethod: 'Smart Card',
  mfaVerified: true,
  lastLogin: 'Active Session',
};

export const INITIAL_METRICS: SystemMetrics = {
  activeCameras: 0,
  totalCameras: 0,
  aiEngineLoadPct: 0,
  avgInferenceLatencyMs: 0,
  maskedAccuracyPct: 0,
  totalDetections24h: 0,
  maskCompliancePct: 0,
  watchlistAlerts24h: 0,
  enrolledSubjectsCount: 0,
};

export const INITIAL_CAMERAS: CameraFeed[] = [];

export const INITIAL_ENROLLED_SUBJECTS: EnrolledSubject[] = [];

export const INITIAL_LOGS: RecognitionEvent[] = [];
