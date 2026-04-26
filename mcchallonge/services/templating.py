import os
from datetime import datetime
from flask import render_template, current_app
from jinja2 import Environment, FileSystemLoader, BaseLoader

def render_tournament_dashboard(
    tournament,
    participants,
    matches,
    custom_content=None,
    logo_url=None,
    show_only=None,
    path_prefix="./",
):
    """
    Renders the tournament dashboard template with provided data.
    Works both within Flask app context and in standalone CLI mode.
    
    Args:
        tournament: Tournament object with tournament data
        participants: List of Participant objects
        matches: List of Match objects
        custom_content: Optional HTML content to add to the dashboard
        logo_url: Optional URL for tournament logo image
        show_only: Optional section-specific render mode
        path_prefix: Relative prefix used for static assets and internal links
        
    Returns:
        String with rendered HTML content
    """
    # Create a helper function to get participant by ID
    def get_participant_by_id(participant_id):
        if participant_id is None:
            return None
        return next((p for p in participants if p.id == participant_id), None)
    
    # Sort participants by wins (descending)
    sorted_participants = sorted(
        participants, 
        key=lambda p: (p.wins, -p.losses) if p.wins is not None else (0, 0), 
        reverse=True
    )
    
    # Format dates for better display
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Prepare template data
    template_data = {
        'title': f"Tournament: {tournament.name}",
        'tournament': tournament,
        'participants': sorted_participants,
        'matches': matches,
        'custom_content': custom_content,
        'logo_url': logo_url,
        'current_date': current_date,
        'get_participant_by_id': get_participant_by_id,
        'show_only': show_only,
        'path_prefix': path_prefix,
    }
    
    try:
        # Try to use Flask's render_template if we're in a Flask app context
        return render_template(
            'tournament_dashboard.jinja.html',
            **template_data
        )
    except RuntimeError:
        # Standalone mode - use Jinja2 directly
        # Determine the template directory path
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(package_dir, 'web', 'templates')
        
        # Define a function to mock Flask's url_for when used outside Flask
        def static_url_for(endpoint, **values):
            if endpoint == 'static':
                filename = values.get('filename', '')
                # For standalone mode, reference static files with proper relative path
                return f"./static/{filename}"
            return "#"  # Fallback for other endpoints
        
        # Create Jinja environment
        env = Environment(loader=FileSystemLoader(template_dir))
        # Add the url_for function to mimic Flask's functionality
        env.globals['url_for'] = static_url_for
        template = env.get_template('tournament_dashboard.jinja.html')
        
        # Render template
        return template.render(**template_data)