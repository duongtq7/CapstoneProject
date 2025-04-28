import { useState } from 'react';
import { MediaItem } from '../types';
import MediaPreviewModal from './MediaPreviewModal';

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

  const handleMediaClick = (media: MediaItem, e: React.MouseEvent) => {
    e.preventDefault();
    setSelectedMedia(media);
    setIsPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setIsPreviewOpen(false);
    setSelectedMedia(null);
  };

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
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((item) => {
          // Use presigned_url if available, otherwise fallback to url
          const imageUrl = item.presigned_url || item.url;
          const thumbnailUrl = item.thumbnail ? (item.presigned_url || item.thumbnail) : imageUrl;
          
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
                />
              ) : (
                <div className="relative w-full h-full bg-gray-200">
                  <img 
                    src={thumbnailUrl} 
                    alt={item.title}
                    className="w-full h-full object-cover" 
                  />
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
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                  <h3 className="text-white font-medium truncate">{item.title}</h3>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <MediaPreviewModal
        isOpen={isPreviewOpen}
        media={selectedMedia}
        onClose={handleClosePreview}
        onDelete={onDeleteMedia}
      />
    </>
  );
};

export default MediaGrid;
