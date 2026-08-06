import axios from 'axios';
import { useQuery, useMutation } from '@tanstack/react-query';
import type { UseMutationResult } from '@tanstack/react-query';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface HealthResponse {
  status: string;
  version: string;
}

export interface RuntimeStatsResponse {
  state: string;
  total_frames_processed: number;
  total_recognitions: number;
  total_unknowns: number;
  errors: number;
  uptime_seconds: number;
  average_fps: number;
}

export interface SystemHealthResponse {
  health: string;
  gpu: {
    available: boolean;
    device_name: string;
    vram_total_mb: number;
    vram_used_mb: number;
    vram_free_mb: number;
  };
  models: Array<{
    name: string;
    type: string;
    status: string;
    latency_ms: number;
    device: string;
  }>;
}

export const useBackendHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>('/health/live');
      return data;
    },
    refetchInterval: 10000,
  });
};

export const useRuntimeStats = () => {
  return useQuery({
    queryKey: ['runtime_stats'],
    queryFn: async () => {
      const { data } = await apiClient.get<RuntimeStatsResponse>('/api/v1/runtime/stats');
      return data;
    },
    refetchInterval: 5000,
  });
};

export const useStartRuntime = (): UseMutationResult<BaseResponse, Error, void> => {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<BaseResponse>('/api/v1/runtime/start');
      return response.data;
    },
  });
};

export const useStopRuntime = (): UseMutationResult<BaseResponse, Error, void> => {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<BaseResponse>('/api/v1/runtime/stop');
      return response.data;
    },
  });
};

export const useSystemInfo = () => {
  return useQuery({
    queryKey: ['system_info'],
    queryFn: async () => {
      const { data } = await apiClient.get<SystemHealthResponse>('/api/v1/system/info');
      return data;
    },
    refetchInterval: 5000,
  });
};

export interface EnrollmentRequest {
  identity_id: string;
  name: string;
  files: Blob[]; 
}

export interface EnrollmentResponse {
  success: boolean;
  identity_id?: string;
  message?: string;
  error_msg?: string;
}

export const useEnrollPerson = (): UseMutationResult<EnrollmentResponse, Error, EnrollmentRequest> => {
  return useMutation({
    mutationFn: async (data: EnrollmentRequest) => {
      const formData = new FormData();
      formData.append('identity_id', data.identity_id);
      formData.append('name', data.name);
      data.files.forEach((file, index) => {
        formData.append('files', file, `capture_${index}.jpg`);
      });

      const response = await apiClient.post<EnrollmentResponse>('/api/v1/enrollment', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  });
};

export interface IdentityModel {
  identity_id: string;
  name: string;
  department?: string;
  notes?: string;
  is_active: boolean;
  recognition_count: number;
  last_seen?: string;
  enrollment_date: string;
}

export interface BaseResponse {
  success: boolean;
  message?: string;
}

export const useIdentities = () => {
  return useQuery({
    queryKey: ['identities'],
    queryFn: async () => {
      const { data } = await apiClient.get<IdentityModel[]>('/api/v1/enrollment');
      return data;
    },
  });
};

export const useUpdateIdentity = (): UseMutationResult<BaseResponse, Error, { id: string, data: { name?: string, department?: string, notes?: string } }> => {
  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put<BaseResponse>(`/api/v1/enrollment/${id}`, data);
      return response.data;
    },
  });
};

export const useDeleteIdentity = (): UseMutationResult<BaseResponse, Error, string> => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.delete<BaseResponse>(`/api/v1/enrollment/${id}`);
      return response.data;
    },
  });
};

export interface HistoryRecord {
  history_id: string;
  timestamp: string;
  identity_id?: string;
  name?: string;
  department?: string;
  verification_score: number;
  mode: string;
  camera_id: string;
  tracking_id: string;
  processing_time_ms: number;
  state: string;
  has_mask: boolean;
}

export interface HistoryResponse {
  success: boolean;
  total: number;
  limit: number;
  offset: number;
  records: HistoryRecord[];
}

export const useHistory = (limit: number = 50, offset: number = 0, search: string = '') => {
  return useQuery({
    queryKey: ['history', limit, offset, search],
    queryFn: async () => {
      const { data } = await apiClient.get<HistoryResponse>('/api/v1/history', {
        params: { limit, offset, search: search || undefined }
      });
      return data;
    },
    refetchInterval: 10000,
  });
};

export const useClearHistory = (): UseMutationResult<BaseResponse, Error, void> => {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.delete<BaseResponse>('/api/v1/history');
      return response.data;
    },
  });
};

export const useDeleteHistoryEvent = (): UseMutationResult<BaseResponse, Error, string> => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.delete<BaseResponse>(`/api/v1/history/${id}`);
      return response.data;
    },
  });
};

export interface SettingsModel {
  target_fps: number;
  max_frame_queue_size: number;
  camera_reconnect_delay_sec: number;
  batch_size: number;
  runtime_mode: string;
  theme: string;
  language: string;
  confidence_threshold: number;
  tracking_strategy: string;
  default_source: string;
  log_retention: string;
  save_unknown_faces: boolean;
}

export const useSettings = () => {
  return useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data } = await apiClient.get<SettingsModel>('/api/v1/settings');
      return data;
    },
  });
};

export const useUpdateSettings = (): UseMutationResult<BaseResponse, Error, Partial<SettingsModel>> => {
  return useMutation({
    mutationFn: async (updates) => {
      const response = await apiClient.put<BaseResponse>('/api/v1/settings', updates);
      return response.data;
    },
  });
};

export interface CameraSourceModel {
  id: string;
  name: string;
  source_type: string;
  connection_url: string;
  is_active: boolean;
  created_at: string;
}

export const useCameras = () => {
  return useQuery({
    queryKey: ['cameras'],
    queryFn: async () => {
      const { data } = await apiClient.get<CameraSourceModel[]>('/api/v1/camera');
      return data;
    },
  });
};

export const useAddCamera = (): UseMutationResult<CameraSourceModel, Error, { name: string, source_type: string, connection_url: string }> => {
  return useMutation({
    mutationFn: async (newCamera) => {
      const response = await apiClient.post<CameraSourceModel>('/api/v1/camera', newCamera);
      return response.data;
    },
  });
};

export const useSetActiveCamera = (): UseMutationResult<BaseResponse, Error, string> => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.post<BaseResponse>(`/api/v1/camera/${id}/activate`);
      return response.data;
    },
  });
};

export const useDeleteCamera = (): UseMutationResult<BaseResponse, Error, string> => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.delete<BaseResponse>(`/api/v1/camera/${id}`);
      return response.data;
    },
  });
};

export interface RecognitionResultModel {
  is_unknown: boolean;
  state: string;
  verification_score: number;
  candidate?: {
    identity_id: string;
    similarity_score: number;
    name?: string;
  };
  bbox?: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  tracking_id?: string;
  has_mask: boolean;
  processing_time_ms: number;
}

export interface BatchRecognitionResult {
  success: boolean;
  results: RecognitionResultModel[];
}

export const useBatchVerify = (): UseMutationResult<BatchRecognitionResult, Error, Blob[]> => {
  return useMutation({
    mutationFn: async (files: Blob[]) => {
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append('files', file, `verify_${index}.jpg`);
      });
      const response = await apiClient.post<BatchRecognitionResult>('/api/v1/recognition/batch', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  });
};

export const useRecognizeSingle = (): UseMutationResult<RecognitionResultModel, Error, File> => {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const response = await apiClient.post<RecognitionResultModel>('/api/v1/recognition', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
  });
};
