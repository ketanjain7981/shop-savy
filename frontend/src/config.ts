// Configuration management for the application
import { useState, useEffect } from 'react';

// Default configuration values (fallbacks if API call fails)
const defaultConfig = {
  manual_room_entry: false,
  open_mic: true,
  user_video: false,
  show_splash: false,
  show_config: false,
  app_title: 'Voice Assistant'
};

// Type definition for config
export interface AppConfig {
  manual_room_entry: boolean;
  open_mic: boolean;
  user_video: boolean;
  show_splash: boolean;
  show_config: boolean;
  app_title: string;
}

// Function to fetch config from the backend
export const fetchConfig = async (serverUrl: string): Promise<AppConfig> => {
  try {
    // Ensure we don't have double slashes in the URL
    const url = serverUrl.endsWith('/') ? `${serverUrl}config` : `${serverUrl}/config`;
    console.log('Fetching config from URL:', url);
    
    const response = await fetch(url);
    console.log('Config response status:', response.status);
    
    if (!response.ok) {
      console.warn('Failed to fetch config from server, using defaults');
      return defaultConfig;
    }
    
    const data = await response.json();
    console.log('Config data received:', data);
    
    // Merge with defaults
    const mergedConfig = {
      ...defaultConfig, // Include defaults for any missing properties
      ...data // Override with values from the server
    };
    
    console.log('Final merged config:', mergedConfig);
    return mergedConfig;
  } catch (error) {
    console.error('Error fetching config:', error);
    return defaultConfig;
  }
};

// React hook to use the config
export const useAppConfig = (serverUrl: string | undefined) => {
  const [config, setConfig] = useState<AppConfig>(defaultConfig);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('useAppConfig: serverUrl =', serverUrl);
    
    const loadConfig = async () => {
      if (!serverUrl) {
        console.log('No serverUrl provided, using default config');
        setConfig(defaultConfig);
        setLoading(false);
        return;
      }

      try {
        console.log('Fetching config from', serverUrl);
        setLoading(true);
        const fetchedConfig = await fetchConfig(serverUrl);
        console.log('Fetched config:', fetchedConfig);
        setConfig(fetchedConfig);
        setError(null);
      } catch (err) {
        setError('Failed to load configuration');
        console.error('Error loading config:', err);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [serverUrl]);

  return { config, loading, error };
};

// Function to get environment variables with fallbacks
export const getEnvConfig = () => {
  return {
    serverUrl: '/api',
    appTitle: 'ShopSavy AI Assistant',
  };
};
