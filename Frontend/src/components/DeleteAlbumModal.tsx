import { X } from "lucide-react";

interface DeleteAlbumModalProps {
  isOpen: boolean;
  albumTitle: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
}

const DeleteAlbumModal = ({ 
  isOpen, 
  albumTitle, 
  onClose, 
  onConfirm, 
  isDeleting 
}: DeleteAlbumModalProps) => {
  
  if (!isOpen) return null;
  
  const handleConfirm = async () => {
    try {
      await onConfirm();
    } catch (error) {
      console.error("Error in delete confirmation:", error);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-red-600">Delete Album</h2>
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mb-6">
          <p className="text-gray-700 mb-2">
            Are you sure you want to delete the album <span className="font-semibold">"{albumTitle}"</span>?
          </p>
          <p className="text-red-500 text-sm">
            This action cannot be undone. All media in this album will also be deleted.
          </p>
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 flex items-center"
          >
            {isDeleting && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {isDeleting ? "Deleting..." : "Delete Album"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteAlbumModal; 