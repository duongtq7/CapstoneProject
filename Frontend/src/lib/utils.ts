import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Thumbnail cache service
const THUMBNAIL_CACHE_KEY = 'video_thumbnails_v3'; // Version the cache key for improvements

// Interface for the cached thumbnails
interface ThumbnailCache {
  [videoId: string]: {
    thumbnailUrl: string;
    timestamp: number;
    originalUrl?: string; // Store original URL for debugging and verification
    alternateIds?: string[]; // Store alternate IDs for cross-referencing
  }
}

// Helper to create a consistent video ID from a URL or file
export const getVideoIdFromSource = (source: string | File): string => {
  if (typeof source === 'string') {
    // For URLs, extract different versions of ID
    const url = new URL(source, window.location.origin); // Safely parse URL
    const urlParts = url.pathname.split('/');
    const lastPart = urlParts[urlParts.length - 1];
    
    // Clean the filename part from potential query parameters
    const baseFilename = lastPart.split('?')[0];
    
    // Generate a clean ID without any tokens or timestamps
    return baseFilename || `video_${Date.now()}`;
  } else {
    // For files, use name plus last modified time for uniqueness
    return `${source.name}_${source.lastModified}`;
  }
};

// Get all possible ID variations for a source to improve cache hits
export const getAllPossibleVideoIds = (source: string | File): string[] => {
  const ids = [];
  
  if (typeof source === 'string') {
    try {
      // Original full URL path as ID
      ids.push(source);
      
      // 1. Parse URL and get the path
      const url = new URL(source, window.location.origin);
      const urlPath = url.pathname;
      ids.push(urlPath);
      
      // 2. Last segment of the path
      const urlParts = urlPath.split('/');
      const lastPart = urlParts[urlParts.length - 1];
      ids.push(lastPart);
      
      // 3. Last segment without query params
      const baseFilename = lastPart.split('?')[0];
      ids.push(baseFilename);
      
      // 4. Just the filename without extension
      const filenameWithoutExt = baseFilename.split('.')[0];
      ids.push(filenameWithoutExt);
      
      // 5. Hash of the original URL for fixed-length ID
      const hashCode = (str: string) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
          const char = str.charCodeAt(i);
          hash = ((hash << 5) - hash) + char;
          hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(16);
      };
      ids.push(hashCode(source));
      
    } catch (e) {
      console.warn("Error generating alternate IDs:", e);
      ids.push(source); // Fallback to original source
    }
  } else {
    // For files, include variations
    ids.push(`${source.name}_${source.lastModified}`);
    ids.push(source.name);
    ids.push(source.name.split('.')[0]); // Name without extension
  }
  
  // Filter out duplicates and empty values
  return [...new Set(ids.filter(id => id))];
};

// Log the entire thumbnail cache for debugging
export const debugThumbnailCache = (): ThumbnailCache | null => {
  try {
    const cachedData = localStorage.getItem(THUMBNAIL_CACHE_KEY);
    if (!cachedData) {
      console.log('DEBUG: Thumbnail cache is empty');
      return null;
    }
    
    const cache: ThumbnailCache = JSON.parse(cachedData);
    const videoIds = Object.keys(cache);
    
    console.log(`DEBUG: Thumbnail cache contains ${videoIds.length} items:`);
    videoIds.forEach(id => {
      const thumbnail = cache[id];
      const age = Math.round((Date.now() - thumbnail.timestamp) / (1000 * 60)); // Age in minutes
      console.log(`DEBUG:   - ${id}: ${thumbnail.thumbnailUrl.substring(0, 30)}... (${age} minutes old)`);
      if (thumbnail.alternateIds) {
        console.log(`DEBUG:     Alternate IDs: ${thumbnail.alternateIds.join(', ')}`);
      }
      if (thumbnail.originalUrl) {
        console.log(`DEBUG:     Original URL: ${thumbnail.originalUrl.substring(0, 50)}...`);
      }
    });
    
    return cache;
  } catch (error) {
    console.error('DEBUG: Error accessing thumbnail cache:', error);
    return null;
  }
};

// Save a thumbnail to localStorage with all possible IDs
export const saveThumbnailToCache = (videoId: string, thumbnailUrl: string, originalSource?: string | File): void => {
  try {
    const cachedData = localStorage.getItem(THUMBNAIL_CACHE_KEY);
    const cache: ThumbnailCache = cachedData ? JSON.parse(cachedData) : {};
    
    // Generate all possible IDs for cross-referencing
    const allIds = originalSource ? getAllPossibleVideoIds(originalSource) : [videoId];
    const originalUrl = typeof originalSource === 'string' ? originalSource : undefined;
    
    // Add the main entry
    cache[videoId] = {
      thumbnailUrl,
      timestamp: Date.now(),
      alternateIds: allIds.filter(id => id !== videoId),
      originalUrl
    };
    
    // Add cross-reference entries for all alternate IDs
    allIds.forEach(id => {
      if (id && id !== videoId) {
        cache[id] = {
          thumbnailUrl,
          timestamp: Date.now(),
          alternateIds: [videoId, ...allIds.filter(altId => altId !== id && altId !== videoId)],
          originalUrl
        };
      }
    });
    
    // Save back to localStorage
    localStorage.setItem(THUMBNAIL_CACHE_KEY, JSON.stringify(cache));
    console.log(`Saved thumbnail for video ${videoId} to cache with ${allIds.length} cross-references`);
    
    // Debug: Show cache contents after save
    debugThumbnailCache();
  } catch (error) {
    console.error('Error saving thumbnail to cache:', error);
  }
};

// Get a thumbnail from localStorage with improved lookup strategy
export const getThumbnailFromCache = (videoId: string, alternateSource?: string | File): string | null => {
  try {
    const cachedData = localStorage.getItem(THUMBNAIL_CACHE_KEY);
    if (!cachedData) {
      console.log(`No cache found for video ${videoId}`);
      return null;
    }
    
    const cache: ThumbnailCache = JSON.parse(cachedData);
    
    // Try direct lookup first
    const cachedItem = cache[videoId];
    if (cachedItem) {
      console.log(`Found cached thumbnail for video ${videoId} (direct lookup)`);
      return cachedItem.thumbnailUrl;
    }
    
    // If we have an alternate source, try all possible IDs from it
    if (alternateSource) {
      const allPossibleIds = getAllPossibleVideoIds(alternateSource);
      
      for (const id of allPossibleIds) {
        if (cache[id]) {
          console.log(`Found cached thumbnail using alternate ID: ${id}`);
          return cache[id].thumbnailUrl;
        }
      }
    }
    
    // Try looking through all cache entries to find any that have this ID as an alternate
    for (const [cacheId, item] of Object.entries(cache)) {
      if (item.alternateIds && item.alternateIds.includes(videoId)) {
        console.log(`Found cached thumbnail via cross-reference from: ${cacheId}`);
        return item.thumbnailUrl;
      }
    }
    
    console.log(`No cached thumbnail for video ${videoId} (all strategies failed)`);
    return null;
  } catch (error) {
    console.error('Error retrieving thumbnail from cache:', error);
    return null;
  }
};

// Clean up old thumbnails (older than 7 days)
export const cleanupOldThumbnails = (): void => {
  try {
    const cachedData = localStorage.getItem(THUMBNAIL_CACHE_KEY);
    if (!cachedData) return;
    
    const cache: ThumbnailCache = JSON.parse(cachedData);
    const now = Date.now();
    const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
    let removedCount = 0;
    
    // Identify and remove old entries
    Object.keys(cache).forEach(videoId => {
      if (now - cache[videoId].timestamp > sevenDaysMs) {
        delete cache[videoId];
        removedCount++;
      }
    });
    
    if (removedCount > 0) {
      console.log(`Cleaned up ${removedCount} old thumbnails from cache`);
      localStorage.setItem(THUMBNAIL_CACHE_KEY, JSON.stringify(cache));
    }
  } catch (error) {
    console.error('Error cleaning up thumbnails:', error);
  }
};

// Video thumbnail generation utility
export const generateVideoThumbnail = async (videoFile: File | string): Promise<string> => {
  // Generate consistent video ID
  const videoId = getVideoIdFromSource(videoFile);
  console.log(`Generating thumbnail for video ID: ${videoId}`);
  
  // First check if we have it cached (using improved lookup with fallbacks)
  const cachedThumbnail = getThumbnailFromCache(videoId, videoFile);
  if (cachedThumbnail) {
    console.log('Using cached thumbnail');
    return cachedThumbnail;
  }
  
  return new Promise((resolve, reject) => {
    try {
      // Create video element to load the video
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.muted = true;
      video.playsInline = true;
      video.crossOrigin = 'anonymous'; // Add crossOrigin to handle CORS issues
      
      // Create URL for the video
      const videoUrl = typeof videoFile === 'string' 
        ? videoFile 
        : URL.createObjectURL(videoFile);
      
      console.log(`Starting thumbnail generation for ${videoId} from ${videoUrl.substring(0, 50)}...`);
      const startTime = Date.now();
      
      // Handle all video events for better error handling
      video.addEventListener('loadeddata', () => {
        console.log(`Video loaded, duration: ${video.duration}s, dimensions: ${video.videoWidth}x${video.videoHeight}`);
        
        // Sometimes video.duration is not available right away
        setTimeout(() => {
          try {
            // Seek to 25% of the video duration to get a representative frame
            // Default to 1 second if duration is NaN
            const seekTime = !isNaN(video.duration) ? video.duration * 0.25 : 1.0;
            console.log(`Seeking to ${seekTime}s`);
            video.currentTime = seekTime;
          } catch (error) {
            console.error('Error during seek:', error);
            // Try a direct capture if seeking fails
            captureFrame();
          }
        }, 500);
      });
      
      // Function to capture the current frame
      const captureFrame = () => {
        try {
          // Create a canvas to draw the video frame
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          
          if (!context) {
            throw new Error('Could not create 2D context');
          }
          
          // Set canvas dimensions to match video or use fallback dimensions
          const width = video.videoWidth || 320;
          const height = video.videoHeight || 240;
          
          console.log(`Setting canvas dimensions to ${width}x${height}`);
          canvas.width = width;
          canvas.height = height;
          
          // Draw video frame to canvas
          context.drawImage(video, 0, 0, width, height);
          
          // Convert canvas to data URL (JPEG format for better performance)
          const thumbnailUrl = canvas.toDataURL('image/jpeg', 0.8);
          
          // Clean up object URL if we created one
          if (typeof videoFile !== 'string') {
            URL.revokeObjectURL(videoUrl);
          }
          
          // Log generation time
          const elapsedTime = Date.now() - startTime;
          console.log(`Generated thumbnail in ${elapsedTime}ms, size: ${thumbnailUrl.length} chars`);
          
          // Store in cache for future use (with improved storage that includes all possible IDs)
          if (thumbnailUrl && thumbnailUrl.length > 100) { // Basic validation
            saveThumbnailToCache(videoId, thumbnailUrl, videoFile);
          } else {
            console.warn('Generated thumbnail appears invalid, not caching');
          }
          
          // Return the thumbnail URL
          resolve(thumbnailUrl);
        } catch (error) {
          console.error('Error capturing thumbnail frame:', error);
          resolve(''); // Return empty string to avoid breaking the app
        }
      };
      
      // When seeked to the position, capture the frame
      video.addEventListener('seeked', captureFrame);
      
      // Handle errors
      video.addEventListener('error', (e) => {
        console.error('Video error:', e);
        if (typeof videoFile !== 'string') {
          URL.revokeObjectURL(videoUrl);
        }
        // Return a fallback empty string instead of rejecting
        resolve('');
      });
      
      // Try to capture frame even if metadata loading fails
      video.addEventListener('canplay', () => {
        if (video.readyState >= 2) { // HAVE_CURRENT_DATA or better
          // If we haven't captured a frame yet, try now
          if (video.currentTime === 0) {
            console.log('Video can play, capturing frame at current position');
            video.currentTime = 1.0; // Try to seek to 1 second
          }
        }
      });
      
      // Set timeout for loading
      const timeout = setTimeout(() => {
        console.warn('Video thumbnail generation timed out');
        // Try to capture whatever frame we have
        captureFrame();
        
        if (typeof videoFile !== 'string') {
          URL.revokeObjectURL(videoUrl);
        }
      }, 10000); // 10 second timeout
      
      // Clear timeout when video is loaded
      video.addEventListener('loadeddata', () => clearTimeout(timeout));
      
      // Set source and load
      video.src = videoUrl;
      video.load();
      
    } catch (error) {
      console.error('Thumbnail generation error:', error);
      resolve(''); // Return empty string to avoid breaking the app
    }
  });
};

// Function to migrate old cache to new format
export const migrateThumbnailCache = (): void => {
  try {
    // Check for old cache
    const oldCacheKey = 'video_thumbnails_v2';
    const oldCache = localStorage.getItem(oldCacheKey);
    
    if (!oldCache) {
      console.log('No old cache to migrate');
      return;
    }
    
    console.log('Migrating thumbnail cache to new format...');
    
    const oldCacheData = JSON.parse(oldCache);
    const newCache: ThumbnailCache = {};
    
    // Simple migration adding new fields
    Object.entries(oldCacheData).forEach(([id, data]: [string, any]) => {
      newCache[id] = {
        thumbnailUrl: data.thumbnailUrl,
        timestamp: data.timestamp,
        alternateIds: [id], // Add self as alternate
        originalUrl: undefined
      };
    });
    
    // Save new cache
    localStorage.setItem(THUMBNAIL_CACHE_KEY, JSON.stringify(newCache));
    console.log(`Migrated ${Object.keys(newCache).length} thumbnails to new cache format`);
    
    // Optionally remove old cache
    // localStorage.removeItem(oldCacheKey);
    
  } catch (error) {
    console.error('Error migrating thumbnail cache:', error);
  }
};
