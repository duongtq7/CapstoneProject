import { useState } from "react";
import Navbar from "../components/Navbar";
import MediaGrid from "../components/MediaGrid";  // Grid component for displaying media
import { Search as SearchIcon } from "lucide-react";
import { MediaItem } from "../types";
import { searchAPI } from "../lib/api";
import { useToast } from "@/components/ui/use-toast";

const Search = () => {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<MediaItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const { toast } = useToast();
  
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    setHasSearched(true);
    
    try {
      console.log(`Executing search for query: "${query}"`);
      
      // Call the search API
      const response = await searchAPI.searchMedia(query);
      
      console.log(`Search complete, received ${response.results.length} results`);
      
      // Log the first result for debugging
      if (response.results.length > 0) {
        console.log("Sample result:", response.results[0]);
      }
      
      setResults(response.results);
      
      if (response.count === 0) {
        console.log("No search results found");
        toast({
          title: "No results found",
          description: "Try a different search term or upload more media.",
          variant: "default",
        });
      } else {
        console.log(`Found ${response.count} results for "${query}"`);
      }
    } catch (error) {
      console.error("Search error:", error);
      toast({
        title: "Search failed",
        description: "There was a problem with your search. Please try again.",
        variant: "destructive",
      });
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-4">Search Media</h1>
          
          <form onSubmit={handleSearch}>
            <div className="flex">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by description or content..."
                  className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                />
              </div>
              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className={`px-4 py-2 text-white rounded-r-md ${
                  isSearching || !query.trim()
                    ? "bg-gray-400"
                    : "bg-primary hover:bg-primary/90"
                }`}
              >
                {isSearching ? (
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  "Search"
                )}
              </button>
            </div>
            
            <p className="mt-2 text-sm text-gray-600">
              Try searching for concepts, objects, or scenes in your media
            </p>
          </form>
        </div>
        
        {hasSearched && (
          <div>
            <h2 className="text-xl font-semibold mb-4">
              {results.length > 0 
                ? `Found ${results.length} result${results.length === 1 ? '' : 's'} for "${query}"`
                : `No results found for "${query}"`}
            </h2>
            
            {results.length > 0 && <MediaGrid items={results} />}
            
            {results.length === 0 && !isSearching && (
              <div className="text-center py-12 bg-gray-100 rounded-lg">
                <SearchIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No matching media found</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Try searching with different terms or upload more media
                </p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Search;
