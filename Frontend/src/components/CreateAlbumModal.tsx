import { useState, useEffect } from "react";
import { X } from "lucide-react";

interface CreateAlbumModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateAlbum: (name: string) => Promise<void>;
}

const CreateAlbumModal = ({ isOpen, onClose, onCreateAlbum }: CreateAlbumModalProps) => {
  const [albumName, setAlbumName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Clear form state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setAlbumName("");
      setError("");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedName = albumName.trim();
    if (!trimmedName) {
      setError("Album name is required");
      return;
    }
    
    if (trimmedName.length < 3) {
      setError("Album name must be at least 3 characters");
      return;
    }

    try {
      setIsLoading(true);
      setError("");
      console.log("Submitting album creation with name:", trimmedName);
      await onCreateAlbum(trimmedName);
      // The modal will be closed by the parent component upon successful creation
    } catch (error: any) {
      console.error("Album creation error:", error);
      // Extract detailed error information for debugging
      let errorMessage = "Failed to create album. Please try again.";
      if (error.response) {
        console.error("Response status:", error.response.status);
        console.error("Response headers:", error.response.headers);
        console.error("Response data:", error.response.data);
        
        // Handle validation errors from FastAPI backend
        if (error.response.data && error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // FastAPI validation errors are often returned as an array
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Album</h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
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

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="albumName" className="block text-sm font-medium text-gray-700 mb-1">
              Album Name
            </label>
            <input
              type="text"
              id="albumName"
              value={albumName}
              onChange={(e) => setAlbumName(e.target.value)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter album name"
              autoFocus
              minLength={3}
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Album name must be at least 3 characters long
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary flex items-center"
            >
              {isLoading && (
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              {isLoading ? "Creating..." : "Create Album"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAlbumModal; 