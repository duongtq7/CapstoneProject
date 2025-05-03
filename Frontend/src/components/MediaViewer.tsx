import { useState, useEffect, useRef } from 'react';
import { MediaItem } from '../types';
import { ArrowLeft, Calendar, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import { generateVideoThumbnail, getThumbnailFromCache, getVideoIdFromSource } from '../lib/utils';

interface MediaViewerProps {
  media: MediaItem;
}

const MediaViewer = ({ media }: MediaViewerProps) => {
  const [showInfo, setShowInfo] = useState(false);
  const [videoThumbnail, setVideoThumbnail] = useState<string | null>(null);
  const [thumbnailProcessing, setThumbnailProcessing] = useState(false);
  const [thumbnailSource, setThumbnailSource] = useState<'none' | 'server' | 'local'>('none');
  const [isDebugMode, setIsDebugMode] = useState(false);
  const thumbnailGenerationAttempted = useRef(false);
  const formattedDate = new Date(media.uploadDate).toLocaleDateString();
  
  // Generate video thumbnail if needed
  useEffect(() => {
    if (media.type === 'video') {
      // Reset the flag when media changes
      thumbnailGenerationAttempted.current = false;
      setThumbnailProcessing(false);
      setThumbnailSource('none');
      
      // First try to get thumbnail from media object
      if (media.thumbnail) {
        console.log('MediaViewer: Using server thumbnail for:', media.id);
        setThumbnailSource('server');
        return;
      }
      
      // Then try to get from cache with improved lookup
      const videoUrl = media.presigned_url || media.url;
      console.log(`MediaViewer: Checking cache for video: ${media.id}`);
      const cachedThumbnail = getThumbnailFromCache(media.id, videoUrl);
      
      if (cachedThumbnail) {
        console.log('MediaViewer: Using cached thumbnail for:', media.id);
        setVideoThumbnail(cachedThumbnail);
        setThumbnailSource('local');
        return;
      }
      
      // If not in cache and not already attempted, generate a new thumbnail
      if (!thumbnailGenerationAttempted.current) {
        thumbnailGenerationAttempted.current = true;
        console.log('MediaViewer: Generating thumbnail for video:', media.id);
        setThumbnailProcessing(true);
        
        const generateThumbnail = async () => {
          try {
            const videoUrl = media.presigned_url || media.url;
            const startTime = Date.now();
            
            const thumbnailUrl = await generateVideoThumbnail(videoUrl);
            
            const elapsedTime = Date.now() - startTime;
            console.log(`MediaViewer: Generated thumbnail in ${elapsedTime}ms: ${thumbnailUrl ? 'success' : 'failed'}`);
            
            if (thumbnailUrl) {
              setVideoThumbnail(thumbnailUrl);
              setThumbnailSource('local');
            }
          } catch (error) {
            console.error("MediaViewer: Error generating video thumbnail:", error);
          } finally {
            setThumbnailProcessing(false);
          }
        };
        
        generateThumbnail();
      }
    }
  }, [media]);
  
  // Use presigned_url if available, otherwise fallback to url
  const mediaUrl = media.presigned_url || media.url;
  
  // Determine the best poster image for the video
  const videoPoster = media.thumbnail || videoThumbnail || undefined;
  
  // Toggle debug mode
  const toggleDebugMode = () => {
    setIsDebugMode(prev => !prev);
  };
  
  // Force refresh of the thumbnail
  const forceRefreshThumbnail = async () => {
    if (media.type !== 'video') return;
    
    // Clear existing thumbnail
    setVideoThumbnail(null);
    setThumbnailSource('none');
    thumbnailGenerationAttempted.current = false;
    
    // Trigger new thumbnail generation
    setThumbnailProcessing(true);
    try {
      const videoUrl = media.presigned_url || media.url;
      console.log('MediaViewer: Forcing thumbnail refresh for:', media.id);
      const thumbnailUrl = await generateVideoThumbnail(videoUrl);
      
      if (thumbnailUrl) {
        setVideoThumbnail(thumbnailUrl);
        setThumbnailSource('local');
      }
    } catch (error) {
      console.error("MediaViewer: Error refreshing thumbnail:", error);
    } finally {
      setThumbnailProcessing(false);
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-4 border-b">
        <Link to="/" className="flex items-center text-gray-700 hover:text-gray-900">
          <ArrowLeft className="w-5 h-5 mr-1" />
          <span>Back</span>
        </Link>
        <div className="flex items-center gap-2">
          {media.type === 'video' && (
            <button
              onClick={forceRefreshThumbnail}
              className="text-xs bg-blue-500 text-white py-1 px-2 rounded hover:bg-blue-600"
            >
              Refresh Thumbnail
            </button>
          )}
          <button 
            onClick={() => setShowInfo(!showInfo)}
            className={`p-2 rounded-full ${showInfo ? 'bg-primary text-white' : 'text-gray-700 hover:bg-gray-100'}`}
          >
            <Info className="w-5 h-5" />
          </button>
          <button
            onClick={toggleDebugMode}
            className="text-xs bg-gray-700 text-white py-1 px-2 rounded hover:bg-gray-800"
          >
            {isDebugMode ? 'Hide Debug' : 'Debug'}
          </button>
        </div>
      </div>
      
      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
        <div className="flex-1 bg-black flex items-center justify-center p-4">
          {media.type === 'image' ? (
            <img 
              src={mediaUrl} 
              alt={media.title} 
              className="max-h-full max-w-full object-contain" 
            />
          ) : (
            <div className="relative w-full h-full flex items-center justify-center">
              {/* Debug info */}
              {isDebugMode && (
                <div className="absolute top-4 left-4 bg-black bg-opacity-80 text-white text-xs p-2 rounded z-20">
                  <p>Media ID: {media.id}</p>
                  <p>Thumbnail Source: {thumbnailSource}</p>
                  <p>Processing: {thumbnailProcessing ? 'Yes' : 'No'}</p>
                  <p>Has Poster: {videoPoster ? 'Yes' : 'No'}</p>
                </div>
              )}
              
              {/* Thumbnail source indicator */}
              {thumbnailSource !== 'none' && !isDebugMode && (
                <div className="absolute top-4 left-4 bg-gray-900 bg-opacity-70 text-white text-xs py-1 px-2 rounded z-10">
                  {thumbnailSource === 'server' ? 'Server Thumbnail' : 'Local Thumbnail'}
                </div>
              )}
              
              {/* Thumbnail loading indicator */}
              {thumbnailProcessing && !videoPoster && (
                <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/30">
                  <div className="text-white text-sm">Generating thumbnail...</div>
                </div>
              )}
              
              <video 
                key={`${media.id}-${mediaUrl}`} // Key to force re-render when URL or media changes
                src={mediaUrl} 
                controls 
                className="max-h-full max-w-full"
                poster={videoPoster}
                onError={(e) => console.error("Video error:", e)}
              >
                Your browser does not support video playback.
              </video>
            </div>
          )}
        </div>
        
        {showInfo && (
          <div className="w-full lg:w-80 border-l border-t lg:border-t-0 p-4 overflow-y-auto">
            <h1 className="text-xl font-bold mb-2">{media.title}</h1>
            
            <div className="flex items-center text-gray-600 mb-4">
              <Calendar className="w-4 h-4 mr-1" />
              <span className="text-sm">{formattedDate}</span>
            </div>
            
            {media.description && (
              <div className="mb-4">
                <h2 className="font-medium text-gray-700 mb-1">Description</h2>
                <p className="text-gray-600">{media.description}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MediaViewer;
