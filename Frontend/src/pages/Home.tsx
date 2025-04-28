import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import MediaGrid from "../components/MediaGrid";
import UploadButton from "../components/UploadButton";
import UploadModal from "../components/UploadModal";
import CreateAlbumModal from "../components/CreateAlbumModal";
import { MediaItem } from "../types";
import { mediaAPI, albumsAPI } from "../lib/api";
import { Plus, ChevronDown, ChevronUp } from "lucide-react";

// Define interface for album with media items
interface Album {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  media?: MediaItem[];
}

const Home = () => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isCreateAlbumModalOpen, setIsCreateAlbumModalOpen] = useState(false);
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [albums, setAlbums] = useState<Album[]>([]);
  const [albumsWithMedia, setAlbumsWithMedia] = useState<Album[]>([]);
  const [selectedAlbumId, setSelectedAlbumId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedAlbums, setExpandedAlbums] = useState<{[key: string]: boolean}>({});

  useEffect(() => {
    fetchAlbumsAndMedia();
  }, []);

  // Fetch albums and then fetch media for each album
  const fetchAlbumsAndMedia = async () => {
    try {
      setIsLoading(true);
      setError("");
      
      // Fetch all albums
      console.log("Fetching albums...");
      const albumsResponse = await albumsAPI.getAlbums();
      console.log("Albums fetched:", albumsResponse);
      setAlbums(albumsResponse);
      
      if (albumsResponse.length > 0) {
        setSelectedAlbumId(albumsResponse[0].id);
        
        // Initialize all albums as expanded
        const initialExpandedState: {[key: string]: boolean} = {};
        albumsResponse.forEach(album => {
          initialExpandedState[album.id] = true;
        });
        setExpandedAlbums(initialExpandedState);
        
        // Fetch media for all albums
        const albumsWithMediaData = await Promise.all(
          albumsResponse.map(async (album) => {
            try {
              const mediaResponse = await mediaAPI.getMedia(album.id);
              return {
                ...album,
                media: mediaResponse
              };
            } catch (error) {
              console.error(`Error fetching media for album ${album.id}:`, error);
              return {
                ...album,
                media: []
              };
            }
          })
        );
        
        setAlbumsWithMedia(albumsWithMediaData);
        
        // Combine all media items for the media grid
        const allMedia = albumsWithMediaData.flatMap(album => album.media || []);
        setMedia(allMedia);
      } else {
        // If no albums exist, prompt user to create one
        console.log("No albums found, prompting user to create one");
        setIsCreateAlbumModalOpen(true);
      }
    } catch (error: any) {
      console.error("Error fetching albums and media:", error);
      setError(error.response?.data?.detail || "Failed to fetch albums and media");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAlbum = async (name: string) => {
    try {
      setError("");
      console.log("Creating album with name:", name);
      const newAlbum = await albumsAPI.createAlbum({ name });
      console.log("New album created:", newAlbum);
      
      // Add the new album to the albums list
      const updatedAlbums = [...albums, newAlbum];
      setAlbums(updatedAlbums);
      
      // Add the new album to albumsWithMedia with empty media array
      const newAlbumWithMedia = {
        ...newAlbum,
        media: []
      };
      setAlbumsWithMedia([...albumsWithMedia, newAlbumWithMedia]);
      
      // Set as selected album
      setSelectedAlbumId(newAlbum.id);
      
      // Set new album as expanded
      setExpandedAlbums({
        ...expandedAlbums,
        [newAlbum.id]: true
      });
      
      // Close the create album modal
      setIsCreateAlbumModalOpen(false);
      
      return newAlbum;
    } catch (error: any) {
      console.error("Error creating album:", error);
      
      // Extract detailed error information
      let errorMessage = "Failed to create album";
      
      if (error.response) {
        console.error("Response status:", error.response.status);
        console.error("Response headers:", error.response.headers);
        console.error("Response data:", error.response.data);
        
        // Handle validation errors from FastAPI backend
        if (error.response.data && error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // Format validation errors nicely
            errorMessage = error.response.data.detail
              .map((err: any) => `${err.loc.join('.')} - ${err.msg}`)
              .join('; ');
          } else {
            errorMessage = error.response.data.detail;
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const handleUpload = async (files: File[]) => {
    if (!selectedAlbumId) {
      // If no album is selected, ask user to create one first
      setError("Please select or create an album first");
      setIsCreateAlbumModalOpen(true);
      return;
    }

    try {
      setIsLoading(true);
      setError("");
      console.log(`Uploading ${files.length} files to album ${selectedAlbumId}`);
      
      const uploadPromises = files.map(file => {
        console.log(`Uploading file: ${file.name}`);
        return mediaAPI.uploadMedia(file, selectedAlbumId);
      });
      
      const uploadedMedia = await Promise.all(uploadPromises);
      console.log("Media upload completed:", uploadedMedia);
      
      // Refresh the albums and media
      await fetchAlbumsAndMedia();
    } catch (error: any) {
      console.error("Error uploading media:", error);
      setError(error.response?.data?.detail || "Failed to upload media items");
    } finally {
      setIsLoading(false);
      setIsUploadModalOpen(false);
    }
  };

  const toggleAlbumExpansion = (albumId: string) => {
    setExpandedAlbums({
      ...expandedAlbums,
      [albumId]: !expandedAlbums[albumId]
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Media Library</h1>
          <div className="flex items-center space-x-4">
            {albums.length > 0 ? (
              <select
                value={selectedAlbumId}
                onChange={(e) => setSelectedAlbumId(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {albums.map((album) => (
                  <option key={album.id} value={album.id}>
                    {album.title}
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-sm text-gray-500">No albums available</div>
            )}
            <button
              onClick={() => setIsCreateAlbumModalOpen(true)}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              <Plus className="h-5 w-5 mr-2" />
              New Album
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded relative mb-4" role="alert">
            <span className="block sm:inline">{error}</span>
            <button 
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={() => setError("")}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : (
          albumsWithMedia.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="text-gray-400 text-center">
                <p className="text-xl mb-2">No albums created. Create an album first, then upload media.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {albumsWithMedia.map((album) => (
                <div key={album.id} className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div 
                    className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleAlbumExpansion(album.id)}
                  >
                    <h2 className="text-xl font-semibold">{album.title}</h2>
                    <button className="p-1 rounded-full hover:bg-gray-100">
                      {expandedAlbums[album.id] ? (
                        <ChevronUp className="h-5 w-5 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-gray-500" />
                      )}
                    </button>
                  </div>
                  
                  {expandedAlbums[album.id] && (
                    <div className="p-4 pt-0">
                      {album.media && album.media.length > 0 ? (
                        <MediaGrid 
                          items={album.media} 
                          onDeleteMedia={async (mediaId) => {
                            try {
                              setIsLoading(true);
                              setError("");
                              await mediaAPI.deleteMedia(mediaId);
                              
                              // Refresh the albums and media data
                              await fetchAlbumsAndMedia();
                            } catch (error: any) {
                              console.error("Error deleting media:", error);
                              setError(error.response?.data?.detail || "Failed to delete media");
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                        />
                      ) : (
                        <div className="text-center py-8 text-gray-400">
                          No media in this album yet. Upload some media to get started!
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </main>
      
      <UploadButton onClick={() => {
        if (albums.length === 0) {
          setError("Please create an album first before uploading media");
          setIsCreateAlbumModalOpen(true);
        } else {
          setIsUploadModalOpen(true);
        }
      }} />
      
      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleUpload}
      />
      
      <CreateAlbumModal
        isOpen={isCreateAlbumModalOpen}
        onClose={() => setIsCreateAlbumModalOpen(false)}
        onCreateAlbum={handleCreateAlbum}
      />
    </div>
  );
};

export default Home;
