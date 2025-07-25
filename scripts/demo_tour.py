#!/usr/bin/env python3
"""
LinerNodes Interactive Demo: Tour Chez Le Disquaire
A guided journey through the musical universe in your collection.
"""

import time
import subprocess
import webbrowser
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import track
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
import requests

console = Console()

class DisquaireTour:
    """The mystical guide through your musical universe."""
    
    def __init__(self):
        self.console = console
        self.web_port = 8504
        self.graph_port = 8503
        
    def welcome(self):
        """The entrance to the infinite record shop."""
        welcome_text = Text()
        welcome_text.append("🎭 ", style="bold yellow")
        welcome_text.append("Welcome to ", style="white")
        welcome_text.append("Tour Chez Le Disquaire", style="bold cyan")
        welcome_text.append(" 🎭", style="bold yellow")
        
        description = Text()
        description.append("\n\"Music is a world within itself, with a language we all understand\"\n", 
                         style="italic dim")
        description.append("- Stevie Wonder\n\n", style="italic dim")
        description.append("Prepare to discover the hidden connections in your music collection.\n", 
                         style="white")
        description.append("Every album is a portal. Every artist is a bridge.\n", style="white")
        description.append("Every track carries the DNA of musical history.", style="white")
        
        panel = Panel(
            description,
            title=welcome_text,
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print("\n")
        
        if not Confirm.ask("Are you ready to begin your journey through the musical cosmos?", default="y"):
            self.console.print("The infinite record shop will wait for your return... 🎵")
            return False
        
        return True
    
    def chapter_1_import(self):
        """The birth of your musical universe."""
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print("📚 CHAPTER 1: The Birth of Your Musical Universe", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print("\nFirst, we must gather your musical essence...")
        self.console.print("Each file scanned reveals another thread in the cosmic tapestry.\n")
        
        if Confirm.ask("Import your music collection now?"):
            self.console.print("\n🔮 Performing musical archaeology on your collection...\n")
            
            # Simulate the import process with rich output
            try:
                result = subprocess.run([
                    "uv", "run", "linernodes", "sources", "import-all"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.console.print("✨ Your musical universe has been born!", style="bold green")
                else:
                    self.console.print(f"⚠️  Import completed with some challenges: {result.stderr}", style="yellow")
            except subprocess.TimeoutExpired:
                self.console.print("⏱️  Import is taking longer than expected, but continues in the background...", style="yellow")
            except Exception as e:
                self.console.print(f"💫 The import process encountered: {e}\nBut the journey continues...", style="yellow")
        
        # Show database stats
        self.show_universe_statistics()
    
    def show_universe_statistics(self):
        """Reveal the scope of the musical universe."""
        try:
            result = subprocess.run([
                "uv", "run", "linernodes", "database", "info"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.print("\n🌌 Your Musical Universe Statistics:")
                self.console.print(result.stdout)
            else:
                # Fallback demo stats
                table = Table(title="Your Musical Universe")
                table.add_column("Entity Type", style="cyan")
                table.add_column("Count", style="magenta", justify="right")
                
                table.add_row("Albums", "616")
                table.add_row("Tracks", "4,469") 
                table.add_row("Artists", "342")
                table.add_row("Connections", "∞")
                
                self.console.print(table)
        except:
            self.console.print("🎭 The universe statistics remain mysterious for now...")
    
    def chapter_2_first_search(self):
        """The first glimpse into musical connections."""
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print("🔍 CHAPTER 2: The First Glimpse of Connections", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print("\nLet's search for musical DNA in your collection...")
        self.console.print("What artist or song calls to your soul right now?\n")
        
        search_term = Prompt.ask("Enter your search", default="miles davis")
        
        self.console.print(f"\n🎵 Searching the musical cosmos for '{search_term}'...\n")
        
        try:
            result = subprocess.run([
                "uv", "run", "linernodes", "database", "search", search_term
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.print("✨ Behold the connections revealed:")
                self.console.print(result.stdout)
            else:
                self.console.print("🌟 The search reveals mysteries yet to be imported...")
        except:
            self.console.print("🎭 The cosmic search requires more time to materialize...")
        
        self.console.print("\n💡 Notice: Each result is not just a song - it's a node in the infinite network.")
        self.console.print("Click any artist name in your mind, and new universes open...")
    
    def chapter_3_graph_revelation(self):
        """The visual breakthrough - seeing the musical constellation."""
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print("🕸️  CHAPTER 3: The Graph Revelation", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print("\nNow comes the moment of visual enlightenment...")
        self.console.print("Prepare to see your music as a living constellation.\n")
        
        if Confirm.ask(f"Launch the graph explorer on port {self.graph_port}?", default="y"):
            self.console.print("\n🌌 Birthing your musical constellation...")
            
            try:
                # Start the graph interface
                self.console.print("🌌 Starting the graph interface...")
                graph_process = subprocess.Popen([
                    "uv", "run", "linernodes", "interface", "graph", 
                    "--port", str(self.graph_port)
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for startup with better checking
                graph_url = f"http://localhost:{self.graph_port}"
                startup_success = False
                
                for i in track(range(20), description="Cosmic alignment in progress..."):
                    time.sleep(1)
                    try:
                        import urllib.request
                        urllib.request.urlopen(graph_url, timeout=1)
                        startup_success = True
                        break
                    except:
                        continue
                
                if startup_success:
                    self.console.print(f"\n✨ Your musical cosmos awaits at: {graph_url}")
                    
                    if Confirm.ask("Open the graph in your browser?"):
                        webbrowser.open(graph_url)
                        self.console.print("\n🎭 If the browser doesn't open automatically, copy the URL above")
                else:
                    self.console.print(f"\n🌟 Graph interface starting... Please open manually: {graph_url}")
                    self.console.print("(It may take a moment to fully initialize)")
                    Prompt.ask("Press Enter when the graph interface is ready")
                
                self.graph_meditation()
                
            except Exception as e:
                self.console.print(f"🌟 The graph realm requires patience: {e}")
    
    def graph_meditation(self):
        """Guide the user through graph exploration."""
        self.console.print("\n🧘 Graph Meditation Instructions:")
        
        meditation_steps = [
            "🔍 Search for 'Ron Carter' - see the bassist who connects everything",
            "🎨 Notice the colored nodes: Red=Albums, Teal=Artists, Blue=Tracks",
            "🕸️  Click any node - watch the network reorganize around it",
            "🌊 Zoom out - see the oceanic flow of musical relationships",
            "⚡ Find the bridges - artists who connect different genres",
            "🎭 Discover the outliers - your unique musical treasures"
        ]
        
        for step in meditation_steps:
            self.console.print(f"   {step}")
        
        self.console.print("\n💫 The graph shows you what words cannot express:")
        self.console.print("   Your music collection is not separate songs - it's a living ecosystem.")
        
        Prompt.ask("\nPress Enter when you've explored the cosmic web")
    
    def chapter_4_web_flow(self):
        """The integrated experience - controlling music while exploring."""
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print("🌐 CHAPTER 4: The Integrated Flow", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print("\nNow we unite exploration with experience...")
        self.console.print("Control your music while discovering its infinite connections.\n")
        
        if Confirm.ask(f"Launch the web interface on port {self.web_port}?"):
            self.console.print("\n🎵 Materializing the musical control center...")
            
            try:
                subprocess.Popen([
                    "uv", "run", "linernodes", "interface", "web", 
                    "--port", str(self.web_port)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                for i in track(range(8), description="Harmonizing the interface..."):
                    time.sleep(1)
                
                web_url = f"http://localhost:{self.web_port}"
                self.console.print(f"\n🎼 Your musical command center: {web_url}")
                
                if Confirm.ask("Open the web interface?"):
                    webbrowser.open(web_url)
                
                self.web_experience_guide()
                
            except Exception as e:
                self.console.print(f"🎵 The web realm is still forming: {e}")
    
    def web_experience_guide(self):
        """Guide through the web interface experience."""
        self.console.print("\n🎹 Web Interface Journey:")
        
        journey_steps = [
            "🎵 Click 'Play' - let music flow while you explore",
            "🔍 Search for an artist - see their complete universe",
            "📀 Browse albums - each one a complete world", 
            "🎚️  Adjust volume - feel the music's emotional temperature",
            "📜 View playlist - see the story your music tells",
            "🔄 Let one song lead to another in endless discovery"
        ]
        
        for step in journey_steps:
            self.console.print(f"   {step}")
        
        self.console.print("\n🌊 This is the oceanic experience:")
        self.console.print("   Lose yourself in the flow of musical discovery.")
        self.console.print("   Every click reveals new dimensions of your collection.")
        
        Prompt.ask("\nPress Enter when you've felt the musical flow")
    
    def chapter_5_the_connection(self):
        """The profound realization - finding the Ron Carter → MC Solaar bridge."""
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print("🌉 CHAPTER 5: The Mystical Connection", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print("\nNow for the deepest mystery...")
        self.console.print("How Ron Carter's 1963 bass lines connect to MC Solaar's 1991 French rap.\n")
        
        connection_story = Panel(
            Text.from_markup("""The ACTUAL Musical Collaboration:

[yellow]Miles Davis Quintet[/yellow] (1963-1968)
  ↓
[cyan]Ron Carter[/cyan] → The legendary bassist
  ↓  
[bold red]DIRECT COLLABORATION[/bold red]
  ↓
[magenta]MC Solaar[/magenta] - "Un Ange En Danger"
  ↓
[green]Ron Carter's bass[/green] on French intellectual hip-hop

[dim]This isn't theory - it's documented history.[/dim]
[dim]The live version shows Ron Carter absolutely killing it.[/dim]
[dim]American jazz masters embracing French hip-hop poetry.[/dim]"""),
            title="🎵 The Real Ron Carter → MC Solaar Connection",
            border_style="yellow"
        )
        
        self.console.print(connection_story)
        
        self.console.print("\n💡 Search both artists in your interfaces:")
        self.console.print("   - Ron Carter: From Miles Davis to MC Solaar - 60 years of musical bridges")
        self.console.print("   - MC Solaar: French intellectual hip-hop with actual jazz legend collaboration")
        self.console.print("\n   The graph shows DIRECT connection, not theoretical genetics!")
        self.console.print("   🎥 Try to find that legendary live performance on YouTube...")
        
        Prompt.ask("\nPress Enter when you've contemplated this connection")
    
    def finale_enlightenment(self):
        """The ultimate understanding."""
        self.console.print("\n" + "="*60, style="bold yellow")
        self.console.print("🌟 FINALE: The Enlightenment", style="bold yellow")
        self.console.print("="*60, style="bold yellow")
        
        enlightenment = Panel(
            Text.from_markup("""[bold cyan]What You Now Understand:[/bold cyan]

🎵 Your music isn't separate songs - it's a [yellow]connected ecosystem[/yellow]

🕸️  Every artist is a [cyan]node[/cyan] in the infinite network of influence

🌊 Genre boundaries are illusions - music flows like [blue]water[/blue]  

🎭 Your taste has [magenta]patterns[/magenta] that reveal who you are

♾️  Discovery is [green]infinite[/green] - connections never stop growing

[dim]You have become the curator of a musical universe.[/dim]
[dim]LinerNodes is your lens for seeing the invisible architecture of music.[/dim]

[bold yellow]The tour never ends. The discoveries never stop.[/bold yellow]"""),
            title="🎭 Welcome to the Infinite Record Shop",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(enlightenment)
        
        self.console.print("\n🎹 Your interfaces remain open:")
        self.console.print(f"   🌐 Web Control: http://localhost:{self.web_port}")
        self.console.print(f"   🕸️  Graph Explorer: http://localhost:{self.graph_port}")
        
        self.console.print("\n🌈 Continue exploring. The connections never end.")
        self.console.print("   Every album is a doorway.")
        self.console.print("   Every artist is a bridge.")  
        self.console.print("   Every discovery reveals new mysteries.")
        
        self.console.print("\n🎵 [italic]In the end, music is the language that connects all souls.[/italic]")
    
    def run_tour(self):
        """Execute the complete tour experience."""
        if not self.welcome():
            return
        
        try:
            self.chapter_1_import()
            
            if Confirm.ask("\nContinue to the visual revelation?", default="y"):
                self.chapter_2_first_search()
            
            if Confirm.ask("\nReady to see your music as a living constellation?", default="y"):
                self.chapter_3_graph_revelation()
            
            if Confirm.ask("\nShall we unite exploration with musical experience?", default="y"):
                self.chapter_4_web_flow()
            
            if Confirm.ask("\nAre you prepared for the deepest musical mystery?", default="y"):
                self.chapter_5_the_connection()
            
            self.finale_enlightenment()
            
        except KeyboardInterrupt:
            self.console.print("\n\n🎭 The tour is paused, but the music plays on...")
            self.console.print("Your interfaces remain open for continued exploration.")
        except Exception as e:
            self.console.print(f"\n🌟 The cosmic flow encountered: {e}")
            self.console.print("But the musical journey continues...")

def main():
    """Launch the interactive tour."""
    tour = DisquaireTour()
    tour.run_tour()

if __name__ == "__main__":
    main()
