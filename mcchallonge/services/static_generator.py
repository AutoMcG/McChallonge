import os
import shutil
from mcchallonge.services.templating import render_tournament_dashboard

# Example usage of the templating module in a standalone script
def generate_static_tournament_page(tournament, participants, matches, output_file, 
                                    custom_content=None, logo_url=None):
    """
    Generate a static HTML page for a tournament.
    
    Args:
        tournament: Tournament object
        participants: List of Participant objects
        matches: List of Match objects
        output_file: Path where HTML file should be saved
        custom_content: Optional HTML to include in the page
        logo_url: Optional URL for tournament logo
    """
    html_content = render_tournament_dashboard(
        tournament, participants, matches, custom_content, logo_url
    )
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only try to create if there's a directory part
        os.makedirs(output_dir, exist_ok=True)
    
    # Write HTML content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Copy static files
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_src_dir = os.path.join(package_dir, 'web', 'static')
    static_dest_dir = os.path.join(output_dir, 'static')
    
    # Create static directory if it doesn't exist
    os.makedirs(static_dest_dir, exist_ok=True)
    
    # Copy CSS, JS, and webfont files
    for subdir in ['css', 'js', 'webfonts']:
        src_subdir = os.path.join(static_src_dir, subdir)
        dest_subdir = os.path.join(static_dest_dir, subdir)
        
        if os.path.exists(src_subdir):
            # Create destination subdirectory
            os.makedirs(dest_subdir, exist_ok=True)
            
            # Copy all files from source to destination
            for file in os.listdir(src_subdir):
                src_file = os.path.join(src_subdir, file)
                dest_file = os.path.join(dest_subdir, file)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dest_file)
    
    print(f"Tournament page generated: {output_file}")
    print(f"Static files copied to: {static_dest_dir}")