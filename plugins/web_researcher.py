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

PLUGIN = {
    "name": "web_researcher",
    "description": "Deep multi-source web researcher and synthesizer. Searches multiple engines and generates full research reports. Trigger: 'วิจัยเชิงลึก', 'ค้นคว้าข้อมูลละเอียด', 'deep research'.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Research question or query topic"},
            "num_sources": {"type": "INTEGER", "description": "Number of sources to synthesize (default: 10)"}
        },
        "required": ["query"]
    }
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    query = parameters.get("query", "").strip()
    num_sources = int(parameters.get("num_sources", 10))
    if not query:
        return "กรุณาระบุหัวข้อที่ต้องการค้นคว้าวิจัยครับ"
    try:
        researcher = WebResearcher()
        loop = asyncio.new_event_loop()
        report = loop.run_until_complete(researcher.search_and_synthesize(query, num_sources=num_sources))
        loop.close()
        save_file = f"research_{query[:20].replace(' ', '_')}.md"
        with open(save_file, "w", encoding="utf-8") as f:
            f.write(report)
        msg = f"วิจัยหัวข้อ '{query}' จาก {num_sources} แหล่งข้อมูลเสร็จสิ้น บันทึกรายงานไว้ที่ {save_file} เรียบร้อยแล้วครับ"
        if player and hasattr(player, "write_log"):
            player.write_log(f"[WebResearcher] Completed research: {query}")
        return msg
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการวิจัย: {e}"

async def main():
    researcher = WebResearcher()
    query = "ความสามารถใหม่ๆ ของ AI Agents ในปี 2026"
    report = await researcher.search_and_synthesize(query, num_sources=20)
    
    with open("research_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    print("[+] Research complete. Saved to research_report.md")

if __name__ == "__main__":
    asyncio.run(main())

