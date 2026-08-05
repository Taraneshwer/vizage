import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = 'ws://127.0.0.1:8000/ws';

export interface WSMessageBase {
  topic: string;
  timestamp: number;
}

export interface WSRuntimeMessage extends WSMessageBase {
  state: string;
  total_frames_processed: number;
  average_fps: number;
  total_recognitions: number;
  total_unknowns: number;
  dropped_frames: number;
  uptime_seconds?: number;
  errors?: number;
}

export interface WSSystemMessage extends WSMessageBase {
  gpu: any;
  models: any[];
  health: string;
}

export interface WSCameraMessage extends WSMessageBase {
  frame_id: string;
  camera_id: string;
  image_base64: string;
  capture_timestamp?: number;
}

export interface WSRecognitionMessage extends WSMessageBase {
  identity_id: string;
  verification_score: number;
  bbox: number[];
  tracking_id: string;
  mask_status: boolean;
  recognition_mode: string;
  processing_time_ms: number;
  capture_timestamp?: number;
}

export interface WSHistoryMessage extends WSMessageBase {
  history_id: string;
  event_timestamp: string;
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

export function useWebSocket<T>(topic: string) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE_URL}/${topic}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      reconnectTimeout.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [topic]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { data, isConnected };
}

export const useRuntimeStream = () => useWebSocket<WSRuntimeMessage>('runtime');
export const useSystemStream = () => useWebSocket<WSSystemMessage>('system');
export const useCameraStream = () => useWebSocket<WSCameraMessage>('camera');
export const useRecognitionStream = () => useWebSocket<WSRecognitionMessage>('recognition');
export const useHistoryStream = () => useWebSocket<WSHistoryMessage>('history');
