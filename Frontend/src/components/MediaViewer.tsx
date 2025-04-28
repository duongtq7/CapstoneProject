
import { useState } from 'react';
import { MediaItem } from '../types';
import { ArrowLeft, Calendar, Info } from 'lucide-react';
import { Link } from 'react-router-dom';

interface MediaViewerProps {
  media: MediaItem;
}

const MediaViewer = ({ media }: MediaViewerProps) => {
  const [showInfo, setShowInfo] = useState(false);
  const formattedDate = new Date(media.uploadDate).toLocaleDateString();
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-4 border-b">
        <Link to="/" className="flex items-center text-gray-700 hover:text-gray-900">
          <ArrowLeft className="w-5 h-5 mr-1" />
          <span>Back</span>
        </Link>
        <button 
          onClick={() => setShowInfo(!showInfo)}
          className={`p-2 rounded-full ${showInfo ? 'bg-primary text-white' : 'text-gray-700 hover:bg-gray-100'}`}
        >
          <Info className="w-5 h-5" />
        </button>
      </div>
      
      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
        <div className="flex-1 bg-black flex items-center justify-center p-4">
          {media.type === 'image' ? (
            <img 
              src={media.url} 
              alt={media.title} 
              className="max-h-full max-w-full object-contain" 
            />
          ) : (
            <video 
              src={media.url} 
              controls 
              className="max-h-full max-w-full"
              poster={media.thumbnail}
            >
              Your browser does not support video playback.
            </video>
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
