
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import MediaViewer from "../components/MediaViewer";
import Navbar from "../components/Navbar";
import { MediaItem } from "../types";

const MediaView = () => {
  const { id } = useParams<{ id: string }>();
  const [media, setMedia] = useState<MediaItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchMedia = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Here you would connect to your backend API
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check if we're using a temporary object URL
        if (id?.startsWith('temp-')) {
          const foundMedia = window.sessionStorage.getItem(`media-${id}`);
          if (foundMedia) {
            setMedia(JSON.parse(foundMedia));
          } else {
            setError("Media not found");
          }
        } else {
          // For demo purposes, create a mock item
          // Replace with your actual API call
          setMedia({
            id: id || "mock-id",
            title: "Sample Media",
            type: "image",
            url: "https://picsum.photos/800/600",
            description: "This is a sample media description.",
            uploadDate: new Date().toISOString(),
            userId: "user-id",
          });
        }
      } catch (err) {
        console.error("Error fetching media:", err);
        setError("Failed to load media");
      } finally {
        setIsLoading(false);
      }
    };
    
    if (id) {
      fetchMedia();
    }
  }, [id]);
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <svg className="animate-spin h-10 w-10 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      </div>
    );
  }
  
  if (error || !media) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="text-red-500 text-xl mb-4">
            {error || "Media not found"}
          </div>
          <a href="/" className="text-primary hover:underline">
            Return to Home
          </a>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="flex-1">
        <MediaViewer media={media} />
      </div>
    </div>
  );
};

export default MediaView;
