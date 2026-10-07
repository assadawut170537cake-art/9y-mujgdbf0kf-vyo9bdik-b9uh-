import asyncio
from typing import List, Dict, Any
from master_fetch.search_engines import multi_search
from master_fetch.fetcher import HTTPSession
import json
import logging

logger = logging.getLogger("web_researcher")

class WebResearcher:
    def __init__(self):
        pass

    async def search_and_synthesize(self, query: str, num_sources: int = 20) -> str:
        print(f"[*] Starting research on: {query}")
        
        # 1. Search for links using multi_search from search_engines
        search_results, reports = await multi_search(query, max_results=num_sources)
        if not search_results:
            return "No results found."
            
        print(f"[*] Found {len(search_results)} sources. Fetching content...")
        
        # 2. Fetch content for top results using HTTPSession
        synthesized_data = []
        
        async with HTTPSession() as session:
            for result in search_results[:num_sources]:
                url = result.url
                title = result.title
                if not url:
                    continue
                    
                try:
                    # HTTPSession handles Paritok auth via env var inside _build_headers
                    response = await session.get(url, follow_redirects=True)
                    if response.status == 200:
                        text = response.content[:2000] # Get first 2000 chars to avoid massive context
                        synthesized_data.append({
                            "title": title,
                            "url": url,
                            "summary": text
                        })
                    else:
                        print(f"[-] Failed to fetch {url}: HTTP {response.status}")
                except Exception as e:
                    print(f"[-] Error fetching {url}: {e}")
                
        # 3. Format output
        report = f"# Research Report: {query}\n\n"
        for idx, data in enumerate(synthesized_data):
            report += f"## {idx+1}. {data['title']}\n"
            report += f"**Source:** {data['url']}\n"
            report += f"**Extract:** {data['summary'][:500]}...\n\n"
            
        return report

async def main():
    researcher = WebResearcher()
    query = "ความสามารถใหม่ๆ ของ AI Agents ในปี 2026"
    report = await researcher.search_and_synthesize(query, num_sources=20)
    
    with open("research_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    print("[+] Research complete. Saved to research_report.md")

if __name__ == "__main__":
    asyncio.run(main())
