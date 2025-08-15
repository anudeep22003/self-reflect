#!/usr/bin/env python3
"""
AI Self-Reflection Backend Demo Script

This script demonstrates the AI self-reflection backend capabilities by running
example queries against both available API endpoints and displaying results
with pretty formatting.

Usage:
    python scripts/demo.py [--port PORT] [--host HOST]

Requirements:
    - Backend server must be running
    - Dependencies: requests, rich
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

try:
    import requests
    from requests.exceptions import ConnectionError, RequestException
except ImportError:
    print("❌ Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.syntax import Syntax
except ImportError:
    print("❌ Error: 'rich' library not found. Install with: pip install rich")
    sys.exit(1)


class AIReflectionDemo:
    def __init__(self, host: str = "localhost", port: int = 8087):
        self.base_url = f"http://{host}:{port}"
        self.console = Console()
        
    def check_server_health(self) -> bool:
        """Check if the server is running and accessible."""
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except (ConnectionError, RequestException):
            return False
    
    def make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a request to the API endpoint with error handling."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Processing query...", total=None)
                
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                progress.remove_task(task)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.console.print(f"❌ API Error: {response.status_code}", style="red")
                try:
                    error_detail = response.json()
                    self.console.print(f"Detail: {error_detail}", style="red")
                except:
                    self.console.print(f"Response: {response.text}", style="red")
                return None
                
        except RequestException as e:
            self.console.print(f"❌ Request failed: {e}", style="red")
            return None
    
    def display_response(self, response: Dict[str, Any], endpoint_name: str):
        """Display API response with pretty formatting."""
        
        # Create main panel
        panel_title = f"🤖 {endpoint_name} Response"
        
        # Extract base response
        base_response = response.get("base_response", {})
        choices = base_response.get("choices", [])
        content = choices[0].get("message", {}).get("content", "No content") if choices else "No response"
        
        # Create content display
        content_panel = Panel(
            content,
            title="💬 AI Response",
            border_style="blue",
            box=box.ROUNDED
        )
        
        # Extract reflection data
        reflection = response.get("reflection_response", {})
        
        # Create reflection table
        reflection_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        reflection_table.add_column("Dimension", style="cyan", width=12)
        reflection_table.add_column("Rating", style="green", width=8)
        reflection_table.add_column("Reasoning", style="white")
        
        dimensions = ["completeness", "accuracy", "reasoning"]
        for dim in dimensions:
            if dim in reflection:
                rating = reflection[dim].get("rating", "N/A")
                reason = reflection[dim].get("reason", "No reason provided")
                
                # Color code ratings
                rating_style = "green" if rating == "A" else "yellow" if rating == "B" else "red"
                reflection_table.add_row(
                    dim.title(),
                    Text(rating, style=rating_style),
                    reason
                )
        
        # Add numerical score
        numerical_score = reflection.get("numerical_score", 0.0)
        score_color = "green" if numerical_score >= 0.8 else "yellow" if numerical_score >= 0.5 else "red"
        
        # Display usage information
        usage = base_response.get("usage", {})
        model = base_response.get("model", "Unknown")
        
        metadata_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        metadata_table.add_column("Key", style="dim")
        metadata_table.add_column("Value")
        
        metadata_table.add_row("📊 Numerical Score", f"[{score_color}]{numerical_score:.2f}[/{score_color}]")
        metadata_table.add_row("🔧 Model", model)
        metadata_table.add_row("🪙 Total Tokens", str(usage.get("total_tokens", "N/A")))
        
        # Create final layout
        self.console.print()
        self.console.print(Panel(panel_title, style="bold blue"))
        self.console.print(content_panel)
        self.console.print()
        self.console.print(Panel(reflection_table, title="🧠 Self-Reflection Analysis", border_style="magenta"))
        self.console.print()
        self.console.print(Panel(metadata_table, title="📈 Metadata", border_style="dim"))
    
    def run_demo_query(self, query: str, endpoint: str, endpoint_name: str):
        """Run a single demo query and display results."""
        self.console.print(f"\n🚀 Testing {endpoint_name}")
        self.console.print(f"📝 Query: [italic]{query}[/italic]")
        
        response = self.make_request(endpoint, {"query": query})
        
        if response:
            self.display_response(response, endpoint_name)
        else:
            self.console.print("❌ Failed to get response", style="red")
    
    def run_full_demo(self):
        """Run the complete demonstration."""
        
        # Header
        self.console.print()
        self.console.print(Panel.fit(
            "🤖 AI Self-Reflection Backend Demo\n\n"
            "This demo showcases the AI system's ability to generate responses\n"
            "and evaluate them across completeness, accuracy, and reasoning quality.",
            title="Welcome",
            border_style="bright_blue",
            box=box.DOUBLE
        ))
        
        # Check server health
        self.console.print("\n🔍 Checking server status...")
        if not self.check_server_health():
            self.console.print(f"❌ Server not accessible at {self.base_url}", style="red")
            self.console.print("💡 Make sure the backend is running with:", style="yellow")
            self.console.print("   cd backend && uvicorn main:app --reload --port 8087", style="yellow")
            return
        
        self.console.print(f"✅ Server is running at {self.base_url}", style="green")
        
        # Demo queries
        demo_queries = [
            {
                "query": "What is 1 + 1?",
                "description": "Simple mathematical question"
            },
            {
                "query": "what is the third month in alphabetical order",
                "description": "Alphabetical ordering question"
            },
            {
                "query": "How many syllables are in the following phrase: \"How much wood could a woodchuck chuck if a woodchuck could chuck wood\"? Answer with a single number only.",
                "description": "Syllable counting task"
            }
        ]
        
        # Test both endpoints
        endpoints = [
            {
                "path": "/api/chat/chat_with_score",
                "name": "Basic Reflection (Fast & Cost-Optimized)",
                "description": "Static reasoning from YAML prompts"
            },
            {
                "path": "/api/chat/chat_with_score_reflect_and_reason", 
                "name": "Advanced Reflection (AI-Generated Reasoning)",
                "description": "Dynamic reasoning with higher latency"
            }
        ]
        
        for endpoint_info in endpoints:
            self.console.print(f"\n{'='*80}")
            self.console.print(Panel.fit(
                f"🎯 {endpoint_info['name']}\n{endpoint_info['description']}",
                border_style="bright_green"
            ))
            
            for i, demo in enumerate(demo_queries, 1):
                self.console.print(f"\n📋 Demo {i}: {demo['description']}")
                self.run_demo_query(
                    demo["query"], 
                    endpoint_info["path"], 
                    endpoint_info["name"]
                )
                
                # Add pause between queries
                if i < len(demo_queries):
                    time.sleep(1)
        
        # Footer
        self.console.print("\n" + "="*80)
        self.console.print(Panel.fit(
            "🎉 Demo completed!\n\n"
            f"📚 API Documentation: {self.base_url}/docs\n"
            f"🔗 OpenAPI Schema: {self.base_url}/openapi.json",
            title="Demo Complete",
            border_style="bright_green",
            box=box.DOUBLE
        ))


def main():
    parser = argparse.ArgumentParser(description="AI Self-Reflection Backend Demo")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8087, help="Server port (default: 8087)")
    
    args = parser.parse_args()
    
    demo = AIReflectionDemo(host=args.host, port=args.port)
    demo.run_full_demo()


if __name__ == "__main__":
    main()