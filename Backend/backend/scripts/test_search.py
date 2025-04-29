#!/usr/bin/env python3
"""
Test script for search functionality.
Checks the Qdrant database and tests the search functionality.
"""

import os
import sys
import asyncio
from typing import List, Dict, Any
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.vector_db import qdrant_manager
from app.core.clip_text_client import clip_text_client

async def test_collection_stats():
    """Test basic collection stats in Qdrant."""
    print("Testing Qdrant collection stats...")
    collection_name = "image_embeddings"
    
    # Check if collection exists
    exists = qdrant_manager.check_collection_exists(collection_name)
    print(f"Collection '{collection_name}' exists: {exists}")
    
    if exists:
        try:
            # Get collection info
            collection_info = qdrant_manager.client.get_collection(collection_name)
            print(f"Collection '{collection_name}' info:")
            print(f"- Status: {collection_info.status}")
            print(f"- Vector size: {collection_info.config.params.vectors.size}")
            print(f"- Vector count: {collection_info.vectors_count}")
            print(f"- Distance: {collection_info.config.params.vectors.distance}")
            
            # Count points
            count_result = qdrant_manager.client.count(collection_name=collection_name)
            print(f"Total points count: {count_result.count}")
            
            # Check some points
            if count_result.count > 0:
                print("\nSample points:")
                # Get a sample of points from the collection
                try:
                    scroll_result = qdrant_manager.client.scroll(
                        collection_name=collection_name,
                        limit=5
                    )
                    
                    for i, point in enumerate(scroll_result.points):
                        print(f"Point {i+1}:")
                        print(f"- ID: {point.id}")
                        print(f"- Vector dimensions: {len(point.vector)}")
                        print(f"- Payload: {point.payload}")
                except Exception as e:
                    print(f"Error listing points: {e}")
            
        except Exception as e:
            print(f"Error getting collection info: {e}")
    
    return exists

async def test_text_embedding():
    """Test text embedding functionality."""
    print("\nTesting text embedding...")
    
    test_queries = [
        "a dog playing in the park",
        "beach sunset",
        "city buildings",
        "family portrait"
    ]
    
    for query in test_queries:
        print(f"\nGenerating embedding for query: '{query}'")
        try:
            embedding = await clip_text_client.get_text_embedding(query)
            if embedding:
                print(f"Successfully generated embedding with {len(embedding)} dimensions")
                print(f"First few values: {embedding[:5]}...")
            else:
                print("Failed to generate embedding")
        except Exception as e:
            print(f"Error generating embedding: {e}")
    
    return True

async def test_search():
    """Test search functionality directly."""
    print("\nTesting search functionality...")
    
    test_queries = [
        "a dog playing in the park",
        "beach sunset",
        "city buildings",
        "family portrait"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        try:
            # Generate embedding
            embedding = await clip_text_client.get_text_embedding(query)
            if not embedding:
                print("Failed to generate embedding")
                continue
                
            print(f"Generated embedding with {len(embedding)} dimensions")
            
            # Search without user filter
            print("Searching without filter...")
            results = qdrant_manager.search_similar(
                collection_name="image_embeddings",
                query_vector=embedding,
                limit=5,
                score_threshold=0.2
            )
            
            if results:
                print(f"Found {len(results)} results")
                for i, result in enumerate(results):
                    print(f"Result {i+1}:")
                    print(f"- ID: {result['id']}")
                    print(f"- Score: {result['score']}")
                    print(f"- Payload: {result['payload']}")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error searching: {e}")
    
    return True

async def main():
    """Main function."""
    print("=== SEARCH FUNCTIONALITY TEST ===\n")
    
    # Test collection stats
    collection_exists = await test_collection_stats()
    
    if not collection_exists:
        print("\nERROR: Collection 'image_embeddings' does not exist!")
        print("Please make sure Qdrant is running and the collection is created.")
        return
    
    # Test text embedding
    await test_text_embedding()
    
    # Test search
    await test_search()
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main()) 