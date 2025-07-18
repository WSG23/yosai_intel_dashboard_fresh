@app.route('/debug/routes')
def debug_routes():
    output = []
    for rule in app.url_map.iter_rules():
        output.append(f"{rule.endpoint}: {rule.rule}")
    return '<pre>' + '\n'.join(sorted(output)) + '</pre>'
