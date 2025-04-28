import axios, { InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

console.log('API URL being used:', API_URL); // For debugging

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Enable this for detailed API debugging
const ENABLE_API_DEBUG = true;

// Add request interceptor to add auth token and log requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  if (ENABLE_API_DEBUG) {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, {
      headers: config.headers,
      data: config.data,
      params: config.params,
    });
  }
  
  return config;
}, (error) => {
  console.error('Request error:', error);
  return Promise.reject(error);
});

// Add response interceptor to handle errors and log responses
api.interceptors.response.use(
  response => {
    if (ENABLE_API_DEBUG) {
      console.log(`[API Response] ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        data: response.data,
        headers: response.headers,
      });
    }
    return response;
  },
  error => {
    if (ENABLE_API_DEBUG) {
      console.error(`[API Error] ${error.response?.status || 'Network Error'} ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
        data: error.response?.data,
        headers: error.response?.headers,
        message: error.message,
      });
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    // The login router doesn't have a prefix in main.py
    const response = await api.post('/login/access-token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  testToken: async () => {
    // The login router doesn't have a prefix in main.py
    const response = await api.post('/login/test-token');
    return response.data;
  },
};

// Users API
export const usersAPI = {
  getCurrentUser: async () => {
    const response = await api.get('/users/users/me');
    return response.data;
  },
  updateCurrentUser: async (data: { email?: string; full_name?: string }) => {
    const response = await api.patch('/users/users/me', data);
    return response.data;
  },
  updatePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.patch('/users/users/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
  deleteCurrentUser: async () => {
    const response = await api.delete('/users/users/me');
    return response.data;
  },
  register: async (data: { email: string; password: string; full_name?: string }) => {
    try {
      console.log('Registering user with data:', { email: data.email, has_password: !!data.password, has_full_name: !!data.full_name });
      console.log('Full user data being sent:', JSON.stringify(data));
      
      // The endpoint has a double prefix: router has 'users' prefix and api_router adds another 'users' prefix
      const response = await api.post('/users/users/signup', data);
      
      console.log('Registration successful, response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Registration error:', error);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
        console.error('Response data:', error.response.data);
        console.error('Request URL:', error.config?.url);
        console.error('Request method:', error.config?.method);
        console.error('Request data:', error.config?.data);
      }
      throw error;
    }
  },
};

// Albums API
export const albumsAPI = {
  getAlbums: async (skip: number = 0, limit: number = 100) => {
    try {
      // No need for double prefix for albums endpoints
      const response = await api.get('/albums/', { params: { skip, limit } });
      return response.data;
    } catch (error) {
      console.error('Failed to get albums:', error);
      throw error;
    }
  },
  getAlbum: async (albumId: string) => {
    const response = await api.get(`/albums/${albumId}/`);
    return response.data;
  },
  createAlbum: async (data: { name: string }) => {
    try {
      console.log('Creating album with data:', data);
      
      // Convert 'name' to 'title' as expected by the backend
      const payload = {
        title: data.name,
        description: null
      };
      
      console.log('Sending album creation payload:', payload);
      
      // Use the endpoint with trailing slash to avoid 307 redirects
      const response = await api.post('/albums/', payload);
      
      console.log('Album created successfully:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Failed to create album:', error);
      if (error.response?.data) {
        console.error('Server validation error details:', error.response.data);
      }
      throw error;
    }
  },
  updateAlbum: async (albumId: string, data: { name: string }) => {
    const response = await api.put(`/albums/${albumId}/`, data);
    return response.data;
  },
  deleteAlbum: async (albumId: string) => {
    const response = await api.delete(`/albums/${albumId}/`);
    return response.data;
  },
};

// Media API
export const mediaAPI = {
  getMedia: async (albumId?: string, skip: number = 0, limit: number = 100) => {
    try {
      const params = { skip, limit, ...(albumId && { album_id: albumId }) };
      console.log(`Fetching media with params:`, params);
      // No need for double prefix for media endpoints
      const response = await api.get('/media/', { params });
      console.log(`Fetched ${response.data.length} media items for album ${albumId || 'all'}`);
      
      // Log the first media item in full to debug
      if (response.data.length > 0) {
        console.log('Debug - Full sample media item:', response.data[0]);
        console.log('Media type:', response.data[0].media_type || 'field not found');
        console.log('Type field:', response.data[0].type || 'field not found');
      }
      
      // Map the backend media_type to frontend type
      const mappedMedia = response.data.map((item: any) => {
        // Create a new mapped object with all original properties
        const mapped = {
          ...item,
          // Use filename from URL if title doesn't exist
          title: item.title || item.url.split('/').pop() || 'Untitled',
          // Map created_at to uploadDate if uploadDate doesn't exist
          uploadDate: item.uploadDate || item.created_at || new Date().toISOString(),
          // Convert "photo" to "image" for frontend compatibility
          type: (item.media_type === 'photo' ? 'image' : item.media_type) || item.type || 'image',
          // Ensure userId exists
          userId: item.user_id || 'unknown'
        };
        
        return mapped;
      });
      
      // Log a sample of the mapped media
      if (mappedMedia.length > 0) {
        console.log('After mapping:', {
          id: mappedMedia[0].id,
          type: mappedMedia[0].type,
          url: mappedMedia[0].url,
          presigned_url: mappedMedia[0].presigned_url || 'NOT PRESENT'
        });
      }
      
      return mappedMedia;
    } catch (error) {
      console.error(`Error fetching media for album ${albumId || 'all'}:`, error);
      throw error;
    }
  },
  getMediaItem: async (mediaId: string) => {
    const response = await api.get(`/media/${mediaId}/`);
    return response.data;
  },
  uploadMedia: async (file: File, albumId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('album_id', albumId);
    
    console.log('Uploading media to album:', albumId);
    
    const response = await api.post('/media/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  deleteMedia: async (mediaId: string) => {
    const response = await api.delete(`/media/${mediaId}/`);
    return response.data;
  },
};

// Search API
export const searchAPI = {
  searchMedia: async (query: string, limit: number = 5) => {
    try {
      console.log(`Searching for media with query: "${query}", limit: ${limit}`);
      const response = await api.get('/search/', { 
        params: { 
          query, 
          limit 
        } 
      });
      
      // Log the raw response data for debugging
      console.log('Raw search response:', response.data);
      console.log(`Found ${response.data.count} search results`);
      
      // Check if we have valid results
      if (!response.data.results || !Array.isArray(response.data.results)) {
        console.warn('Search results are not in expected format', response.data);
        return { results: [], count: 0 };
      }
      
      // Convert backend model to frontend format
      const mappedResults = response.data.results.map((item: any) => {
        if (!item || !item.media) {
          console.warn('Invalid search result item', item);
          return null;
        }
        
        const media = item.media;
        return {
          id: media.id,
          title: media.title || media.url.split('/').pop() || 'Untitled',
          type: (media.media_type === 'photo' ? 'image' : media.media_type) || 'image',
          url: media.url,
          presigned_url: media.presigned_url,
          uploadDate: media.created_at || new Date().toISOString(),
          userId: media.user_id || 'unknown',
          score: item.score || 0.0
        };
      }).filter(Boolean); // Remove any null entries
      
      console.log(`Mapped ${mappedResults.length} valid search results`);
      
      return {
        results: mappedResults,
        count: mappedResults.length
      };
    } catch (error) {
      console.error(`Error searching for media with query "${query}":`, error);
      throw error;
    }
  }
}; 