import { ArrowLeft, Trash2, X } from "lucide-react";
import { MediaItem } from "../types";
import { format } from "date-fns";
import { useState, useEffect, useRef } from "react";
import { mediaAPI } from "../lib/api";
import { generateVideoThumbnail, getThumbnailFromCache, getVideoIdFromSource } from "../lib/utils";

interface MediaPreviewModalProps {
  isOpen: boolean;
  media: MediaItem | null;
  onClose: () => void;
  onDelete?: (mediaId: string) => Promise<void>;
}

const MediaPreviewModal = ({ isOpen, media, onClose, onDelete }: MediaPreviewModalProps) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [videoThumbnail, setVideoThumbnail] = useState<string | null>(null);
  const [thumbnailProcessing, setThumbnailProcessing] = useState(false);
  const [thumbnailSource, setThumbnailSource] = useState<'none' | 'server' | 'local'>('none');
  const modalRef = useRef<HTMLDivElement>(null);
  const thumbnailGenerationAttempted = useRef(false);
  
  // Generate video thumbnail if needed
  useEffect(() => {
    if (isOpen && media && media.type === 'video') {
      // Reset the flag when media changes
      thumbnailGenerationAttempted.current = false;
      setThumbnailSource('none');
      
      // First try to get from media object
      if (media.thumbnail) {
        console.log('MediaPreviewModal: Using server thumbnail for:', media.id);
        setThumbnailSource('server');
        return;
      }
      
      // Then try to get from cache using improved lookup with multiple strategies
      const videoUrl = media.presigned_url || media.url;
      const cachedThumbnail = getThumbnailFromCache(media.id, videoUrl);
      
      if (cachedThumbnail) {
        console.log('MediaPreviewModal: Using cached thumbnail for:', media.id);
        setVideoThumbnail(cachedThumbnail);
        setThumbnailSource('local');
        return;
      }
      
      // If not in cache and not already attempted, generate a new thumbnail
      if (!thumbnailGenerationAttempted.current) {
        thumbnailGenerationAttempted.current = true;
        console.log('MediaPreviewModal: Generating thumbnail for video:', media.id);
        setThumbnailProcessing(true);
        
        const generateThumbnail = async () => {
          try {
            const videoUrl = media.presigned_url || media.url;
            const startTime = Date.now();
            
            const thumbnailUrl = await generateVideoThumbnail(videoUrl);
            
            const elapsedTime = Date.now() - startTime;
            console.log(`MediaPreviewModal: Generated thumbnail in ${elapsedTime}ms: ${thumbnailUrl ? 'success' : 'failed'}`);
            
            if (thumbnailUrl) {
              setVideoThumbnail(thumbnailUrl);
              setThumbnailSource('local');
            }
          } catch (error) {
            console.error("MediaPreviewModal: Error generating video thumbnail:", error);
          } finally {
            setThumbnailProcessing(false);
          }
        };
        
        generateThumbnail();
      }
    }
    
    // Clear thumbnail when modal closes
    if (!isOpen) {
      setVideoThumbnail(null);
      thumbnailGenerationAttempted.current = false;
      setThumbnailProcessing(false);
      setThumbnailSource('none');
    }
  }, [isOpen, media]);

  // Early return after hooks are defined
  if (!isOpen || !media) return null;

  // Determine if media is image or video
  const isImage = media.type === 'image';
  
  // Use presigned_url if available, otherwise fallback to url
  const mediaUrl = media.presigned_url || media.url;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only close if clicking on the backdrop, not the content
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Format the date properly or show "Invalid Date" if date is invalid
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return "Invalid Date";
      }
      return format(date, "MM/dd/yyyy");
    } catch (e) {
      return "Invalid Date";
    }
  };
  
  const handleDelete = async () => {
    if (!media || !onDelete) return;
    
    try {
      setIsDeleting(true);
      
      // If onDelete was provided as a prop, use it
      if (onDelete) {
        await onDelete(media.id);
      } else {
        // Otherwise use the API directly
        await mediaAPI.deleteMedia(media.id);
      }
      
      onClose();
    } catch (error) {
      console.error("Error deleting media:", error);
    } finally {
      setIsDeleting(false);
    }
  };
  
  const handleClose = () => {
    onClose();
  };
  
  // Determine the best poster image for the video
  const videoPoster = media.thumbnail || videoThumbnail || undefined;
  
  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div 
        ref={modalRef}
        className="bg-white rounded-lg overflow-hidden shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <div className="absolute top-4 right-4 z-10">
          <button
            onClick={handleClose}
            className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="flex flex-1 overflow-hidden">
          {/* Main content - Image/Video */}
          <div className="flex-1 bg-black flex items-center justify-center">
            {isImage ? (
              <img 
                src={mediaUrl} 
                alt={media.title || "Image preview"} 
                className="max-h-[70vh] max-w-full object-contain"
              />
            ) : (
              <>
                {/* Debug indicator for thumbnail source */}
                {thumbnailSource !== 'none' && (
                  <div className="absolute top-4 left-4 bg-gray-900 bg-opacity-70 text-white text-xs py-1 px-2 rounded z-10">
                    {thumbnailSource === 'server' ? 'Server Thumbnail' : 'Local Thumbnail'}
                  </div>
                )}

                {/* Thumbnail processing indicator */}
                {thumbnailProcessing && !videoPoster && (
                  <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/30">
                    <div className="text-white text-sm">Generating thumbnail...</div>
                  </div>
                )}
                <video 
                  key={`${media.id}-${mediaUrl}`} // Key to force re-render when URL or media changes
                  src={mediaUrl} 
                  controls 
                  autoPlay 
                  className="max-h-[70vh] max-w-full"
                  poster={videoPoster}
                  onError={(e) => console.error("Video error:", e)}
                >
                  Your browser does not support the video tag.
                </video>
              </>
            )}
          </div>
          
          {/* Sidebar with details */}
          <div className="w-80 border-l p-4 overflow-y-auto bg-white flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold line-clamp-2">
                {media.title || "Untitled"}
              </h2>
            </div>
            
            <div className="text-sm text-gray-600 mb-4">
              Uploaded: {formatDate(media.uploadDate)}
            </div>
            
            {media.description && (
              <div className="mb-6">
                <h3 className="text-sm font-medium mb-1">Description</h3>
                <p className="text-sm text-gray-700">{media.description}</p>
              </div>
            )}
            
            <div className="mt-auto">
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-red-600 text-red-600 rounded-md hover:bg-red-50 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                <span>{isDeleting ? "Deleting..." : "Delete"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MediaPreviewModal; 