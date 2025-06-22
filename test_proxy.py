#!/usr/bin/env python3
"""Test script to verify proxy functionality for Spotify and YouTube"""

import asyncio
from spotify import search_spotify, fetch_song_info, SPOTIFY_TOKEN_MANAGER

async def test_spotify_proxy():
    """Test Spotify API access through proxy"""
    print("Testing Spotify API access through proxy...")
    
    try:
        # Check if credentials are available
        from config import CLIENT_ID, CLIENT_SECRET
        if not CLIENT_ID or not CLIENT_SECRET:
            print("   ⚠ Spotify credentials not set in environment variables")
            print("   Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to test Spotify functionality")
            return "skipped"
        
        # Test token acquisition
        print("1. Testing Spotify token acquisition...")
        token = await SPOTIFY_TOKEN_MANAGER.get_token()
        if token:
            print("   ✓ Successfully obtained Spotify access token")
        else:
            print("   ✗ Failed to obtain Spotify access token")
            return False
            
        # Test search functionality
        print("2. Testing Spotify search...")
        results = await search_spotify("Bohemian Rhapsody Queen", limit=1)
        if results:
            print(f"   ✓ Successfully found track: {results[0]['artist']} - {results[0]['title']}")
            print(f"   URL: {results[0]['url']}")
            return results[0]['url']
        else:
            print("   ✗ No search results found")
            return False
            
    except KeyError as e:
        print(f"   ✗ Missing key in Spotify API response: {str(e)}")
        print("   This might be due to invalid credentials or API changes")
        return False
    except Exception as e:
        print(f"   ✗ Spotify test failed: {str(e)}")
        return False

async def test_song_link_api():
    """Test song.link API access through proxy"""
    print("\nTesting song.link API access through proxy...")
    
    try:
        # Test with a known Spotify URL
        test_url = "https://open.spotify.com/track/4u7EnebtmKWzUH433cf5Qv"  # Bohemian Rhapsody
        print(f"Testing with URL: {test_url}")
        
        result = await fetch_song_info(test_url)
        if result and result.get('title'):
            print(f"   ✓ Successfully fetched song info: {result['title']} by {result.get('artistName', 'Unknown')}")
            print(f"   Available platforms: {list(result.get('platform_urls', {}).keys())}")
            return True
        else:
            print("   ✗ Failed to fetch song info")
            return False
            
    except Exception as e:
        print(f"   ✗ song.link API test failed: {str(e)}")
        return False

async def test_ip_check():
    """Check what IP address is being used through proxy"""
    print("\nTesting IP address through proxy...")
    
    try:
        import aiohttp
        from aiohttp_socks import ProxyConnector
        
        # Check IP without proxy
        print("1. Checking IP without proxy...")
        async with aiohttp.ClientSession() as session:
            async with session.get('https://httpbin.org/ip') as response:
                data = await response.json()
                local_ip = data['origin']
                print(f"   Local IP: {local_ip}")
        
        # Check IP with proxy
        print("2. Checking IP with proxy...")
        connector = ProxyConnector.from_url("socks5://127.0.0.1:1080")
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get('https://httpbin.org/ip') as response:
                data = await response.json()
                proxy_ip = data['origin']
                print(f"   Proxy IP: {proxy_ip}")
                
        if local_ip != proxy_ip:
            print("   ✓ Proxy is working - IP addresses are different")
            return True
        else:
            print("   ⚠ Proxy might not be working - IP addresses are the same")
            return False
            
    except Exception as e:
        print(f"   ✗ IP check failed: {str(e)}")
        return False

def test_youtube_proxy():
    """Test YouTube-dl proxy configuration"""
    print("\nTesting YouTube-dl proxy configuration...")
    
    try:
        import yt_dlp as youtube_dl
        
        # Test configuration
        ydl_opts = {
            'proxy': 'socks5://127.0.0.1:1080',
            'quiet': True,
            'no_warnings': True,
        }
        
        test_url = "https://www.youtube.com/watch?v=fJ9rUzIMcZQ"  # Bohemian Rhapsody
        print(f"Testing with URL: {test_url}")
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            if info:
                print(f"   ✓ Successfully extracted info: {info.get('title', 'Unknown title')}")
                print(f"   Duration: {info.get('duration', 'Unknown')} seconds")
                return True
            else:
                print("   ✗ Failed to extract video info")
                return False
                
    except Exception as e:
        print(f"   ✗ YouTube test failed: {str(e)}")
        return False

async def main():
    """Run all proxy tests"""
    print("=" * 60)
    print("PROXY FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Check if proxy is accessible
    print("Checking if SOCKS5 proxy is accessible at 127.0.0.1:1080...")
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 1080))
        sock.close()
        if result == 0:
            print("✓ Proxy is accessible\n")
        else:
            print("✗ Proxy is not accessible - make sure ss-local is running")
            return
    except Exception as e:
        print(f"✗ Error checking proxy: {e}")
        return
    
    # Run tests
    results = []
    
    # Test IP check first
    ip_result = await test_ip_check()
    results.append(("IP Check", ip_result))
    
    # Test Spotify
    spotify_result = await test_spotify_proxy()
    if spotify_result == "skipped":
        results.append(("Spotify API", "SKIPPED"))
    else:
        results.append(("Spotify API", bool(spotify_result)))
    
    # Test song.link API
    songlink_result = await test_song_link_api()
    results.append(("Song.link API", songlink_result))
    
    # Test YouTube
    youtube_result = test_youtube_proxy()
    results.append(("YouTube-dl", youtube_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result == "SKIPPED":
            status = "⊝ SKIP"
        else:
            status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<20}: {status}")
    
    total_passed = sum(1 for _, result in results if result is True)
    total_skipped = sum(1 for _, result in results if result == "SKIPPED")
    print(f"\nTotal: {total_passed}/{len(results) - total_skipped} tests passed ({total_skipped} skipped)")
    
    if total_passed == len(results) - total_skipped:
        print("\n🎉 All tests passed! Your proxy setup is working correctly.")
    else:
        failed_count = len(results) - total_passed - total_skipped
        print(f"\n⚠ {failed_count} test(s) failed. Please check your proxy configuration.")

if __name__ == "__main__":
    asyncio.run(main())
