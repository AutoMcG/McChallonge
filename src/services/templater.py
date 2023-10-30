from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader = FileSystemLoader(["src/web/templates/", "web/templates"]), #it feels dirty to do this just to support running tests from this or that dir...
    autoescape=select_autoescape()
    )

def run_table_template(table_template_name: str, title: str, relative_static_dir: str, schema, main_data_source) -> str:
    template = env.get_template(table_template_name)
    return template.render(title = title, relative_static_dir = relative_static_dir, schema = schema, main_data_source = main_data_source)