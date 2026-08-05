export type NavigationModule = 
  | 'dashboard'
  | 'enrollment'
  | 'live-recognition'
  | 'identity-gallery'
  | 'history'
  | 'analytics'
  | 'settings';

export type UserRole = 'Admin' | 'Security Officer' | 'Auditor' | 'System Operator';

export interface SecurityUser {
  id: string;
  name: string;
  email: string;
  badgeNumber: string;
  role: UserRole;
  department: string;
  avatarUrl: string;
  isAuthenticated: boolean;
  loginMethod: 'OAuth Google' | 'Okta SSO' | 'Smart Card' | 'PIN';
  mfaVerified: boolean;
  lastLogin: string;
}

export type SubjectCategory = 'Employee' | 'Contractor' | 'VIP' | 'Watchlist' | 'Restricted' | 'Visitor';

export interface EnrolledSubject {
  id: string;
  fullName: string;
  badgeId: string;
  category: SubjectCategory;
  clearanceLevel: 'Level 1' | 'Level 2' | 'Level 3' | 'Top Secret';
  department: string;
  unmaskedPhotoUrl: string;
  maskedPhotoUrl: string;
  enrolledDate: string;
  enrolledBy: string;
  status: 'Active' | 'Suspended' | 'Revoked';
  riskRating: 'Low' | 'Medium' | 'High' | 'Critical';
  notes: string;
  embeddingVectorPreview: number[]; // 8-16 visual weights for UI vector graphs
  lastSeenLocation?: string;
  lastSeenTime?: string;
}

export type MaskType = 'N95 Respirator' | 'Surgical Mask' | 'Cloth Mask' | 'Balaclava / Gaiter' | 'Face Shield' | 'No Mask' | 'Partial / Improper';

export interface RecognitionEvent {
  id: string;
  timestamp: string;
  cameraId: string;
  cameraName: string;
  zone: string;
  subjectId?: string;
  subjectName: string;
  subjectCategory: SubjectCategory;
  matchConfidence: number; // e.g. 97.8
  maskDetected: MaskType;
  maskCorrectlyWorn: boolean;
  facialOcclusionPercent: number; // e.g. 55%
  snapshotUrl: string;
  riskLevel: 'Normal' | 'Info' | 'Warning' | 'Critical';
  flaggedByOfficer: boolean;
  verificationStatus: 'Verified' | 'Pending Review' | 'False Positive' | 'Dismissed';
  notes?: string;
}

export interface CameraFeed {
  id: string;
  name: string;
  zone: string;
  status: 'Online' | 'Offline' | 'Degraded';
  resolution: string;
  fps: number;
  aiLatencyMs: number;
  totalDetectionsToday: number;
  maskedCountToday: number;
  watchlistHitsToday: number;
  streamType: 'RTSP' | 'Webcam' | 'Simulated Loop';
  streamUrl?: string;
}

export interface SystemMetrics {
  activeCameras: number;
  totalCameras: number;
  aiEngineLoadPct: number;
  avgInferenceLatencyMs: number;
  maskedAccuracyPct: number;
  totalDetections24h: number;
  maskCompliancePct: number;
  watchlistAlerts24h: number;
  enrolledSubjectsCount?: number;
}

export interface AIAnalysisRequest {
  type: 'incident-summary' | 'risk-assessment' | 'log-audit' | 'system-health';
  logs?: RecognitionEvent[];
  queryContext?: string;
}

export interface AIAnalysisResponse {
  summary: string;
  threatLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'ELEVATED';
  keyInsights: string[];
  recommendedActions: string[];
}
