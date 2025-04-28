import { ArrowLeft, Trash2, X } from "lucide-react";
import { MediaItem } from "../types";
import { format } from "date-fns";
import { useState } from "react";
import { mediaAPI } from "../lib/api";

interface MediaPreviewModalProps {
  isOpen: boolean;
  media: MediaItem | null;
  onClose: () => void;
  onDelete?: (mediaId: string) => Promise<void>;
}

const MediaPreviewModal = ({ isOpen, media, onClose, onDelete }: MediaPreviewModalProps) => {
  const [isDeleting, setIsDeleting] = useState(false);
  
  if (!isOpen || !media) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only close if clicking on the backdrop, not the content
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Determine if media is image or video
  const isImage = media.type === 'image';
  
  // Use presigned_url if available, otherwise fallback to url
  const mediaUrl = media.presigned_url || media.url;

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
  
  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg overflow-hidden shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
        {/* Close button */}
        <div className="absolute top-4 right-4 z-10">
          <button
            onClick={onClose}
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
              <video 
                src={mediaUrl} 
                controls 
                autoPlay 
                className="max-h-[70vh] max-w-full"
              >
                Your browser does not support the video tag.
              </video>
            )}
          </div>
          
          {/* Sidebar with details */}
          <div className="w-72 bg-white border-l border-gray-200 overflow-y-auto">
            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-xl font-bold mb-1">{media.title || "Untitled"}</h3>
                <div className="flex items-center text-gray-500">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm">{formatDate(media.uploadDate)}</span>
                </div>
              </div>
              
              {media.description && media.description.trim() !== "" && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Description</h4>
                  <p className="text-gray-800">
                    {media.description}
                  </p>
                </div>
              )}
              
              <div className="pt-4 mt-6 border-t border-gray-200">
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex items-center text-red-600 hover:text-red-800 disabled:opacity-50"
                >
                  <Trash2 className="h-5 w-5 mr-2" />
                  <span>{isDeleting ? "Deleting..." : "Delete Media"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MediaPreviewModal; 