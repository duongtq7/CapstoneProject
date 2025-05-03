import { useState, useEffect, useCallback, useRef } from 'react';
import { MediaItem } from '../types';
import MediaPreviewModal from './MediaPreviewModal';
import { 
  generateVideoThumbnail, 
  getThumbnailFromCache, 
  cleanupOldThumbnails, 
  getVideoIdFromSource,
  debugThumbnailCache,
  migrateThumbnailCache,
  getAllPossibleVideoIds
} from '../lib/utils';

interface MediaGridProps {
  items: MediaItem[];
  emptyMessage?: string;
  onDeleteMedia?: (mediaId: string) => Promise<void>;
}

const MediaGrid = ({ 
  items, 
  emptyMessage = "No media items yet. Upload some to get started!",
  onDeleteMedia 
}: MediaGridProps) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedMedia, setSelectedMedia] = useState<MediaItem | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [videoThumbnails, setVideoThumbnails] = useState<Record<string, string>>({});
  const [debugMode, setDebugMode] = useState(false);
  const [cacheMigrated, setCacheMigrated] = useState(false);
  const [thumbnailStatus, setThumbnailStatus] = useState<Record<string, {status: string, source?: string}>>({});
  const processedVideoIds = useRef(new Set<string>());

  // Track if component is mounted to prevent state updates after unmount
  const isMounted = useRef(true);
  
  // Migrate old cache on mount
  useEffect(() => {
    if (!cacheMigrated) {
      console.log("Migrating thumbnail cache if needed");
      migrateThumbnailCache();
      setCacheMigrated(true);
    }
  }, [cacheMigrated]);
  
  // Clean up old thumbnails on mount and show debug info
  useEffect(() => {
    // Display existing cache on mount
    console.log("MediaGrid mounted, debugging thumbnail cache:");
    debugThumbnailCache();
    
    // Clean up old thumbnails
    cleanupOldThumbnails();

    // Force re-rendering after initial mount to ensure thumbnails are displayed
    const timer = setTimeout(() => {
      if (isMounted.current) {
        console.log("Forcing refresh of thumbnails");
        setVideoThumbnails(prev => ({...prev}));
      }
    }, 500);
    
    return () => {
      clearTimeout(timer);
      isMounted.current = false;
    };
  }, []);
  
  // Load cached thumbnails when items change
  useEffect(() => {
    console.log(`Loading cached thumbnails for ${items.length} items`);
    
    // Reset processed videos and thumbnail status on items change
    processedVideoIds.current = new Set<string>();
    setThumbnailStatus({});
    
    const newStatus: Record<string, {status: string, source?: string}> = {};
    
    const loadCachedThumbnails = () => {
      const newCachedItems: Record<string, string> = {};
      let foundCount = 0;
      
      items.forEach(item => {
        if (item.type === 'video') {
          // Try multiple ID generation strategies
          const videoUrl = item.presigned_url || item.url;
          
          // Store all possible IDs for this video
          const possibleIds = getAllPossibleVideoIds(videoUrl);
          console.log(`Looking up cached thumbnail for ${item.id}`);
          console.log(`  - Generated ${possibleIds.length} possible IDs for lookup`);
          
          // Try to find a cached thumbnail using any of the possible IDs
          let cachedThumbnail = getThumbnailFromCache(item.id, videoUrl);
          
          if (cachedThumbnail) {
            foundCount++;
            newCachedItems[item.id] = cachedThumbnail;
            newStatus[item.id] = { status: 'cached', source: 'local' };
          } else if (item.thumbnail) {
            // If no local thumbnail but there's a server one, track it
            newStatus[item.id] = { status: 'server', source: 'server' };
          } else {
            // No thumbnail available yet
            newStatus[item.id] = { status: 'missing' };
          }
        }
      });
      
      if (Object.keys(newCachedItems).length > 0) {
        console.log(`Loaded ${foundCount} cached thumbnails`);
        setVideoThumbnails(prev => ({
          ...prev,
          ...newCachedItems
        }));
      } else {
        console.log("No cached thumbnails found for current items");
      }
      
      // Update status
      setThumbnailStatus(prev => ({...prev, ...newStatus}));
    };
    
    loadCachedThumbnails();
  }, [items]);

  // Generate thumbnails for videos that don't have them
  useEffect(() => {
    const pendingThumbnails = new Set<string>();
    
    const generateThumbnails = async () => {
      if (!isMounted.current) return;
      
      // Find videos that need thumbnails
      const videoItems = items.filter(item => 
        item.type === 'video' && 
        !item.thumbnail && 
        !videoThumbnails[item.id] && 
        !pendingThumbnails.has(item.id) &&
        !processedVideoIds.current.has(item.id)
      );
      
      if (videoItems.length === 0) {
        console.log("No videos need thumbnail generation");
        return;
      }
      
      console.log(`Found ${videoItems.length} videos needing thumbnails`);
      
      // Process thumbnails one at a time for better stability
      for (const item of videoItems) {
        if (!isMounted.current) return;
        
        pendingThumbnails.add(item.id);
        processedVideoIds.current.add(item.id);
        
        // Update status to processing
        setThumbnailStatus(prev => ({
          ...prev, 
          [item.id]: { status: 'processing' }
        }));
        
        console.log(`Starting thumbnail generation for ${item.id}`);
        
        try {
          const videoUrl = item.presigned_url || item.url;
          
          console.log(`Generating thumbnail for video: ${item.id} (${videoUrl.substring(0, 30)}...)`);
          const thumbnailUrl = await generateVideoThumbnail(videoUrl);
          
          if (thumbnailUrl && isMounted.current) {
            console.log(`Successfully generated thumbnail for: ${item.id}`);
            setVideoThumbnails(prev => ({
              ...prev,
              [item.id]: thumbnailUrl
            }));
            
            // Update status to generated
            setThumbnailStatus(prev => ({
              ...prev, 
              [item.id]: { status: 'generated', source: 'local' }
            }));
          } else {
            console.warn(`Failed to generate thumbnail for: ${item.id}`);
            // Update status to failed
            setThumbnailStatus(prev => ({
              ...prev, 
              [item.id]: { status: 'failed' }
            }));
          }
        } catch (error) {
          console.error(`Error generating thumbnail for video ${item.id}:`, error);
          // Update status to error
          setThumbnailStatus(prev => ({
            ...prev, 
            [item.id]: { status: 'error', source: error instanceof Error ? error.message : 'unknown error' }
          }));
        } finally {
          pendingThumbnails.delete(item.id);
        }
        
        // Wait between generating thumbnails to avoid overwhelming the browser
        if (isMounted.current && pendingThumbnails.size > 0) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    };
    
    // Start generating thumbnails with a small delay to give time for cached thumbnails to load
    const timer = setTimeout(() => {
      generateThumbnails();
    }, 1000);
    
    // Cleanup function to cancel any pending operations
    return () => {
      clearTimeout(timer);
      pendingThumbnails.clear();
    };
  }, [items, videoThumbnails]);

  const handleMediaClick = useCallback((media: MediaItem, e: React.MouseEvent) => {
    console.log('Media clicked:', media.id);
    e.preventDefault();
    e.stopPropagation(); // Prevent event bubbling
    setSelectedMedia(media);
    setIsPreviewOpen(true);
  }, []);

  const handleClosePreview = useCallback(() => {
    console.log('Closing preview');
    setIsPreviewOpen(false);
    setTimeout(() => {
      setSelectedMedia(null);
    }, 300); // Small delay to ensure smooth transition
  }, []);

  // Show debug panel if needed
  const toggleDebugMode = useCallback(() => {
    setDebugMode(current => !current);
    debugThumbnailCache();
  }, []);

  // Force refresh thumbnails
  const forceRefreshThumbnails = useCallback(() => {
    // Clear processed flags to allow re-processing
    processedVideoIds.current.clear();
    
    // Reset all thumbnails and force a refresh
    const newStatus: Record<string, {status: string, source?: string}> = {};
    
    items.forEach(item => {
      if (item.type === 'video') {
        newStatus[item.id] = { status: 'refresh-pending' };
        console.log(`Forcing refresh for ${item.id}`);
      }
    });
    
    // Update status
    setThumbnailStatus(newStatus);
    
    // Force re-render
    setVideoThumbnails({});
  }, [items]);

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="text-gray-400 text-center">
          <p className="text-xl mb-2">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Debug toggle button */}
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleDebugMode}
          className="bg-gray-800 text-white px-3 py-1 rounded text-xs"
        >
          {debugMode ? 'Hide Debug' : 'Debug'}
        </button>
      </div>

      {/* Debug panel */}
      {debugMode && (
        <div className="fixed bottom-12 right-4 w-96 max-h-80 overflow-auto bg-gray-800 text-white p-3 rounded text-xs z-50">
          <h3 className="font-bold mb-2">Thumbnail Debug</h3>
          <p>Items: {items.length} | Videos: {items.filter(i => i.type === 'video').length}</p>
          <p>Cached thumbnails: {Object.keys(videoThumbnails).length}</p>
          <p>Cache migrated: {cacheMigrated ? 'Yes' : 'No'}</p>
          <div className="flex gap-2 mt-2">
            <button 
              onClick={() => debugThumbnailCache()}
              className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
            >
              Refresh Cache
            </button>
            <button 
              onClick={() => {
                localStorage.removeItem('video_thumbnails_v3');
                localStorage.removeItem('video_thumbnails_v2');
                setVideoThumbnails({});
                alert('Cache cleared');
              }}
              className="bg-red-500 text-white px-2 py-1 rounded text-xs"
            >
              Clear Cache
            </button>
            <button 
              onClick={forceRefreshThumbnails}
              className="bg-green-500 text-white px-2 py-1 rounded text-xs"
            >
              Force Refresh
            </button>
          </div>
          
          <h4 className="font-bold mt-3 mb-1">Video Status:</h4>
          <ul className="text-xs max-h-40 overflow-y-auto">
            {items.filter(i => i.type === 'video').map(video => {
              const status = thumbnailStatus[video.id] || { status: 'unknown' };
              let statusColor = 'text-gray-400';
              let statusIcon = '?';
              
              switch(status.status) {
                case 'cached':
                  statusColor = 'text-green-400';
                  statusIcon = '✓';
                  break;
                case 'processing':
                  statusColor = 'text-yellow-400';
                  statusIcon = '⟳';
                  break;
                case 'generated':
                  statusColor = 'text-green-400';
                  statusIcon = '★';
                  break;
                case 'server':
                  statusColor = 'text-blue-400';
                  statusIcon = '☁';
                  break;
                case 'failed':
                case 'error':
                  statusColor = 'text-red-400';
                  statusIcon = '✕';
                  break;
                case 'refresh-pending':
                  statusColor = 'text-purple-400';
                  statusIcon = '⟲';
                  break;
                case 'missing':
                  statusColor = 'text-orange-400';
                  statusIcon = '!';
                  break;
              }
              
              return (
                <li key={video.id} className="mb-1">
                  <span className="opacity-70">{video.id.substring(0, 10)}...:</span> 
                  <span className={statusColor}>
                    {` ${statusIcon} ${status.status}`} {status.source ? `(${status.source})` : ''}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((item) => {
          // Use presigned_url if available, otherwise fallback to url
          const imageUrl = item.presigned_url || item.url;
          
          // For videos, determine the best thumbnail source
          let thumbnailUrl = imageUrl;
          let thumbnailSource = 'none';
          
          if (item.type === 'video') {
            if (item.thumbnail) {
              thumbnailUrl = item.thumbnail;
              thumbnailSource = 'server';
            } else if (videoThumbnails[item.id]) {
              thumbnailUrl = videoThumbnails[item.id];
              thumbnailSource = 'local';
            }
          }
          
          // Get the status for this item
          const status = thumbnailStatus[item.id];
          const isProcessing = status?.status === 'processing' || status?.status === 'refresh-pending';
          
          return (
            <div
              key={item.id}
              className="relative bg-gray-50 rounded-lg overflow-hidden aspect-square shadow-sm hover:shadow-md transition-all cursor-pointer"
              onMouseEnter={() => setHoveredId(item.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={(e) => handleMediaClick(item, e)}
            >
              {item.type === 'image' ? (
                <img 
                  src={imageUrl} 
                  alt={item.title} 
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="relative w-full h-full bg-gray-200">
                  {/* Debug indicator for thumbnail source */}
                  {debugMode && (
                    <div className="absolute top-0 left-0 bg-black bg-opacity-70 text-white text-xs p-1 z-10">
                      {thumbnailSource === 'server' ? 'Server' : 
                       thumbnailSource === 'local' ? 'Local' : 'None'}
                    </div>
                  )}
                  
                  {/* Processing indicator */}
                  {isProcessing && (
                    <div className="absolute top-0 right-0 bg-yellow-500 text-white text-xs p-1 z-10">
                      Processing...
                    </div>
                  )}
                  
                  {/* Show thumbnail if available */}
                  {thumbnailSource !== 'none' && (
                    <img 
                      key={`thumb-${item.id}-${thumbnailSource}-${thumbnailUrl.substring(0, 20)}`}
                      src={thumbnailUrl} 
                      alt={item.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      onError={(e) => {
                        // If thumbnail fails to load, show a default video icon
                        console.error(`Thumbnail failed to load for ${item.id}`);
                        e.currentTarget.style.display = 'none';
                        
                        // Update status
                        setThumbnailStatus(prev => ({
                          ...prev, 
                          [item.id]: { 
                            status: 'error', 
                            source: `Failed to load ${thumbnailSource} thumbnail`
                          }
                        }));
                      }}
                    />
                  )}
                  
                  {/* Always show play button overlay */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="bg-black bg-opacity-60 rounded-full p-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                      </svg>
                    </div>
                  </div>
                </div>
              )}
              
              {hoveredId === item.id && (
                <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 text-white">
                  <div className="text-center">
                    <h3 className="font-medium text-sm mb-1 line-clamp-2">{item.title}</h3>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {isPreviewOpen && selectedMedia && (
        <MediaPreviewModal
          isOpen={isPreviewOpen}
          media={selectedMedia}
          onClose={handleClosePreview}
          onDelete={onDeleteMedia}
        />
      )}
    </>
  );
};

export default MediaGrid;
