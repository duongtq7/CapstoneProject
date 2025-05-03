import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import MediaGrid from "../components/MediaGrid";  // Grid component for displaying media
import { Search as SearchIcon, Globe, Sliders } from "lucide-react";
import { MediaItem } from "../types";
import { searchAPI } from "../lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";

const Search = () => {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<MediaItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [translateEnabled, setTranslateEnabled] = useState(true);
  const [limit, setLimit] = useState(10);
  const [scoreThreshold, setScoreThreshold] = useState(0.1);
  const [deduplicateVideos, setDeduplicateVideos] = useState(true);
  const [rawResultsCount, setRawResultsCount] = useState(0);
  const { toast } = useToast();
  
  // Log any API configuration issues on component mount
  useEffect(() => {
    console.log("Search component mounted");
    console.log("API Base URL:", import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1');
  }, []);
  
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    setHasSearched(true);
    setDebugInfo(null);
    
    try {
      console.log(`[Search] Starting search for query: "${query}"`);
      console.log(`[Search] Current time: ${new Date().toISOString()}`);
      console.log(`[Search] Translation enabled: ${translateEnabled}`);
      console.log(`[Search] Limit: ${limit}, Score threshold: ${scoreThreshold}`);
      console.log(`[Search] Deduplicate videos: ${deduplicateVideos}`);
      
      // Call the search API with translation parameter
      const response = await searchAPI.searchMedia(query, limit, translateEnabled, scoreThreshold);
      
      console.log(`[Search] API response:`, response);
      console.log(`[Search] Found ${response.results.length} results`);
      
      // Store raw results count
      setRawResultsCount(response.results.length);
      
      // Store debug info if available
      if (response.debug_info) {
        console.log(`[Search] Debug info:`, response.debug_info);
        setDebugInfo(response.debug_info);
      }
      
      // Log the first result for debugging
      if (response.results.length > 0) {
        console.log("[Search] Sample result:", response.results[0]);
      }
      
      // Filter results to deduplicate videos if enabled
      let filteredResults = response.results;
      if (deduplicateVideos) {
        // Keep track of media_ids we've seen
        const seenMediaIds = new Set<string>();
        filteredResults = response.results.filter(item => {
          // For video_embeddings, extract the parent video id from metadata
          const mediaId = item.metadata?.collection === "video_embeddings" && item.metadata?.media_id 
            ? item.metadata.media_id 
            : item.id;
          
          // If we've seen this media_id before, filter it out
          if (seenMediaIds.has(mediaId)) {
            return false;
          }
          
          // Otherwise add it to seen and keep it
          seenMediaIds.add(mediaId);
          return true;
        });
        
        console.log(`[Search] After deduplication: ${filteredResults.length} results`);
      }
      
      setResults(filteredResults);
      
      if (filteredResults.length === 0) {
        console.log("[Search] No results found");
        toast({
          title: "No results found",
          description: "Try a different search term or upload more media.",
          variant: "default",
        });
      } else {
        console.log(`[Search] Successfully found ${filteredResults.length} results for "${query}"`);
      }
    } catch (error: any) {
      console.error("[Search] Error during search:", error);
      
      // Log detailed error information
      if (error.response) {
        console.error("[Search] Response status:", error.response.status);
        console.error("[Search] Response headers:", error.response.headers);
        console.error("[Search] Response data:", error.response.data);
        console.error("[Search] Request URL:", error.config?.url);
        console.error("[Search] Request method:", error.config?.method);
        console.error("[Search] Request params:", error.config?.params);
        console.error("[Search] Request base URL:", error.config?.baseURL);
      }
      
      toast({
        title: "Search failed",
        description: error.response?.data?.detail || "There was a problem with your search. Please try again.",
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
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by description or content..."
                  className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                />
              </div>
              
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="h-full" title="Search Settings">
                    <Sliders className="h-4 w-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <h4 className="font-medium leading-none">Search Settings</h4>
                      <p className="text-sm text-muted-foreground">
                        Configure your search parameters
                      </p>
                    </div>
                    
                    <div className="grid gap-2">
                      <div className="grid gap-1">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="limit">Result Limit</Label>
                          <div className="flex items-center gap-2">
                            <Input
                              id="limit"
                              type="number"
                              min={1}
                              max={100}
                              value={limit}
                              onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
                              className="w-20 h-8"
                            />
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid gap-1">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="threshold">Similarity Threshold</Label>
                          <span className="text-sm">{scoreThreshold.toFixed(2)}</span>
                        </div>
                        <Slider
                          id="threshold"
                          min={0}
                          max={1}
                          step={0.01}
                          value={[scoreThreshold]}
                          onValueChange={(value) => setScoreThreshold(value[0])}
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>More Results</span>
                          <span>Higher Quality</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label htmlFor="deduplicate" className="mr-2">Deduplicate Videos</Label>
                        <Switch
                          id="deduplicate"
                          checked={deduplicateVideos}
                          onCheckedChange={setDeduplicateVideos}
                          aria-label="Toggle video deduplication"
                        />
                      </div>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
              
              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className={`px-4 py-2 text-white rounded-md ${
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
            
            <div className="flex items-center mt-2">
              <p className="text-sm text-gray-600">
                Try searching for concepts, objects, or scenes in your media
              </p>
              
              {debugInfo && (
                <div className="ml-auto text-xs text-gray-500">
                  {debugInfo.score_threshold && (
                    <span className="mr-2">Threshold: {debugInfo.score_threshold}</span>
                  )}
                  {debugInfo.processed_results_count !== undefined && (
                    <span className="mr-2">Results: {debugInfo.processed_results_count}/{debugInfo.raw_results_count || 0}</span>
                  )}
                  {deduplicateVideos && (
                    <span>Deduplicated: {results.length}/{rawResultsCount}</span>
                  )}
                </div>
              )}
            </div>
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
